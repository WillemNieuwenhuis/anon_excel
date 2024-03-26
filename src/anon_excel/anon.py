import argparse
from glob import glob
# import logging
from pathlib import Path
import sys
import pandas as pd
from anon_excel.calc_stats import category_to_rank


def transform_to_anonymous(df: pd.DataFrame, column: str) -> pd.DataFrame:
    '''find student number column and anonymize
       return unchanged if column is not in dataframe
    '''
    if not column in df.columns:
        return df

    series = df[column]
    df['student_anon'] = series.apply(lambda s: abs(hash(s)))
    cur_cols = list(df.columns)
    ix = cur_cols.index(column)
    new_cols = cur_cols[0:ix] + cur_cols[-1:] + cur_cols[ix:-1]
    df = df[new_cols]
    df = df.drop(columns=[column])
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

    files = glob(str(folder) + '/P*.xlsx')
    if len(files) == 0:
        print('No excel files found')

    for dex in files:
        name = Path(dex)
        outname = name.with_stem(name.stem + '_anon')
        if outname.exists():
            continue

        df = read_and_clean(name, col[0])
        df = transform_to_anonymous(df, col[0])
        df = category_to_rank(df)
        df.to_excel(outname, index=False)


if __name__ == '__main__':
    main()
