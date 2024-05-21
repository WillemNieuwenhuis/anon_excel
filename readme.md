# Calculate paired T-test

## Installation
The app is a python application and can be installed with pip:

```shell
pip install anon_excel-1.0.0-py3-none-any.whl
```
This will also install all dependencies (pandas and scipy).

## Usage

```
usage: anonex [-h] [-c COLUMN [COLUMN ...]] [-x] [-t] [-o] folder

This app scans multiple sets of surveys. The survey data is cleaned up and optionally saved (default:no), and optionally a T-test analysis  
is performed and saved (default:yes). Personal information is removed.

positional arguments:
  folder                Specify the folder with the excel report(s)

options:
  -h, --help            show this help message and exit
  -c COLUMN [COLUMN ...], --column COLUMN [COLUMN ...]
                        Specify the columns (by name) to make anonymous
  -x, --clean           Read and clean the data
  -t, --ttest           Perform T-test calculation
  -o, --overwrite       Overwrite existing excel outputs
```

## The surveys
Inputs are surveys with common questions and students. The surveys are
in Excel format. Surveys come in a pre-course survey and a post-course survey. The
pre-course survey contains the survey result before lecture/workshop/course.
The post-course survey contains survey results obtained after the
lecture/workshop/course.

Multiple sets of pre- and post-course surveys are allowed.
The filenames of pre- and post-course surveys are the same, but the
pre-course survey starts with `Pre`, while the post-course surveys starts
with `Post`. For example:

```
Pre-Course Survey_ Perceived Sense of Community in Blended Learning(1-5).xlsx
Post-Course Survey_ Perceived Sense of Community in Blended Learning(1-5).xlsx
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
survey values to numerical values. For example:

```
Scoring.xlsx
```

## Requirements
The application will generate multiple outputs:
- Paired T-test results, for both dimensions: questions and students
- Table with numerical rankings per question for all students: one with
   pre- and post survey questions combined, one table with the pre-survey
   questions and one with the post-survey questions. Only questions
   common to pre- and post- survey are included
- A legend connecting the shorthand question names with the original question

### Approach
1. Find sets of surveys, if none found stop.
1. Clean the survey data
1. Hash the student data to remove possibility of identification
1. Recode the categorical ranking into numerical values 
1. Extract only the common questions from both surveys
1. Filter the data to only use data from students participating in both surveys
1. Calculate the T-test for each question

### Anonymize student ID's

Turn ID codes in a unique code. This is done with a hashing function
called "blake2b". This is a stable hashing function to guarantuee that the
hashcode will be the same for the same student each time, as well as unique.

The hashed code will be only be visible in the optional cleaned data. In the analysis
result the anonymized ID's are replaced with human readable ID's: **student_nn**; all other identifyable 
data is absent from the analysis results.

