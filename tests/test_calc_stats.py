import numpy as np
import pandas as pd
from pathlib import Path
from anon_excel.calc_stats import category_to_rank
from anon_excel.ranking_data import load_ranking_from_folder, get_rank_lookup

RANK_TEST_DATA = [{'Your student number': 's123495',
                   'I trust others in this course': 'Strongly agree (SA)',
                   'I feel reluctant to speak openly': 'Strongly agree (SA)'},
                  {'Your student number': 's125676',
                   'I trust others in this course': 'Agree (A)',
                   'I feel reluctant to speak openly': 'Agree (A)'},
                  {'Your student number': 's147612',
                   'I trust others in this course': 'Neutral (N)',
                   'I feel reluctant to speak openly': 'Neutral (N)'},
                  {'Your student number': 's189724',
                   'I trust others in this course': 'Disagree (D)',
                   'I feel reluctant to speak openly': 'Disagree (D)'},
                  {'Your student number': 's675437',
                   'I trust others in this course': 'Strongly Disagree (SD)',
                   'I feel reluctant to speak openly': 'Strongly Disagree (SD)'}]

load_ranking_from_folder(Path('data'))


def test_category_to_rank_do_not_change_input():
    df = pd.DataFrame(RANK_TEST_DATA)

    _ = category_to_rank(df)

    q1_orig = df['I trust others in this course'].values
    assert q1_orig[0] == 'Strongly agree (SA)'


def test_category_to_rank_positiv():
    '''test proper changing the categorized answers to numerical,
       using a positive ranking for the first question
       and a negative ranking for the second question
    '''
    df = pd.DataFrame(RANK_TEST_DATA)

    new_df = category_to_rank(df)

    q1 = new_df['I trust others in this course'].values
    q2 = new_df['I feel reluctant to speak openly'].values

    arr1 = np.array([4, 3, 2, 1, 0])
    arr2 = np.array([0, 1, 2, 3, 4])

    assert np.array_equal(q1, arr1)
    assert np.array_equal(q2, arr2)
