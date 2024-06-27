import argparse
import logging
from hashlib import blake2b
import os
from pathlib import Path
import pandas as pd
import re
import string
import sys
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from anon_excel.calc_stats import (
    category_to_rank, determine_distinct_students, paired_ttest)
from anon_excel.ranking_data import load_from_folder

log = logging.getLogger(__name__)

ANALYSIS_OUTPUT_BASE = 'analysis'
CLEANED_OUTPUT_BASE = 'cleaned'
DATA_OUTPUT_BASENAME = 'data_survey'
ANONYMOUS_ID = 'student_anon'
CLEAN_SHEET_PRE_SURVEY = 'Clean pre-survey'
CLEAN_SHEET_POST_SURVEY = 'Clean post-survey'

# name of ID column in the surveys:
# Note that this column will NOT end up in the cleaned and final outputs
DEFAULT_STUDENT_COLUMN = 'Your student number'
# columns to drop in cleaned output
DROP_COLUMNS = ['ID', 'Start time', 'Completion time',
                'Email', 'Name', 'Last modified time']


def transform_to_anonymous(df: pd.DataFrame,
                           on_column: str, to_column: str) -> pd.DataFrame:
    '''find student number column and anonymize, using
       the blake2b stable hash function. This will add a new column.
       return unchanged if column is not in dataframe
    '''
    if on_column not in df.columns:
        return df

    series = df[on_column]
    df[to_column] = series.apply(lambda s: blake2b(
        bytes(s.strip(), 'utf-8'), digest_size=8).hexdigest()).astype('string')
    cur_cols = list(df.columns)
    ix = cur_cols.index(on_column)
    new_cols = cur_cols[0:ix] + cur_cols[-1:] + cur_cols[ix:-1]
    df = df[new_cols]

    return df


def get_parser() -> argparse.ArgumentParser:
    '''Setup a command line parser'''
    parser = argparse.ArgumentParser(
        description='''This app scans multiple sets of surveys. It offers an option
         to clean and store the survey data, and also an option to perform and store
         a T-test analysis. The T-test is only possible when both pre- and post-
         survey is available.
         Optionally personal information is removed.
        '''
    )
    parser.add_argument(
        'folder',
        help='Specify the folder with the excel report(s)')
    parser.add_argument(
        '-a', '--anonymize',
        action='count',
        required=False,
        default=0,
        help='Anonymize personal data (default = No)')
    parser.add_argument(
        '-c', '--color',
        action='store_true',
        required=False,
        default=False,
        help='Add colors in excel file with clean ranked data (default = No)')
    parser.add_argument(
        '-o', '--overwrite',
        action='store_true',
        required=False,
        default=False,
        help='Overwrite existing excel outputs (default = No)')
    parser.add_argument(
        '-s', '--strip',
        action='store_true',
        required=False,
        default=False,
        help='Strip leading s-char from s-number (default = No)')
    parser.add_argument(
        '-t', '--ttest',
        action='store_true',
        required=False,
        default=False,
        help='Perform T-test calculation (default = No)')
    parser.add_argument(
        '-x', '--clean',
        action='store_true',
        required=False,
        default=False,
        help='Save cleaned data (default = No)')

    return parser


def read_and_clean(excel_name: Path, column: str) -> pd.DataFrame:
    '''Read the excel data, remove all records that have invalid
       data in the `column` field (usually the user ID), and change
       the type from Object to string'''
    df = pd.read_excel(excel_name)
    df = df.dropna(axis='index', subset=[column])
    df = df.astype({column: 'string'})
    names = df[column]
    df[column] = names.apply(lambda x: x.strip())
    # throw away duplicate student records (keep first)
    df = df.drop_duplicates(subset=[column])

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


def strip_leading_letter(name: str) -> str:
    if not name.startswith(tuple(string.digits)):
        return name[1:]

    return name


def strip_leading_letter_from_column(df: pd.DataFrame, namecol: str) -> pd.DataFrame:
    series = df[namecol]
    df[namecol] = series.apply(strip_leading_letter)

    return df


def load_and_prepare_survey_data(survey_file: str, namecol: str,
                                 strip: bool) -> pd.DataFrame:
    '''Read survey file, remove invalid data, remove leading letter if any from
       personal ID, transcode this personal ID's (in the `namecol` field) into
       anonymized values, and translate the answer code into numerical
       rankings, according to the `scoring.xlsx` data
    '''
    df = read_and_clean(Path(survey_file), namecol)
    if strip:
        df = strip_leading_letter_from_column(df, namecol)

    df[namecol]
    df = transform_to_anonymous(df, on_column=namecol, to_column=ANONYMOUS_ID)
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

    if not check_remove_all_outputs(folder,
                                    clean=args.clean,
                                    ttest=args.ttest,
                                    overwrite=args.overwrite):
        sys.exit()
    return folder, id_column


def determine_survey_data_name(survey_file: Path, sequence_nr: int) -> str:
    '''Extract a sequence ID from filename. The pattern looked for is
       `(n-m)` where n, m are integer values, fe. `(1-89)`. If this cannot
       be found the `sequence_nr` will be used instead to generate a filename.
       The name generated will then be either:
       1. survey_data_(n-m)
       2. survey_data_<sequence_nr>
    '''
    patt = f'{sequence_nr:02}'

    regex = r'.*(\(\d+-\d+\))'
    m = re.match(regex, survey_file.name)
    if m and (len(m.groups()) == 1):
        patt = m.group(1)

    return f'{DATA_OUTPUT_BASENAME}_{patt}'


def clean_and_save_survey_data(folder: Path,
                               pre_file: Path, post_file: Path,
                               df_pre: pd.DataFrame, df_post: pd.DataFrame,
                               seq_nr: int,
                               anonymize: int) -> Path:
    ''' Save survey data to excel. Only keep relevant columns.
        Depending on the command line parameter `anonymize` the following happens:
        `anonymize=0` : student ID column is retained, no anonymized data in output
        `anonymize=1` : student ID column is retained, also anonymized data in output
        `anonymize=2` : student ID column is removed, only anonymized data in output
    '''
    out_folder = folder / CLEANED_OUTPUT_BASE
    check_create_out_folder(out_folder)
    clean_output = out_folder / \
        f'''{CLEANED_OUTPUT_BASE}_{determine_survey_data_name(
            pre_file, sequence_nr=seq_nr)}.xlsx'''

    # filter out the sensitive columns and prepare for output
    cols_to_drop = DROP_COLUMNS
    if anonymize == 0:  # 0 == drop anonymized data
        log.info(f'Do not save anonymized data, {anonymize=}')
        cols_to_drop = [*DROP_COLUMNS, ANONYMOUS_ID]
    if anonymize == 2:  # 2 == drop sensitive data
        log.info(f'Removing sensitive data, {anonymize=}')
        cols_to_drop = [*DROP_COLUMNS, DEFAULT_STUDENT_COLUMN]
    remain_columns = [col for col in df_pre.columns if col not in cols_to_drop]
    clean_data = [(df_pre[remain_columns], CLEAN_SHEET_PRE_SURVEY)]
    if post_file.name:
        remain_columns = [
            col for col in df_post.columns if col not in cols_to_drop]
        clean_data.append((df_post[remain_columns], CLEAN_SHEET_POST_SURVEY))

    log.info(f'Writing cleaned data to "{clean_output}"')
    write_to_excel(clean_output, sheets=clean_data)

    return clean_output


def ttest_and_save(folder: Path, pre_file: Path,
                   df_pre: pd.DataFrame, df_post: pd.DataFrame,
                   seq_nr: int):
    log.info('Calculating paired T-test from Pre- and Post survey')
    df_pairs, _, df_legend, df_bf, df_af, df_stud_pairs = paired_ttest(
        df_pre, df_post, id_column=ANONYMOUS_ID)

    out_folder = folder / ANALYSIS_OUTPUT_BASE
    check_create_out_folder(out_folder)
    excel_output = out_folder / \
        f'{ANALYSIS_OUTPUT_BASE}_{determine_survey_data_name(pre_file, seq_nr)}.xlsx'
    ttest_output = [(df_pairs, 'Paired T-test'),
                    (df_stud_pairs, 'Students T-test'),
                    (df_bf, 'Pre-questions'),
                    (df_af, 'Post-questions'),
                    (df_legend, 'Question legend')]

    log.info(f'Writing analysis result to "{excel_output}"')
    write_to_excel(excel_output, sheets=ttest_output)

# Function to find the column index of 'id_column'


def find_id_column_index(worksheet, column_name: str):
    for cell in worksheet[1]:  # Iterate over the first row (header)
        if cell.value == column_name:
            return cell.col_idx - 1  # Return zero-based index


def colorize_excel(excel_file: Path,
                   df_pre: pd.DataFrame, df_post: pd.DataFrame,
                   id_column: str):
    book = load_workbook(excel_file)

    stud_common, studs_before_only, stud_after_only = determine_distinct_students(
        df_pre, df_post, id_column)

    # Define fills
    fill_green = PatternFill(start_color="CCFFCC",
                             end_color="CCFFCC", fill_type="solid")
    fill_blue = PatternFill(start_color="CCCCFF", end_color="CCCCFF", fill_type="solid")
    fill_red = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")

    # Get the worksheets
    ws_pre = book[CLEAN_SHEET_PRE_SURVEY]
    ws_post = book[CLEAN_SHEET_POST_SURVEY]

    # get index of the id_column
    id_col_idx_pre = find_id_column_index(ws_pre, id_column)
    id_col_idx_post = find_id_column_index(ws_post, id_column)

    # Apply conditional formatting for survey_pre
    for row in ws_pre.iter_rows(min_row=2, max_row=ws_pre.max_row, min_col=1, max_col=ws_pre.max_column):
        cell_value = row[id_col_idx_pre].value
        if cell_value in stud_common:
            for cell in row:
                cell.fill = fill_green
        elif cell_value in studs_before_only:
            for cell in row:
                cell.fill = fill_blue

    # Apply conditional formatting for survey_post
    for row in ws_post.iter_rows(min_row=2, max_row=ws_post.max_row, min_col=1, max_col=ws_post.max_column):
        cell_value = row[id_col_idx_post].value
        if cell_value in stud_common:
            for cell in row:
                cell.fill = fill_green
        elif cell_value in stud_after_only:
            for cell in row:
                cell.fill = fill_red

    # Save the updated Excel file
    book.save(excel_file)


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
    for seq_nr, (pre_file, post_file) in enumerate(surveys, start=1):
        log.info('Initiating analysis')
        log.info(f'Pre-survey file: "{pre_file}"')
        df_pre = load_and_prepare_survey_data(pre_file, id_column, args.strip)
        if post_file.name:
            log.info(f'Post-survey file: "{post_file}"')
            df_post = load_and_prepare_survey_data(post_file, id_column, args.strip)
        else:
            log.info('No accompanying post file')
            if args.ttest:
                log.info('Skipping T-test')

        if args.clean:
            clean_output = clean_and_save_survey_data(
                folder, pre_file, post_file, df_pre, df_post,
                seq_nr,
                args.anonymize)

            # optionally apply styles/colors
            if args.color:
                sel_col = ANONYMOUS_ID
                if args.anonymize == 0:
                    sel_col = id_column
                colorize_excel(clean_output, df_pre, df_post, sel_col)

        # T-test is only possible whith both pre- and post_survey files
        if args.ttest and post_file.name:
            ttest_and_save(folder, pre_file, df_pre, df_post, seq_nr)


if __name__ == '__main__':
    main()
