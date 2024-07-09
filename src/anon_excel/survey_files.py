from hashlib import blake2b
from pathlib import Path
import string

import pandas as pd

from anon_excel.constants import ANONYMOUS_ID
from anon_excel.calc_stats import category_to_rank


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


def read_and_clean_survey(excel_name: Path, column: str) -> pd.DataFrame:
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


def strip_leading_letter(name: str) -> str:
    if not name.startswith(tuple(string.digits)):
        return name[1:]

    return name


def strip_leading_letter_from_column(df: pd.DataFrame, namecol: str) -> pd.DataFrame:
    series = df[namecol]
    df[namecol] = series.apply(strip_leading_letter)

    return df


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


def load_and_prepare_survey_data(survey_file: str, namecol: str,
                                 strip: bool) -> pd.DataFrame:
    '''Read survey file, remove invalid data, remove leading letter if any from
       personal ID, transcode this personal ID's (in the `namecol` field) into
       anonymized values, and translate the answer code into numerical
       rankings, according to the `scoring.xlsx` data
    '''
    df = read_and_clean_survey(Path(survey_file), namecol)
    if strip:
        df = strip_leading_letter_from_column(df, namecol)

    df[namecol]
    df = transform_to_anonymous(df, on_column=namecol, to_column=ANONYMOUS_ID)
    df_ranked = category_to_rank(df)

    return df_ranked
