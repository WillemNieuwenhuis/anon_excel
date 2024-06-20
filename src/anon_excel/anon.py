import argparse
import logging
from hashlib import blake2b
import os
from pathlib import Path
import sys
import pandas as pd
from anon_excel.calc_stats import category_to_rank, paired_ttest
from anon_excel.ranking_data import load_from_folder

log = logging.getLogger(__name__)

ANALYSIS_OUTPUT_BASE = 'analysis'
CLEANED_OUTPUT_BASE = 'cleaned'
ANONYMOUS_ID = 'student_anon'

# name of ID column in the surveys:
# Note that this column will NOT end up in the cleaned and final outputs
DEFAULT_STUDENT_COLUMN = 'Your student number'
# columns to drop in cleaned output
DROP_COLUMNS = ['ID', 'Start time', 'Completion time',
                'Email', 'Name', 'Last modified time']


def transform_to_anonymous(df: pd.DataFrame,
                           on_column: str, to_column: str) -> pd.DataFrame:
    '''find student number column and anonymize, using
       the blake2b stable hash function
       return unchanged if column is not in dataframe
    '''
    if on_column not in df.columns:
        return df

    series = df[on_column]
    df[to_column] = series.apply(lambda s: blake2b(
        bytes(s, 'utf-8'), digest_size=8).hexdigest()).astype('string')
    cur_cols = list(df.columns)
    ix = cur_cols.index(on_column)
    new_cols = cur_cols[0:ix] + cur_cols[-1:] + cur_cols[ix:-1]
    df = df[new_cols]
    df = df.drop(columns=[on_column])
    return df


def get_parser() -> argparse.ArgumentParser:
    '''Setup a command line parser'''
    parser = argparse.ArgumentParser(
        description='''This app scans multiple sets of surveys. It offers an option
         to clean and store the survey data, and also an option to perform and store
         a T-test analysis. The T-test is only possible when both pre- and post-
         survey is available.
         Any personal information is removed.
        '''
    )
    parser.add_argument(
        'folder',
        help='Specify the folder with the excel report(s)')
    parser.add_argument(
        '-c', '--column',
        nargs='+',
        required=False,
        help='Specify the columns (by name) to make anonymous')
    parser.add_argument(
        '-x', '--clean',
        action='store_true',
        required=False,
        default=False,
        help='Save cleaned data (default = No)')
    parser.add_argument(
        '-t', '--ttest',
        action='store_true',
        required=False,
        default=False,
        help='Perform T-test calculation (default = No)')
    parser.add_argument(
        '-o', '--overwrite',
        action='store_true',
        required=False,
        help='Overwrite existing excel outputs')

    return parser


def read_and_clean(excel_name: Path, column: str) -> pd.DataFrame:
    '''Read the excel data, remove all records that have invalid
       data in the `column` field (usually the user ID), and change
       the type from Object to string'''
    df = pd.read_excel(excel_name)
    df = df.dropna(axis='index', subset=[column])
    df = df.astype({column: 'string'})

    return df


def find_survey_files(folder: Path, allow_missing_post: bool = False) -> list[tuple[Path, Path]]:
    '''Find one or more sets of pre- and post survey excel files.
       Assume the pre-survey excel files start with 'Pre' and the
       post-survey excel files start with 'Post' with the remaining stems are equal.
       The allow_missing_post setting is used to allow existence of pre-survey file only,
       making it possible to pre-analyse / clean the data; the pre-survey file MUST
       be available.
       return tuples containing both a pre and a post survey file, where the post
       survey file can be an empty path when allow_missing_post == true.
    '''
    stem_pre = 'Pre'
    stem_post = 'Post'
    files = list(folder.glob(f'{stem_pre}*.xlsx'))
    if len(files) == 0:
        print('No survey excel files found')
        return []

    files = [Path(f) for f in files]
    surveys = []
    for pre in files:
        post_file = pre.with_stem(stem_post + pre.stem[len(stem_pre):])
        if post_file.exists():
            surveys.append((pre, post_file))
        elif allow_missing_post:
            surveys.append((pre, Path('')))

    return surveys


def load_and_prepare_survey_data(survey_file: str, namecol: str) -> pd.DataFrame:
    '''Read survey file, remove invalid data, transcode the personal ID's
       (in the `namecol` field) into anonymized values, and translate the
       answer code into numerical rankings, according to the `scoring.xlsx` data'''
    df = read_and_clean(Path(survey_file), namecol)
    df = transform_to_anonymous(
        df, on_column=namecol, to_column=ANONYMOUS_ID)
    df_ranked = category_to_rank(df)

    return df_ranked


def remove_previous_results(files: list[Path], do_overwrite: bool, which_output: str) -> bool:
    if not files:
        return True

    prev = [Path(p).name for p in files]
    if do_overwrite:
        log.info(f'Trying to remove previous {which_output} results: \n{prev}')
        for f in files:
            os.remove(f)
        return True

    log.error(f'Output {which_output} data already exists.\n'
              'Use --overwrite to force removal and recalculation')

    return False


def check_remove_all_outputs(folder: Path, clean: bool, ttest: bool, overwrite: bool) -> bool:
    for check, rem in zip([ANALYSIS_OUTPUT_BASE, CLEANED_OUTPUT_BASE], [ttest, clean or ttest]):
        if not rem:
            continue
        cur_fol = folder / check
        prev = list(cur_fol.glob(f'{check}*.xlsx'))
        if not remove_previous_results(prev, which_output=check, do_overwrite=overwrite):
            return False

    return True


def check_create_out_folder(folder: Path):
    '''Make sure folder exists'''
    if folder.exists() and folder.is_dir():
        return True

    folder.mkdir()


def write_to_excel(filename: Path, sheets: tuple[list[pd.DataFrame], str]) -> None:
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for df, sheetname in sheets:
            df.to_excel(writer, sheet_name=sheetname, index=False)


def validate_input(args) -> tuple[Path, str]:
    folder = Path(args.folder)
    if not folder.exists:
        log.error('Folder {args.folder} does not exist')
        sys.exit(1)

    id_column = DEFAULT_STUDENT_COLUMN
    if args.column:
        id_column = args.column[0]

    if not check_remove_all_outputs(folder,
                                    clean=args.clean,
                                    ttest=args.ttest,
                                    overwrite=args.overwrite):
        sys.exit()
    return folder, id_column


def clean_and_save_survey_data(folder: Path,
                               pre_file: Path, post_file: Path,
                               df_pre: pd.DataFrame, df_post: pd.DataFrame):
    out_folder = folder / CLEANED_OUTPUT_BASE
    check_create_out_folder(out_folder)
    clean_output = out_folder / f'{CLEANED_OUTPUT_BASE}_{pre_file.name}'

    # filter out the sensitive columns and prepare for output
    remain_columns = [col for col in df_pre.columns if col not in DROP_COLUMNS]
    clean_data = [(df_pre[remain_columns], 'Clean pre-survey')]
    if post_file.name:
        remain_columns = [
            col for col in df_post.columns if col not in DROP_COLUMNS]
        clean_data.append((df_post[remain_columns], 'Clean post-survey'))

    log.info(f'Writing cleaned data to "{clean_output}"')
    write_to_excel(clean_output, sheets=clean_data)


def ttest_and_save(folder: Path, pre_file: Path, df_pre: pd.DataFrame, df_post: pd.DataFrame):
    log.info('Calculating paired T-test from Pre- and Post survey')
    df_pairs, _, df_legend, df_bf, df_af, df_stud_pairs = paired_ttest(
        df_pre, df_post, id_column=ANONYMOUS_ID)

    out_folder = folder / ANALYSIS_OUTPUT_BASE
    check_create_out_folder(out_folder)
    excel_output = out_folder / f'{ANALYSIS_OUTPUT_BASE}_{pre_file.name[4:]}'
    ttest_output = [(df_pairs, 'Paired T-test'),
                    (df_stud_pairs, 'Students T-test'),
                    (df_bf, 'Pre-questions'),
                    (df_af, 'Post-questions'),
                    (df_legend, 'Question legend')]

    log.info(f'Writing analysis result to "{excel_output}"')
    write_to_excel(excel_output, sheets=ttest_output)


def main():
    args = get_parser().parse_args()

    folder, id_column = validate_input(args)

    surveys = find_survey_files(folder, allow_missing_post=args.clean)
    if not surveys:
        log.error('No survey files found, quitting')
        sys.exit()

    if not args.clean and not args.ttest:
        log.info('No cleaning or t-test requested, nothing to do, quitting')
        sys.exit()

    # init ranking lookup
    load_from_folder(args.folder)

    # start processing
    for pre_file, post_file in surveys:
        log.info('Initiating analysis')
        log.info(f'Pre-survey file: "{pre_file}"')
        df_pre = load_and_prepare_survey_data(pre_file, id_column)
        if post_file.name:
            log.info(f'Post-survey file: "{post_file}"')
            df_post = load_and_prepare_survey_data(post_file, id_column)
        else:
            log.info('No accompanying post file')
            if args.ttest:
                log.info('Skipping T-test')

        if args.clean:
            clean_and_save_survey_data(folder, pre_file, post_file, df_pre, df_post)

        # T-test is only possible whith both pre- and post_survey files
        if args.ttest and post_file.name:
            ttest_and_save(folder, pre_file, df_pre, df_post)


if __name__ == '__main__':
    main()
