from pathlib import Path
import mock

from anon_excel.anon import find_survey_files, remove_previous_results


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


@mock.patch('anon_excel.anon.os.remove')
def test_remove_previous_results_called(mock_remove):
    files = [Path(p) for p in ['analysis_course1.xlsx', 'analysis_course2.xlsx']]
    remove_previous_results(files)
    assert mock_remove.call_count == 2
    assert mock_remove.call_args_list == [mock.call(f) for f in files]
