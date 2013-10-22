from plyus import db
from plyus.player import Player

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), unique = True)

    player_proxies = db.relationship("PlayerProxy")

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class PlayerProxy(db.Model):
    """This class will link player objects to a user object, without the player object having
    to know anything about Users. This is an extra level of indirection, but without it,
     player objects, and therefore the whole game engine would need to know about Users"""
    __tablename__ = "player_proxies"
    user_id = db.Column(db.Integer, db.ForeignKey(User.id),primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey(Player.id), primary_key=True)
    player = db.relationship("Player", uselist=False)