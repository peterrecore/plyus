import logging
from plyus.gamestate import GameState 
from plyus.misc import *
from plyus.mutable import MutableList 
from plyus.mutable import JSONEncoded
from plyus.util import draw_n
from plyus.errors import FatalPlyusError 
from plyus import db

#TODO:  make sure we can't have 2 players with the same name.  or else
# make sure we handle that case properly
class Player(db.Model):

    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    gamestate_id = db.Column(db.Integer, db.ForeignKey(GameState.id), nullable = False) 
    name = db.Column(db.String)
    position = db.Column(db.Integer)
    gold = db.Column(db.Integer)
    buildings_on_table = db.Column(MutableList.as_mutable(JSONEncoded))
    buildings_in_hand = db.Column(MutableList.as_mutable(JSONEncoded))
    buildings_buffer = db.Column(MutableList.as_mutable(JSONEncoded))
    cur_role = db.Column(db.Integer)
    roles = db.Column(MutableList.as_mutable(JSONEncoded))
    revealed_roles = db.Column(MutableList.as_mutable(JSONEncoded))
    rainbow_bonus = db.Column(db.Boolean)
    first_to_eight_buildings = db.Column(db.Boolean)
    points = db.Column(db.Integer)

    def __init__(self, n):
        self.name = n
        self.position = None
        self.gold = 2
        self.buildings_on_table = []
        self.buildings_in_hand = []
        self.buildings_buffer = []
        self.cur_role = None
        self.roles = []
        self.revealed_roles = []
        self.rainbow_bonus = False
        self.first_to_eight_buildings = False
        self.points = None

    #current player chooses to get gold
    def take_gold(self):
        self.gold += 2

    #when current player chooses to draw cards
    def take_cards(self, cards):
        if len(cards) < 2:
            #TODO: figure out and implement rule on reshuffling building cards 
            raise FatalPlyusError("Building deck is out of cards.")
        self.buildings_buffer = util.draw_n(cards, 2)

    def set_position(self, i):
        self.position = i

    def __repr__(self):
        return "Player(name=%s, pos=%s, cur_role= %s, roles=%s, gold=%s, hand=%r, dists=%s)" % (self.name, 
            self.position, self.cur_role, self.roles, self.gold, self.buildings_in_hand,self.buildings_on_table)

    def to_dict_for_public(self, deck):
        d = {}
        fields_to_copy = ['name','position','gold', 'points','revealed_roles']

        for k in fields_to_copy:
            d[k] = self.__dict__[k]
        
        d['buildings_on_table'] = [deck.card_for_id(i) for i in self.buildings_on_table]
        d['num_cards_in_hand'] = len(self.buildings_in_hand)

        return d


    def to_dict_for_private(self, deck):
        d = self.to_dict_for_public(deck)

        fields_to_copy = ['cur_role', 'roles']
        for k in fields_to_copy:
            d[k] = self.__dict__[k]
       
        d['buildings_in_hand'] = [deck.card_for_id(i) for i in self.buildings_in_hand]
        d['buildings_buffer'] = [deck.card_for_id(i) for i in self.buildings_buffer]
        return d
