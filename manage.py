#!python
from flask.ext import script
import plyus
import config

plyus.create_flask_app(config.dev)
manager = script.Manager(plyus.app)


@manager.command
def create_db():
    from plyus import db

    db.create_all()


@manager.command
def run():
    plyus.app.run(debug=True)

@manager.command
def diagram():
    from sqlalchemy_schemadisplay import create_schema_graph
    from plyus import db

    # Database
    host     = 'localhost'
    engine   = 'postgresql'
    database = 'database'
    username = 'username'
    password = 'password'

    # General
    data_types = False
    indexes    = False


    # Generation
    dsn = engine + '://' + username + ':' + password + '@' + host + '/' + database;


#    graph = create_uml_graph(db.Model)
    graph = create_schema_graph(metadata=db.Model.metadata)

    graph.write_png('schema.png')



if __name__ == "__main__":
    manager.run()
