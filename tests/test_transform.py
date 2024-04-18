import pandas as pd

from anon_excel.anon import transform_to_anonymous

ANONIMIZE_DATA = [{'Your student number': 's12345',
                   'q1': 'Agree (A)',
                   'q2': 'Disagree (D)'},
                  {'Your student number': 's125676',
                   'q1': 'Agree (A)',
                   'q2': 'Agree (A)'}]


def test_transform_to_anonymous_no_id_col():
    '''test no change when on_column is missing in df'''
    df = pd.DataFrame(ANONIMIZE_DATA)

    df_new = transform_to_anonymous(df, 'My student number', 'anon')

    assert df_new.equals(df)


def test_transform_to_anonymous_id_col_removed():
    '''test that the on column data is removed after
       succesfully anonimizing student numbers and the new
       anonimzed column has been added
    '''
    df = pd.DataFrame(ANONIMIZE_DATA)

    df_new = transform_to_anonymous(df, 'Your student number', 'anon')
    assert 'Your student number' not in df_new.columns
    assert 'anon' in df_new.columns
