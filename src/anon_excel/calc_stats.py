import logging
import pandas as pd
from scipy import stats
from anon_excel.ranking_data import rank_lookup


log = logging.getLogger(__name__)


def category_to_rank(df: pd.DataFrame) -> pd.DataFrame:
    ''' Transform answer categories to numerical rankings
    '''
    log.info('Transform categories to numerical values')
    df_rank = df.copy()
    for question, ranks in rank_lookup.items():
        if question in list(df_rank.columns):
            # strip whitespace
            df_rank[question] = df_rank[question].replace(r'\s+', ' ', regex=True)
            df_rank[question] = df_rank[question].map(ranks)

    return df_rank


def determine_common_questions(bf_quest: list, af_quest: list) -> list:
    '''
        Find questions available in both surveys
    '''
    qset = set(rank_lookup.keys())
    col_set_before = set(bf_quest)
    col_set_after = set(af_quest)
    common_cols = col_set_before.intersection(col_set_after)
    questions = list(qset.intersection(common_cols))
    return questions


def determine_common_students(bf_studs: list, af_studs: list) -> list:
    '''
        Find students common to both surveys
    '''
    stud_before = set(bf_studs)
    stud_after = set(af_studs)
    stud_common = stud_before.intersection(stud_after)

    return stud_common


def paired_ttest(df_before: pd.DataFrame, df_after: pd.DataFrame, id_column: str) -> \
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
              pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # first make sure the dataframe are ordered by the same column (student_anon)
    df_before = df_before.sort_values(by=[id_column])
    df_after = df_after.sort_values(by=[id_column])

    questions = determine_common_questions(df_before.columns, df_after.columns)
    stud_common = determine_common_students(
        df_before[id_column].values, df_after[id_column].values)

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
    # overlapping students and questions from Pre and Post survey results
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
