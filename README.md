To run this project, you will need to do the following:
- install python 2.7
- install pip and virtualenv
- create a new virtualenv for this project
- activate your new virtualenv
- use pip to install the packages in env/requirements.txt
- you can now use manage.py to create a database or run the webapp in dev mode.

Random notes:
- I wanted games to be repeatable, so there's some effort dedicated to saving
  the state of the random number generator, which probably looks confusing.

- I want games to be persisted in a database, so games can be played over days or weeks.
