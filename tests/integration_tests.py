import unittest
import json
import random
import logging
import collections
from plyus.util import *
from plyus.misc import *
from plyus.player import Player 
from plyus.gamestate import GameState 
from plyus.referee import Referee 
from simpleai import SimpleAIPlayer
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker

def create_session_maker():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.WARNING) 
        logging.warning("info level set.")
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING) 

    def test_two_players_simpleai(self):
        self.do_one_test(0, 2)
        self.do_one_test(1, 2)
        self.do_one_test(42, 2)

    def test_three_players_simpleai(self):
        self.do_one_test(0, 3)
        self.do_one_test(2, 3)
        self.do_one_test(4, 3)

    def test_five_players_simpleai(self):
        self.do_one_test(4, 5)
        self.do_one_test(9, 5)
        self.do_one_test(7, 5)

    def test_four_players_simpleai(self):
        self.do_one_test(4, 4)
        self.do_one_test(3, 4)
        self.do_one_test(2, 4)



    def create_players_and_ais(self, num_players):
        names = ['PeterAI', 'MananAI','AndyAI','MarkAI','KevinAI','RyanAI','TabithaAI'] 
        ais = {}
        players = []
        for n in names[0:num_players]:
           ais[n] = SimpleAIPlayer(n)
           players.append(Player(n))
        return (players, ais)

    def get_game_for_id(self, sess, game_id):
        g = sess.query(GameState).filter(GameState.id == game_id).one()
        return g

    def do_one_test(self, seed, num_players):
        players, ais = self.create_players_and_ais(num_players)
        session_maker = create_session_maker()
        sess = session_maker()
        game_id = self.create_new_game(seed, sess, players)
        sess.close()

        max_steps = 100 * len(players)

        finished_cleanly = False
        for step_num in range(max_steps):
            sess = session_maker()
            game = self.get_game_for_id(sess, game_id)

            self.process_ai_move(game, ais) 

            sess.commit() 
            if game.stage == Stage.GAME_OVER :
                self.log_game_results(game)
                finished_cleanly = True
                sess.close()
                break
            sess.close()

        self.assertTrue(finished_cleanly, "finish before 100 steps per player")

    def process_ai_move(self, game, ais):
        ref = Referee(game)
        cur_plyr = game.get_cur_plyr()
        cur_ai = ais[cur_plyr.name]
        json = ref.get_current_state_as_json_for_player(cur_plyr.position)
        parsed_json = util.from_json(json) 
        move = cur_ai.decide_what_to_do_json(parsed_json)
        ref.perform_move(move)
        logging.info("After processing ai move, stage is %s ", game.stage)

    def log_game_results(self, game):
       logging.warning("**********************************************")
       logging.warning("******* Success, game over and %s won after %s rounds  ******" % (game.winner,game.round_num)) 
       for p in game.players:
         logging.warning("Player %s had %s pts" % (p.name, p.points))


    def create_new_game(self, seed, sess, players):
        game = GameState()
        game.initialize_game(seed,players, deck_template='decks/deck_test_60.csv')
        sess.add(game) 
        sess.commit()
        return game.id


 