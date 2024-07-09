ANALYSIS_OUTPUT_BASE = 'analysis'
CLEANED_OUTPUT_BASE = 'cleaned'
DATA_OUTPUT_BASENAME = 'data_survey'
ANONYMOUS_ID = 'student_anon'
CLEAN_SHEET_PRE_SURVEY = 'Clean pre-survey'
CLEAN_SHEET_POST_SURVEY = 'Clean post-survey'

# name of ID column in the surveys:
# Note that this column will NOT end up in the cleaned and final outputs
DEFAULT_STUDENT_COLUMN = 'Your student number'
# columns to drop in cleaned output
DROP_COLUMNS = ['ID', 'Start time', 'Completion time',
                'Email', 'Name', 'Last modified time']
