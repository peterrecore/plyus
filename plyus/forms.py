from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField
from wtforms.validators import Required


class LoginForm(Form):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)


class NewGameForm(Form):
    num_players = SelectField('Number of Players', choices=[('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])