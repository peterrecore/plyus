import logging
from plyus import db
from plyus.user import User
from plyus.gamestate import GameState
from plyus.player import Player
from plyus.errors import FatalPlyusError

WAITING_FOR_PLAYERS = 1
WAITING_TO_START = 2


class ProtoGame(db.Model):
    __tablename__ = "proto_games"
    id = db.Column(db.Integer, primary_key = True)

    status = db.Column(db.String)
    num_players = db.Column(db.Integer)
    real_game = db.Column(db.Integer, db.ForeignKey(GameState.id))
    proto_players = db.relationship("ProtoPlayer")

    owner_id = db.Column(db.Integer, db.ForeignKey(User.id))

    def __init__(self, n, owner):
        self.owner_id = owner.id
        self.num_players = n
        pp = ProtoPlayer(owner)
        self.proto_players = [pp]
        self.status = WAITING_FOR_PLAYERS

    def can_user_join(self, user):
        if self.is_full():
            return False
        #TODO: Should this be done via a sql query or a for loop like this?
        for pp in self.proto_players:
            if user.id == pp.user_id:
                return False
        return True

    def join_user(self, user):
        if self.can_user_join(user):
            pp = ProtoPlayer(user)
            self.proto_players.append(pp)
            if self.is_full():
                self.status = WAITING_TO_START
            logging.info("user %s has been added as protoplayer %s to protogame %s",user, pp, self)
        else:
            logging.warn("user %s can't join protogame %s but was trying to.",user, self)
            raise FatalPlyusError("Can't join this game. maybe because game is full?")


    def can_user_start(self, user):
        if self.is_full and user.id == self.owner_id:
            return True
        return False

    def is_full(self):
        return len(self.proto_players) >= self.num_players

class ProtoPlayer(db.Model):
    """This class will link player objects to a user object, without the player object having
    to know anything about Users. This is an extra level of indirection, but without it,
     player objects, and therefore the whole game engine would need to know about Users"""
    __tablename__ = "proto_players"
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship("User")
    player_id = db.Column(db.Integer, db.ForeignKey(Player.id))
    player = db.relationship("Player", uselist=False)
    proto_game_id = db.Column(db.Integer, db.ForeignKey(ProtoGame.id), nullable = False)

    def __init__(self, u):
        self.user_id = u.id
#        self.proto_game_id = pg_id

    def __repr__(self):
        return "ProtoPlayer(user_id=%s)" % self.user_id
