import logging
import csv
import util
import random
from collections import defaultdict
from plyus.mutable import MutableList 
from plyus.mutable import MutableDict 
from plyus.mutable import JSONEncoded
from plyus.util import lowest_higher_than
from plyus.util import reverse_map
from plyus.errors import NotYourTurnError
from plyus.errors import IllegalActionError
from plyus.errors import NoSuchActionError
from plyus.errors import FatalPlyusError 
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref


Base = declarative_base()


class BuildingDeck(Base):
    __tablename__ = "buildingdecks"
    id = Column(Integer,primary_key=True)
    game_state_id = Column(Integer, ForeignKey("gamestates.id"))
    template = Column(String)
    cards = Column(MutableList.as_mutable(JSONEncoded)) 
    card_map = None
    full_cards = None

    def __init__(self, template):
        """ template is a file name for now.  Might be a database id later """
        self.template = template
        self._construct_card_map()
        self.cards = list(self.card_map.keys())

    def _construct_card_map(self):

        if self.full_cards is None:
            self.full_cards = self._create_deck_from_csv(self.template) 

        if self.card_map is None:
            self.card_map = dict([(c.id,c) for c in self.full_cards]) 

    def card_for_id(self, card_id):
        if self.card_map is None:
            self._construct_card_map()
        return self.card_map[card_id]

    def _create_deck_from_csv(self, filename):

        def card_from_line(line):
            return Building(int(line[0]), line[1], int(line[2]), line[3])

        with open(filename, 'r') as myfile:
            lines = csv.reader(myfile)
            return [card_from_line(line) for line in lines]


class Building(object):

    def __init__(self,id, color, points, name, cost=None):
        self.id = id
        self.color = color
        self.points = points
        self.name = name
        self.cost = cost
        if cost is None:
            self.cost = points

    def __repr__(self):
        return "Building(id=%s, %s, %s, %s, %s)"% (self.id,self.name , self.color, self.points, self.cost)

    def __eq__(self, other):
        if type(self) is type(other):
            return self.id == other.id

#Each game consists of several stages, progressing forward relentlessly
# (no backsies or looping)
class Stage:
    PRE_GAME = 'PRE_GAME'  #still waiting for players to join
    PLAYING = 'PLAYING' # game has started
    END_GAME = 'END_GAME' #a player built 8 buidings, so this is the last round
    GAME_OVER = 'GAME_OVER' #last round finished, winners/scores recorded

#Each Round consists of two phases
class Phase:
    PICK_ROLES = 'PICK_ROLES'
    PLAY_TURNS = 'PLAY_TURNS'

#The Play turn phase consists of several steps
class Step:
    NO_STEP = 'NO_STEP'
    COINS_OR_BUILDING = 'COINS_OR_BUILDING'
    KEEP_CARD = 'KEEP_CARD'
    MURDER = 'MURDER'
    STEAL = 'STEAL'
    RAZE = 'RAZE'
    BUILD_BUILDING = 'BUILD_BUILDING' 
    PICK_ROLE = 'PICK_ROLE' 
    HIDE_ROLE = 'HIDE_ROLE' 
    FINISH = 'FINISH'


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    num = Column(Integer)
