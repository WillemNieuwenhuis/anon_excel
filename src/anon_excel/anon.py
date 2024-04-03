import argparse
from glob import glob
# import logging
from hashlib import blake2b
import os
from pathlib import Path
import sys
import pandas as pd
from anon_excel.calc_stats import category_to_rank, calc_question_mean, paired_ttest


def transform_to_anonymous(df: pd.DataFrame, on_column: str, to_column: str) -> pd.DataFrame:
    '''find student number column and anonymize, using
       the blake2b stable hash function
       return unchanged if column is not in dataframe
    '''
    if not on_column in df.columns:
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
        description='''This app will anonymize personal information
        in user specified columns in an excel table. The personal
        information is hashed and can be repeated on other excel files
        producing the same hashed value for the same input.
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
    parser.add_argument(
        '-r', '--remove',
        action='store_true',
        required=False,
        help='Do not copy personal data to output')

    return parser


def read_and_clean(excel_name: Path, column: str) -> pd.DataFrame:
    df = pd.read_excel(excel_name)
    df = df.dropna(axis='index', subset=[column])
    df = df.astype({column: 'string'})

    return df


def main():
    args = get_parser().parse_args()

    folder = Path(args.folder)
    if not folder.exists:
        print('Folder {args.folder} does not exist')
        sys.exit(1)

    col = ['Your student number']
    if args.column:
        col = args.col

    # logging.basicConfig(
    #     filename=folder / 'anon_excel.log',
    #     filemode='w',
    #     format='%(asctime)s %(levelname)-8s %(message)s',
    #     level=logging.INFO,
    #     datefmt='%Y-%m-%d %H:%M:%S')
    # log = logging.getLogger(__name__)

    if args.overwrite:
        prev_result = glob(str(folder) + '/P*anon.xlsx')
        for fn in prev_result:
            os.remove(fn)

    files = glob(str(folder) + '/P*.xlsx')
    if len(files) == 0:
        print('No excel files found')

    dfs = []
    for dex in files:
        name = Path(dex)
        outname = name.with_stem(name.stem + '_anon')
        if outname.exists():
            continue

        df = read_and_clean(name, col[0])
        df = transform_to_anonymous(
            df, on_column=col[0], to_column='student_anon')
        df = category_to_rank(df)
        dfs.append(df)

        # task 1: add ranking averages, both to questions (columns)
        #         as well as studentID (rows)
        df_mean = calc_question_mean(df)
        df_mean.to_excel(outname, index=False)

    # task 2: calculate paired t-test for each question common in
    #         before and after with student as independent var
    paired_ttest(dfs[0], dfs[1], 'student_anon')


if __name__ == '__main__':
    main()
