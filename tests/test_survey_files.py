from pathlib import Path
import mock
import pytest

from anon_excel.anon import find_survey_files


@mock.patch('anon_excel.anon.glob')
def test_find_survey_files_none(mock_glob):
    mock_glob.return_value = []
    folder = Path('data')
    files = find_survey_files(folder)
    assert len(files) == 0


@mock.patch('anon_excel.anon.glob')
@mock.patch('anon_excel.anon.Path.exists')
def test_find_survey_files_one_of_two(mock_exists, mock_glob):
    mock_glob.return_value = ['Pre_survey1.xlsx', 'Pre_survey2.xlsx']
    mock_exists.side_effect = [False, True]
    folder = Path('data')
    files = find_survey_files(folder)
    assert len(files) == 1
    assert files[0][1] == Path('Post_survey2.xlsx')


@mock.patch('anon_excel.anon.glob')
@mock.patch('anon_excel.anon.Path.exists')
def test_find_survey_files_two_of_two(mock_exists, mock_glob):
    mock_glob.return_value = ['Pre_survey1.xlsx', 'Pre_survey2.xlsx']
    mock_exists.side_effect = [True, True]
    folder = Path('data')
    files = find_survey_files(folder)
    assert len(files) == 2
    assert files[0][1] == Path('Post_survey1.xlsx')
    assert files[1][1] == Path('Post_survey2.xlsx')
