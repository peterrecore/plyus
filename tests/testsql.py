import unittest
import json
import random
import logging
import collections
from util import *
from plyus import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker

def create_session_maker():
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

class TestSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG) 
        logging.warning("logging level set in TestSQL")

    def test_save_and_load(self):
        deck_template = 'decks/deck_test_30.csv' 
        p1 = Player("peter")
        p2 = Player("manan")
        g = GameState()
        g.initialize_game(42, [p1,p2], deck_template)

        p1.gold = 32
        p1.take_cards(g.building_card_deck.cards)

        session_maker = create_session_maker()
        session = session_maker()
        session.add(g)
        session.commit()

        gs_id = g.id
        session.close()

        new_session = session_maker()

        g_loaded = new_session.query(GameState).filter(GameState.id == gs_id).one()

        g_loaded.get_random_gen()

        self.assertEqual(g_loaded.base_seed, 42)


        p1_loaded = session.query(Player).filter(Player.name=='peter').one()
        p1_bad_copy = Player("peter")
        self.assertEqual("peter", p1_loaded.name)
        self.assertNotEqual(p1_loaded,p1_bad_copy)
        self.assertEqual(len(p1_loaded.buildings_buffer), 2)




    def test_building_deck_reconstruction(self):
        """ BuildingDecks have some transient fields like full_cards and card_map.  this test
            ensures that these fields get properly recreated after a buildingdeck is loaded from the db"""
        deck = BuildingDeck('decks/deck_test_30.csv')
        sess = create_session_maker()()
        sess.add(deck)
        sess.commit()
        id = deck.id

        deck = None
        loaded_deck = sess.query(BuildingDeck).filter(BuildingDeck.id == id).one()
        card = loaded_deck.card_for_id(3)
        self.assertEqual(card.id, 3)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    unittest.main()