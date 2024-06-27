# Calculate paired T-test

## Installation
The app is a python application and can be installed with pip:

```shell
pip install anon_excel-1.0.0-py3-none-any.whl
```
This will also install all dependencies (pandas and scipy).

## Usage

```
usage: anonex [-h] [-a] [-c] [-o] [-s] [-t] [-x] folder

This app scans multiple sets of surveys. It offers an option to clean and store the survey data, and also an option to perform and store a T-test analysis. The T-test is only possible when both pre- and post- survey is available.
Optionally personal information is removed.

positional arguments:
  folder           Specify the folder with the excel report(s)

options:
  -h, --help       show this help message and exit
  -a, --anonymize  Anonymize personal data (default = No)
  -c, --color      Add colors in excel file with clean ranked data (default = No)
  -o, --overwrite  Overwrite existing excel outputs (default = No)
  -s, --strip      Strip leading s-char from s-number (default = No)
  -t, --ttest      Perform T-test calculation (default = No)
  -x, --clean      Save cleaned data (default = No)
```

## The surveys
Inputs are surveys with common questions and students. The surveys are
in Excel format. Surveys come in a pre-course survey and a post-course survey. The
pre-course survey contains the survey result before lecture/workshop/course.
The post-course survey contains survey results obtained after the
lecture/workshop/course.

Only a single set of pre- and post-course surveys is expected.
The filenames of pre- and post-course surveys are unique: the pre-course survey
starts with `Pre`, the post-course surveys starts with `Post`. For example:

```
Pre-Course Survey_ Perceived Sense of Community in Blended Learning(1-89).xlsx
Post-Course Survey_ Perceived Sense of Community in Blended Learning(1-34).xlsx
```

Properties of the surveys:
- Both contain student ID's and thus can identify individuals
- The lists of students do not have to be identical
- The lists of questions do not have to be the same
- The answers of the questions are categorical:
    (Strongly agree (SA), Agree (A), Neutral (N),
    Disagree (D), Strongly Disagree (SD)

### Ranking table
An additional input is the translation table to link the categorical
survey values to numerical values. The location is assumed to be in the same
folder as the survey data files. For now the name of this ranking table is fixed to:

```
Scoring.xlsx
```

>[!**Note**]
The ranking table is unique for each set of surveys.


## Application requirements
The application can generate multiple outputs:  both cleaned data and T-test are optional.
When a T-test is calculated cleaning will also be run, but saving the cleaned data is still
optional.
Cleaned data excel file:
- Output of cleanup up data for both pre-survey and post-survey data
Analysis output excel file:
- Paired T-test results, for both dimensions: questions and students
- Descriptive statistics for the questions
- Table with numerical rankings per question for all students: one table
   with the pre-survey questions and one with the post-survey questions. 
   Only questions common to pre- and post- survey are included
- A legend connecting the shorthand question names with the original question

### Approach
1. Find sets of surveys, if none found stop.
1. Optionally encrypt the student data to remove possibility of identification
1. Recode the categorical ranking into numerical values 
1. Clean the survey data; for cleaning only post-survey data is not required
1. Optionally save the cleanup data. Data will be stored in subfolder **cleaned**
1. App is finished if no T-test is specified
1. Extract only the common questions from both surveys
1. Filter the data to only use data from students participating in both surveys
1. Calculate the T-test for each question
1. Calculate the T-test for each student
1. Save the result to the subfolder **analysis**

### Anonymize student ID's

Turn ID codes in a unique code. This is done with a hashing function
called "blake2b". This is a stable hashing function to guarantuee that the
hashcode will be the same for the same student each time, as well as unique.

The hashed code will be only be visible in the optional cleaned data, and when
the `anonymize` command line parameter is set appropriately. In the analysis
result the anonymized ID's are replaced with human readable ID's: **student_nn**;
all other identifyable data is absent from the analysis results.

