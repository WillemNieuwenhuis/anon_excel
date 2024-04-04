# Calculate paired T-test

## Installation
The app is a python application and can be installed with pip:

```shell
pip install anon_excel-1.0.0-py3-none-any.whl
```
This will also install all dependencies (pandas and scipi).

## Usage
Syntax:
```
anonex 
```
Start a console

## The surveys
Inputs are two surveys with common questions and students. The surveys are
in Excel format. The first survey (filename is assumed to start with "Pre") contains
the survey result before lecture/workshop/course. The second survey (filename is assumed
to start with "Post") contains surveys results obtained after the lecture/workshop/course.

Properties of the surveys:
- Both contain student ID's and thus can identify individuals
- The lists of students do not have to be identical
- The lists of questions do not have to be the same
- The answers of the questions are categorical:
    (Strongly agree (SA), Agree (A), Neutral (N),
    Disagree (D), Strongly Disagree (SD)

## Requirements
The application will generate multiple outputs:
- Paired T-test results
- A table with rankings per question for all students
- A legend connecting the shortened question names with the original question

### Approach
1. Find both surveys, if not found stop.
1. Clean the data if needed
1. Hash the student data to remove possibility of identification
1. Recode the categorical ranking into numerical values 
1. Extract only the common questions from both surveys
1. Filter the data to only use data from students participating in both surveys
1. Calculate the T-test for each question

### Anonymize student ID's

Turn ID codes in a unique code. This is done with a hashing function
called "blake2b". This is a stable hashing function to guarantuee that the
hashcode will be the same for the same student each time, as well as unique.

The hashed code will be visible in the analysis result; all other identifyable 
data is removed.

