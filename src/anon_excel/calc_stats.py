import logging
import pandas as pd
from scipy import stats

POSITIV_RANK = {'Strongly agree (SA)': 4, 'Agree (A)': 3, 'Neutral (N)': 2,
                'Disagree (D)': 1, 'Strongly Disagree (SD)': 0, '': 0}
NEGATIV_RANK = {'Strongly agree (SA)': 0, 'Agree (A)': 1, 'Neutral (N)': 2,
                'Disagree (D)': 3, 'Strongly Disagree (SD)': 4, '': 0}
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

log = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
log.addHandler(ch)


def category_to_rank(df: pd.DataFrame) -> pd.DataFrame:
    ''' Transform answer categories to numerical rankings
    '''
    log.info('Transform categories to numerical values')
    df_rank = df.copy()
    for question, ranks in RANK_LOOKUP.items():
        if question in list(df_rank.columns):
            # strip whitespace
            df_rank[question] = df_rank[question].replace(r'\s+', ' ', regex=True)
            df_rank[question] = df_rank[question].map(ranks)

    return df_rank


def determine_common_questions(df_bf: pd.DataFrame, df_af: pd.DataFrame) -> list:
    '''
        Find questions available in both dataframes
    '''
    qset = set(RANK_LOOKUP.keys())
    col_set_before = set(df_bf.columns)
    col_set_after = set(df_af.columns)
    common_cols = col_set_before.intersection(col_set_after)
    questions = list(qset.intersection(common_cols))
    return questions


def determine_common_students(df_before: pd.DataFrame, df_after: pd.DataFrame,
                              id_column: str) -> list:
    '''
        Find students common to both dateframes
    '''
    stud_before = set(df_before[id_column].values)
    stud_after = set(df_after[id_column].values)
    stud_common = stud_before.intersection(stud_after)

    return stud_common


def paired_ttest(df_before: pd.DataFrame, df_after: pd.DataFrame, id_column: str) -> \
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
              pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # first make sure the dataframe are ordered by the same column (student_anon)
    df_before = df_before.sort_values(by=[id_column])
    df_after = df_after.sort_values(by=[id_column])

    questions = determine_common_questions(df_before, df_after)
    stud_common = determine_common_students(df_before, df_after, id_column)

    # Extract data from both dataframes for common questions only
    df_before = df_before[[id_column, *questions]]
    df_after = df_after[[id_column, *questions]]

    # Extract data only for common students
    df_bf = df_before[df_before[id_column].isin(stud_common)]
    df_af = df_after[df_after[id_column].isin(stud_common)]

    # create shorthands for the questions
    quests_before = [f'before_{n:02}' for n in range(1, len(questions)+1)]
    quests_after = [f'after_{n:02}' for n in range(1, len(questions)+1)]

    # combine into single dataset with only
    # overlapping students and questions in Pre and Post survey results
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

    # apply Ttest for each student
    stud_pairs = []
    for stud in stud_common:
        before = df_bf[df_bf[id_column] == stud][quests_before[1:]].values[0]
        after = df_af[df_af[id_column] == stud][quests_after[1:]].values[0]
        res = stats.ttest_rel(before, after)
        stud_pairs.append(
            {id_column: stud, 'statistic': res.statistic, 'pvalue': res.pvalue})

    # turn results into dataframes
    df_pairs = pd.DataFrame(pairs)
    df_stud_pairs = pd.DataFrame(stud_pairs)
    question_legend = [questions, quests_before, quests_after]
    df_legend = pd.DataFrame(question_legend).T
    df_legend.columns = ['Question', 'Before_question_ID', 'After_question_ID']

    # for nices output: order by student ID or question
    df_pairs = df_pairs.sort_values(by=['question'])
    df_stud_pairs = df_stud_pairs.sort_values(by=[id_column])

    return df_pairs, df_combined, df_legend, df_bf, df_af, df_stud_pairs
