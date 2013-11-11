import os
basedir = os.path.abspath(os.path.dirname(__file__))

global_config =  {   'CSRF_ENABLED': True,
    'SECRET_KEY' : '42',
    'OPENID_PROVIDERS' : [
        { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
        { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
        { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' },
    ] ,
    'TEMP_DIR':os.path.join(basedir, 'tmp')
}

test = {}
test.update(global_config)
test.update( { 'SQLALCHEMY_DATABASE_URI' : 'sqlite://'} ) # this is sqlalchemy's syntax for an in memory sqlite3 db


db_uri = 'sqlite:///' + basedir + '/tmp/dev.db'
dev = {}
dev.update(global_config)
dev.update(  {'SQLALCHEMY_DATABASE_URI': db_uri})
providers = dev['OPENID_PROVIDERS']

providers.append({ 'name': 'FakeFake', 'url': 'http://localhost:8000/id/mrpurple' })

