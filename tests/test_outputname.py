from pathlib import Path
from anon_excel.anon import determine_survey_data_name


def test_determine_survey_data_name_with_valid_pattern():
    '''check for filename with (n-m)'''
    fn = Path('Post- Course Survey_ Perceived Sense of Community in Blended Learning(1-89).xlsx')
    res = determine_survey_data_name(fn, 7)
    assert res == 'data_survey_(1-89)'


def test_determine_survey_data_name_with_sequence():
    fn = Path('Post- Course Survey_ Perceived Sense of Community in Blended Learning.xlsx')
    res = determine_survey_data_name(fn, 7)
    assert res == 'data_survey_07'


def test_determine_survey_data_empty_filename():
    fn = Path('')
    res = determine_survey_data_name(fn, 7)
    assert res == 'data_survey_07'
