import pandas as pd
from pathlib import Path

SCORING_DATA_FILE = Path('data/Scoring.xlsx')
EXPECTED_COLUMNS = ['question', 'Strongly agree (SA)', 'Agree (A)', 'Neutral (N)',
                    'Disagree (D)', 'Strongly Disagree (SD)']


def read_ranking_data(fn: Path, worksheet: str = 'Scoring') -> pd.DataFrame:
    df = pd.read_excel(fn, sheet_name=worksheet)
    df = df[EXPECTED_COLUMNS]
    df = df.set_index('question')
    dct = df.to_dict('records')

    ranking = {q: rec for q, rec in zip(df.index, dct)}

    return ranking


rank_lookup = read_ranking_data(SCORING_DATA_FILE)
