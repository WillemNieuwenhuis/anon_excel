from pathlib import Path
import mock

from anon_excel.anon import remove_previous_results
from anon_excel.survey_files import find_survey_files, strip_leading_letter


@mock.patch('anon_excel.anon.Path.glob')
def test_find_survey_files_none(mock_glob):
    '''Check when no survey files are found'''
    mock_glob.return_value = []
    folder = Path('data')
    files = find_survey_files(folder)
    assert len(files) == 0


@mock.patch('anon_excel.anon.Path.glob')
@mock.patch('anon_excel.anon.Path.exists')
def test_find_survey_files_one_of_two(mock_exists, mock_glob):
    '''Check for return of tuples with existing pre and post surveys'''
    mock_glob.return_value = ['Pre_survey1.xlsx', 'Pre_survey2.xlsx']
    mock_exists.side_effect = [False, True]
    folder = Path('data')
    files = find_survey_files(folder)
    assert len(files) == 1
    assert files[0][1] == Path('Post_survey2.xlsx')


@mock.patch('anon_excel.anon.Path.glob')
@mock.patch('anon_excel.anon.Path.exists')
def test_find_survey_files_two_of_two_missing_post(mock_exists, mock_glob):
    '''Check for return of tuples with existing pre and optional post'''
    mock_glob.return_value = ['Pre_survey1.xlsx', 'Pre_survey2.xlsx']
    mock_exists.side_effect = [False, True]
    folder = Path('data')
    files = find_survey_files(folder, allow_missing_post=True)
    assert len(files) == 2
    assert len(files[0][1].name) == 0
    assert files[1][1] == Path('Post_survey2.xlsx')


@mock.patch('anon_excel.anon.Path.glob')
@mock.patch('anon_excel.anon.Path.exists')
def test_find_survey_files_two_of_two(mock_exists, mock_glob):
    mock_glob.return_value = ['Pre_survey1.xlsx', 'Pre_survey2.xlsx']
    mock_exists.side_effect = [True, True]
    folder = Path('data')
    files = find_survey_files(folder)
    assert len(files) == 2
    assert files[0][1] == Path('Post_survey1.xlsx')
    assert files[1][1] == Path('Post_survey2.xlsx')


@mock.patch('anon_excel.anon.os.remove')
def test_remove_previous_results_called(mock_remove):
    files = [Path(p) for p in ['analysis_course1.xlsx', 'analysis_course2.xlsx']]
    remove_previous_results(files, which_output='analysis', do_overwrite=True)
    assert mock_remove.call_count == 2
    assert mock_remove.call_args_list == [mock.call(f) for f in files]


@mock.patch('anon_excel.anon.os.remove')
def test_remove_previous_results_called_for_non_matching_files(mock_remove):
    files = [Path(p) for p in ['analysis_course1.xlsx', 'analysis_course2.xlsx']]
    remove_previous_results(files, do_overwrite=True, which_output='cleaned')
    assert mock_remove.call_count == 2
    assert mock_remove.call_args_list == [mock.call(f) for f in files]


def test_strip_leading_letter():
    assert strip_leading_letter('A123') == '123'
    assert strip_leading_letter('B456789') == '456789'
    assert strip_leading_letter('') == ''
    assert strip_leading_letter('012') == '012'
    assert strip_leading_letter('!345') == '345'
    assert strip_leading_letter('345abc') == '345abc'
