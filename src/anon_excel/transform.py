import pandas as pd


def transform_anonymous(src: pd.DataFrame) -> pd.DataFrame:
    return None


def open_source_excel(fn: str) -> pd.DataFrame:
    return pd.read_excel(fn)
