import pandas as pd
from scipy import stats

POSITIV_RANK = {'Strongly agree (SA)': 4, 'Agree (A)': 3, 'Neutral (N)': 2,
                'Disagree (D)': 1, 'Strongly Disagree (SD)': 0, '': -1}
NEGATIV_RANK = {'Strongly agree (SA)': 0, 'Agree (A)': 1, 'Neutral (N)': 2,
                'Disagree (D)': 3, 'Strongly Disagree (SD)': 4, '': -1}
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


def calc_question_mean(df: pd.DataFrame) -> pd.DataFrame:
    qset = set(RANK_LOOKUP.keys())
    col_set = set(df.columns)
    select = list(qset.intersection(col_set))
    for col in select:
        df = df.astype({col: 'float64'})

    df['mean'] = df[select].mean(axis=1)            # add row averages
    df.loc['averages', select] = df[select].mean()  # add col averages
    return df


def category_to_rank(df: pd.DataFrame) -> pd.DataFrame:
    for question, ranks in RANK_LOOKUP.items():
        if question in list(df.columns):
            df[question] = df[question].replace(r'\s+', ' ', regex=True)
            df[question] = df[question].map(ranks)

    return df


def paired_ttest_on_question(before: pd.Series, after: pd.Series) -> tuple[float, float]:
    '''Calculate paired t-test
       return stat-value and p-value
    '''
    res = stats.ttest_rel(before, after)
    return res['statistic'], res['pvalue']


def paired_ttest(df_before: pd.DataFrame, df_after: pd.DataFrame, id_column: str):
    # first make sure the dataframe are ordered by the same column (student_anon)
    df_before.sort_values(by=[id_column])
    df_after.sort_values(by=[id_column])

    # select common questions
    qset = set(RANK_LOOKUP.keys())
    col_set_before = set(df_before.columns)
    col_set_after = set(df_after.columns)
    common_cols = col_set_before.intersection(col_set_after)
    questions = list(qset.intersection(common_cols))
    # make sure the questions are in the same order for before and after
    df_before = df_before[[id_column, *questions]]
    df_after = df_after[[id_column, *questions]]

    # select common students
    stud_before = set(df_before[id_column].values)
    stud_after = set(df_after[id_column].values)
    stud_common = stud_before.intersection(stud_after)
    df_bf = df_before[df_before[id_column].isin(stud_common)]
    df_af = df_after[df_after[id_column].isin(stud_common)]

    # combine into single dataset with only
    # overlapping students and questions in Pre and Post survey results
    quests_before = [f'before_{n:02}' for n in range(1, len(questions)+1)]
    quests_after = [f'after_{n:02}' for n in range(1, len(questions)+1)]
    df_bf.columns = [id_column, *quests_before]
    df_af.columns = [id_column, *quests_after]
    df_combined = df_bf.merge(df_af, on=id_column)
    combined_cols = [id_column, *[q for tup in zip(
        quests_before, quests_after) for q in tup]]
    df_combined = df_combined[combined_cols]

    # Apply Ttest for each question
    pairs = []
    for bef, aft, question in zip(quests_before, quests_after, questions):
        df_q = df_combined[[id_column, bef, aft]]
        res = stats.ttest_rel(df_q[bef].values, df_q[aft].values)
        pairs.append(
            {'question': question, 'statistic': res.statistic, 'pvalue': res.pvalue})

    df_pairs = pd.DataFrame(pairs)
    question_legend = [questions, quests_before, quests_after]
    df_legend = pd.DataFrame(question_legend).T
    df_legend.columns = ['Question', 'Before_question_ID', 'After_question_ID']

    with pd.ExcelWriter('data/analysis.xlsx') as writer:
        df_pairs.to_excel(writer, sheet_name='Paired Ttest', index=False)
        df_combined.to_excel(writer, sheet_name='Rankings', index=False)
        df_legend.to_excel(writer, sheet_name='Question legend', index=False)
