import unittest
import json
import random
import logging
import collections
from util import *
from plyus import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker

def create_memory_session():
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

class TestSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG) 
        logging.warning("logging level set in TestSQL")

    def test_save_and_load(self):
        deck = Building.create_deck_from_csv('decks/deck_test_30.csv') 
        p1 = Player("peter")
        p2 = Player("manan")
        g = GameState()
        g.initialize_game(42, [p1,p2], deck)

        p1.gold = 32
        p1.take_cards(deck)

        session = create_memory_session()
        session.add(g)
        session.commit()

        gs_id = g.id

        g_loaded = session.query(GameState).filter(GameState.id == gs_id).one()

        self.assertEqual(g_loaded.seed, g.seed)


        p1_loaded = session.query(Player).filter(Player.name=='peter').one()
        p1_bad_copy = Player("peter")
        self.assertEqual(p1.name, p1_loaded.name)
        self.assertEqual(p1, p1_loaded)
        self.assertNotEqual(p1,p1_bad_copy)
        self.assertEqual(len(p1_loaded.buildings_buffer), 2)
        self.assertEqual(g_loaded.players[p1.position], p1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    unittest.main()
