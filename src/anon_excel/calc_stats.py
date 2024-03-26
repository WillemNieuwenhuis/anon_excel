import pandas as pd

POSITIV_RANK = {'Strongly agree (SA)': 4, 'Agree (A)': 3, 'Neutral (N)': 2,
                'Disagree (D)': 1, 'Strongly Disagree (D)': 0, '': -1}
NEGATIV_RANK = {'Strongly agree (SA)': 0, 'Agree (A)': 1, 'Neutral (N)': 2,
                'Disagree (D)': 3, 'Strongly Disagree (D)': 4, '': -1}
RANK_LOOKUP = \
    {'I feel that students in this course care about each other': POSITIV_RANK,
     'I feel that I am encouraged to ask questions': POSITIV_RANK,
     'I feel connected to others in this course': POSITIV_RANK,
     'I feel that it is hard to get help when I have a question': NEGATIV_RANK,
     'I do not feel a spirit of community': NEGATIV_RANK,
     'I feel that I receive timely feedback': POSITIV_RANK,
     'I feel that this course is like a family': POSITIV_RANK,
     'I feel uneasy exposing gaps in my understanding': NEGATIV_RANK,
     'I feel isolated in this course': NEGATIV_RANK,
     'I feel reluctant to speak openly': NEGATIV_RANK,
     'I trust others in this course': POSITIV_RANK,
     'I feel that this course results in only modest learning': NEGATIV_RANK,
     'I feel that I can rely on others in this course': POSITIV_RANK,
     'I feel that other students do not help me learn': NEGATIV_RANK,
     'I feel that members of this course depend on me': POSITIV_RANK,
     'I feel that I am given ample opportunities to learn': POSITIV_RANK,
     'I feel uncertain about others in this course': NEGATIV_RANK,
     'I feel that my educational needs are not being met': NEGATIV_RANK,
     'I feel confident that others will support me': POSITIV_RANK,
     'I feel that this course does not promote a desire to learn': NEGATIV_RANK,
     }


def calc_row_stat():
    pass


def category_to_rank(df: pd.DataFrame) -> pd.DataFrame:
    for question, ranks in RANK_LOOKUP.items():
        df[question] = df[question].map(ranks)

    return df
