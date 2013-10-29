from flask import flash, Flask, render_template, redirect,url_for, g, session,request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import login_user, logout_user, current_user, login_required

from plyus import app
from plyus import db, lm, oid
from plyus.user import User, PlayerProxy
from plyus.gamestate import GameState
from plyus.forms import LoginForm, NewGameForm
from plyus.player import Player

# Login related functions

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
    return render_template('login.html',
        title = 'Sign In',
        form = form,
        providers = app.config['OPENID_PROVIDERS'])


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('list_games'))

@app.before_request
def before_request():
    g.user = current_user


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname = nickname, email = resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('list_games'))

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/games')
def list_games():
    app.logger.warn("entered list_ games")
    app.logger.warn("config is %s" % app.config)
    games = GameState.query.all()
    app.logger.warn("got games")
    return render_template("sample.html",games_in_template = games )

@app.route('/game/<int:gid>')
@login_required
def show_game(gid):
    game = GameState.query.filter(GameState.id==gid).first()
    return render_template("game.html", game = game.to_dict_for_public())

@app.route('/game/new', methods=['GET', 'POST'])
@login_required
def new_game():
    form = NewGameForm()
    if form.validate_on_submit():
        seed = 37

        creator = Player(g.user.nickname )
        game = GameState(seed, creator, form.num_players.data)
        proxy = PlayerProxy(g.user, creator)
        db.session.add(game)
        db.session.add(proxy)
        db.session.commit()
        return redirect(url_for('show_game',gid=game.id))
    else:
        return render_template("new_game.html",form=form)

@app.route('/hello')
def hello():
    app.logger.warn("about to say hello")
    return 'hello works fine'

