from flask import flash, render_template, redirect, url_for, g, session, request
from flask.ext.login import login_user, logout_user, current_user, login_required

from plyus import app
from plyus import lm, oid
from plyus.user import User
from plyus.gamestate import GameState
from plyus.forms import LoginForm, NewGameForm
from plyus.proto import *
# Login related functions

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('games'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        x = oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
        app.logger.warn("got result from try_login: %s", x)
        return x
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


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
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('list_games'))


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/games')
def list_games():
    app.logger.warn("entered list_ games")
    app.logger.warn("config is %s" % app.config)
    games = ProtoGame.query.all()
    app.logger.warn("got games")
    return render_template("games_list.html", games_in_template=games)


@app.route('/games/my')
@login_required
def list_my_games():
    waiting_statuses = (ProtoGame.WAITING_FOR_PLAYERS, ProtoGame.WAITING_TO_START)
    waiting = ProtoGame.query.join(ProtoPlayer)\
            .filter(ProtoPlayer.user_id == g.user.id)\
            .filter(ProtoGame.status.in_(waiting_statuses))\
            .all()
    in_progress = ProtoGame.query.join(ProtoPlayer).filter(ProtoPlayer.user_id == g.user.id).filter(ProtoGame.status == ProtoGame.PLAYING).all()

    return render_template("games_my_list.html",games_in_progress = in_progress, games_waiting = waiting)

@app.route('/games/joinable')
@login_required
def list_games_joinable():
    games = ProtoGame.query.filter_by(status=ProtoGame.WAITING_FOR_PLAYERS).all()
    return render_template("games_join.html", games=games)


@app.route('/protogame/join/<int:gid>')
def join_proto_game(gid):
    proto_game = ProtoGame.query.filter(ProtoGame.id == gid).one()
    proto_game.join_user(g.user)
    db.session.commit()
    app.logger.info("added user %s to protogame", g.user.email)
    return redirect(url_for("show_proto_game", gid=gid))


@app.route('/game/<int:gid>')
@login_required
def show_game(gid):
    game = GameState.query.filter(GameState.id == gid).one()
    return render_template("game.html", game=game.to_dict_for_public())


@app.route('/protogame/<int:gid>')
@login_required
def show_proto_game(gid):
    proto_game = ProtoGame.query.filter(ProtoGame.id == gid).one()
    can_join = proto_game.can_user_join(g.user)
    return render_template("protogame.html", game=proto_game, show_join_button=can_join)


@app.route('/game/new', methods=['GET', 'POST'])
@login_required
def new_game():
    form = NewGameForm()
    if form.validate_on_submit():
        seed = 37

        proto_game = ProtoGame(form.num_players.data, g.user)
        app.logger.warn("proto_players is %s" % proto_game.proto_players)
        db.session.add(proto_game)
        db.session.commit()
        return redirect(url_for('show_proto_game', gid=proto_game.id))
    else:
        return render_template("new_game.html", form=form)


@app.route('/fakelogin/<string:fake_name>', methods=['GET'])
def fake_login(fake_name):
    user = User.query.filter_by(email=fake_name).first()
    if user is None:
        user = User(nickname=fake_name, email=fake_name)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=False)
    return redirect(url_for('list_games'))
