from unittest.mock import Mock
import pytest
from anon_excel.anon import determine_survey_data_name


@pytest.mark.parametrize("filename, sequence_nr, expected", [
    ("data_survey_(1-89).xlsx", 1, "data_survey_(1-89)"),
    ("data_survey.xlsx", 2, "data_survey_02"),
    ("data_survey_(1-89)_(2-90).xlsx", 3, "data_survey_(1-89)"),
    ("prefix_(1-89)_suffix.xlsx", 4, "data_survey_(1-89)"),
    ("(1-89)_data_survey.xlsx", 5, "data_survey_(1-89)"),
    ("data_survey_(1-89).xlsx", 6, "data_survey_(1-89)")
])
def test_determine_survey_data_name(filename, sequence_nr, expected):
    survey_file = Mock()
    survey_file.name = filename
    assert determine_survey_data_name(survey_file, sequence_nr) == expected


def test_determine_survey_data_name_with_non_path_input():
    with pytest.raises(AttributeError):
        # Passing an integer instead of a Path object
        determine_survey_data_name(123, 1)
