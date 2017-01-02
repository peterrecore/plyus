To run this project, you will need to do the following:
- install python 3.6 or higher
- create a new virtualenv for this project
 - python -m venv venv3
- activate your new virtual env  (by sourcing the activate script in venv3/bin)
- use pip to install the packages in requirements.txt
- you can now use manage.py to create a database or run the webapp in dev mode.


Random notes:
- I wanted games to be repeatable, so there's some effort dedicated to saving
  the state of the random number generator, which probably looks confusing.

- I want games to be persisted in a database, so games can be played over days or weeks.


Running Unit Tests:
python -m unittest tests.testsql

*Versions:*
- 0.5: all existing tests run, but web functionality not currently tested.  last version before conversion to python 3
- 0.6: will upgrade to python 3 and latest version of flask and other libs.

patch for defusexml for openid:
2 files, elementtree and common.py