import unittest
import logging

import plyus
import config
plyus.create_flask_app(config.test)

from plyus.player import Player
from plyus.misc import BuildingDeck
from plyus.gamestate import GameState
from plyus.user import User
from plyus.proto import ProtoGame, ProtoPlayer

def create_session_maker():
    return plyus.db.create_scoped_session


class TestSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG) 
        logging.warning("logging level set in TestSQL")
        plyus.db.drop_all()
        plyus.db.create_all()

    def test_save_and_load(self):
        deck_template = 'decks/deck_test_30.csv' 
        p1 = Player("peter")
        p2 = Player("manan")
        g = GameState(42, p1, 2, deck_template)
        g.add_player(p2)
        g.start_game()

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


        p1_loaded = session.query(Player).filter(Player.name=='peter' , Player.gamestate_id == gs_id).one()
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


    def test_protos(self):
        #create 2 protogames, and include user 1 in both. once as owner, once as player that user should have 2 protoplayers
        sess = create_session_maker()()


        u1 = User(nickname="peternick", email="peter@example.org")
        u2 = User(nickname="manannick", email="manan@example.org")
        u3 = User(nickname="marknick", email="mark@example.org")
        sess.add_all([u1, u2, u3])
        sess.flush()

        for u in [u1,u2,u3]:
            logging.debug("user %s has id %s" % (u.nickname, u.id))

        pg1 = ProtoGame(2, u1)
        pg2 = ProtoGame(2, u3)

        pp1 = ProtoPlayer(u1)
        pp2 = ProtoPlayer(u2)

        pg1.proto_players.append(pp2)
        pg2.proto_players.append(pp1)

        sess.add(pg1)
        sess.add(pg2)

        sess.commit()


        p_u1g1 = Player("peter in game 1")
        p_u2g1 = Player("manan in game 1")

        p_u1g2 = Player("peter in game 2")
        p_u2g2 = Player("peter in game 2")



        deck_template = 'decks/deck_test_30.csv'

        logging.debug("u1 protoplayers are %s" % u1.proto_players)

        self.assertEqual(len(u1.proto_players), 2)
        self.assertEqual(len(u2.proto_players), 1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    unittest.main()
