import argparse
from glob import glob
import logging
from hashlib import blake2b
import os
from pathlib import Path
import sys
import pandas as pd
from anon_excel.calc_stats import category_to_rank, paired_ttest

ANALYSIS_OUTPUT_BASE = 'analysis'
ANONYMOUS_ID = 'student_anon'
# name of ID column in the surveys:
DEFAULT_STUDENT_COLUMN = 'Your student number'


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
        description='''This app will calculate paired T-test statistics
        on a set of surveys. Personal information is anonymized.
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
        '-o', '--overwrite',
        action='store_true',
        required=False,
        help='Overwrite existing excel outputs')

    return parser


def read_and_clean(excel_name: Path, column: str) -> pd.DataFrame:
    df = pd.read_excel(excel_name)
    df = df.dropna(axis='index', subset=[column])
    df = df.astype({column: 'string'})

    return df


def find_survey_files(folder: Path) -> list[tuple[Path, Path]]:
    '''Find one or more sets of pre- and post survey excel files.
       Assume the pre-survey excel files start with 'Pre' and the
       post-survey excel files start with 'Post' with the remaining stems are equal.
       return only those sets containing both a pre and a post survey file.
    '''
    stem_pre = 'Pre'
    stem_post = 'Post'
    files = glob(str(folder) + f'/{stem_pre}*.xlsx')
    if len(files) == 0:
        print('No survey excel files found')
        return []

    files = [Path(f) for f in files]
    surveys = []
    for pre in files:
        post_file = pre.with_stem(stem_post + pre.stem[len(stem_pre):])
        if post_file.exists():
            surveys.append((pre, post_file))

    return surveys


def load_and_prepare_survey_data(survey_file: str, namecol: str) -> pd.DataFrame:
    df = read_and_clean(Path(survey_file), namecol)
    df = transform_to_anonymous(
        df, on_column=namecol, to_column=ANONYMOUS_ID)
    df_ranked = category_to_rank(df)

    return df_ranked


logging.basicConfig(
    filename='anon_excel.log',
    filemode='w',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
log.addHandler(ch)


def remove_previous_results(files: list[Path]) -> None:
    prev = [Path(p).name for p in files]
    log.error(f'Removing previous analysis results: \n{prev}')
    for f in files:
        os.remove(f)


def main():
    args = get_parser().parse_args()

    folder = Path(args.folder)
    if not folder.exists:
        log.error('Folder {args.folder} does not exist')
        sys.exit(1)

    id_column = DEFAULT_STUDENT_COLUMN
    if args.column:
        id_column = args.col[0]

    prev = glob(str(folder) + f'/{ANALYSIS_OUTPUT_BASE}*.xlsx')
    if args.overwrite:
        if prev:
            remove_previous_results(prev)
    else:
        prev = [Path(p).name for p in prev]
        log.error(f'Output analysis {prev} already exists.\n'
                  'Use --overwrite to force removal and recalculation')
        sys.exit()

    surveys = find_survey_files(folder)
    if not surveys:
        log.error('No survey files found, quitting')
        sys.exit()

    for pre_file, post_file in surveys:
        log.info('Initiating analysis')
        log.info(f'Pre-survey file: "{pre_file}"')
        df_pre = load_and_prepare_survey_data(pre_file, id_column)
        log.info(f'Post-survey file: "{post_file}"')
        df_post = load_and_prepare_survey_data(post_file, id_column)

        # task: calculate paired t-test for each question common in
        #       pre survey and post survay with student as independent var
        log.info('Calculating paired Ttest from Pre- and Post survey')
        df_pairs, df_combined, df_legend, df_bf, df_af, df_stud_pairs = paired_ttest(
            df_pre, df_post, id_column=ANONYMOUS_ID)

        excel_output = folder / Path(ANALYSIS_OUTPUT_BASE + '_' + pre_file.name[4:])
        log.info(f'Writing analysis result to "{excel_output}"')
        with pd.ExcelWriter(excel_output) as writer:
            df_pairs.to_excel(writer, sheet_name='Paired Ttest', index=False)
            df_stud_pairs.to_excel(
                writer, sheet_name='Students Ttest', index=False)
            df_combined.to_excel(writer, sheet_name='Rankings', index=False)
            df_bf.to_excel(writer, sheet_name='Pre-questions', index=False)
            df_af.to_excel(writer, sheet_name='Post-questions', index=False)
            df_legend.to_excel(
                writer, sheet_name='Question legend', index=False)


if __name__ == '__main__':
    main()
