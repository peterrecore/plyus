#!python
from flask.ext import script
from plyus import app

manager = script.Manager(app)

@manager.command
def hello():
    "say hello" 
    print "hello"


@manager.command
def create_db():
    from plyus import db
    db.create_all()

@manager.command
def run():
   app.run(debug = True) 

if __name__ == "__main__":
    manager.run()
