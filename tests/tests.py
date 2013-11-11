import unittest
import json
import logging
import plyus
import config

plyus.create_flask_app(config.test)

from plyus.util import *
from plyus.errors import *
from plyus.player import Player
from plyus.referee import Referee
from plyus.round import Round
from plyus.gamestate import GameState
from plyus.misc import Stage, Building, BuildingDeck
from simpleai import SimpleAIPlayer


class TestAllTheThings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
    #        logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.WARNING)
        logging.warning("Warning level set.")

    def test_create_deck_from_file(self):
        deck = BuildingDeck('decks/deck_test_30.csv')
        self.assertEqual(len(deck.cards), 30)
        self.assertEqual(deck.full_cards[2], Building(3, "green", 2, "Fort Knox"))
        self.assertEqual(deck.card_for_id(3), Building(3, "green", 2, "Fort Knox"))
        self.assertEqual(deck.card_for_id(3).color, "green")


    def test_draw(self):
        given = [1, 2, 3, 4, 5]
        result = draw_n(given, 2)
        self.assertEqual(len(result), 2)
        self.assertListEqual(result, [1, 2])
        self.assertListEqual(given, [3, 4, 5])

    def test_building(self):
        foo = Building(1, "blue", 3, "NASA")
        self.assertTrue(foo.name == "NASA")

    @unittest.skip("skipping until we rewrite to not make it so fragile.")
    def test_valid_moves(self):
        self.do_test_using_json_from_file("moves.json", "valid_moves")


    def test_create_round(self):
        players = [fake_player("Peter"), fake_player("Manan")]
        game = GameState(42, players[0], 2, deck_template="decks/deck_test_30.csv")
        game.add_player(players[1])
        self.assertIsNotNone(game.to_dict_for_public(),
                             "to_dict shouldn't crash even if called before game is started and round is created")
        game.start_game()
        r = Round(game)

        self.assertEqual(len(r.face_up_roles), 0)
        self.assertEqual(len(r.face_down_roles), 1)
        self.assertEqual(len(r.role_draw_pile), 7)

    #when the wrong player tries to take a move
    # we expect an Error.
    def test_wrong_turn(self):
        with self.assertRaises(NotYourTurnError):
            players = [fake_player("Peter"), fake_player("Manan")]
            game = GameState(42, players[0], 2, deck_template='decks/default.csv')
            game.add_player(players[1])
            game.start_game()

            ref = Referee(game)

            with open("tests/moves.json") as f:
                move_sets = json.loads(f.read())

            moves = move_sets["wrong_turn"]
            for move in moves:
                ref.perform_move(move)

    def do_test_using_json_from_file(self, file, move_set):
        players = [fake_player("peter"), fake_player("manan")]

        test_deck = Building.create_deck_from_csv('decks/deck_test_30.csv')
        game = GameState()
        game.initialize_game(42, players, deck=test_deck)

        ref = Referee(r, game)

        with open(file) as f:
            move_sets = json.loads(f.read())

        moves = move_sets[move_set]
        for move in moves:
            ref.perform_move(move)

    def test_multiple_simple_ai_tests(self):
        total_rounds = 0
        test_method = self.do_ai_test_with_json
        #test_method = self.do_ai_test
        for a in range(20):
            #total_rounds += test_method(a, 2)
            total_rounds += test_method(a, 3)
            # total_rounds += test_method(a, 4)
            total_rounds += test_method(a, 5)
            # total_rounds += test_method(a, 6)
        logging.warning("total_rounds: %s" % total_rounds)

    def do_ai_test(self, seed, num_players):
        names = ['PeterAI', 'MananAI', 'AndyAI', 'MarkAI', 'KevinAI', 'RyanAI', 'TabithaAI']
        ais = {}
        players = []
        for n in names[0:num_players]:
            ais[n] = SimpleAIPlayer(n)
            players.append(Player(n))

        game = GameState(seed, players[0], num_players, deck_template='decks/deck_test_60.csv')
        for p in players[1:num_players]:
            game.add_player(p)
        game.start_game()
        ref = Referee(game)
        num_steps = 100 * len(players)

        for i in range(num_steps):
            logging.debug("On step %s of simulation" % i)
            cur_plyr = game.players[game.cur_player_index]
            logging.debug("Cur plyr index is %s" % game.cur_player_index)
            logging.debug("Cur plyr is %s" % cur_plyr)
            cur_ai = ais[cur_plyr.name]
            move = cur_ai.decide_what_to_do_native(game)
            ref.perform_move(move)
            #            logging.warning("Stage is %s" % game.stage)
            if game.stage == Stage.GAME_OVER:
                logging.warning("**********************************************")
                logging.warning("******* Success, game over and %s won   ******" % game.winner)
                for p in game.players:
                    logging.warning("Player %s had %s pts" % (p.name, p.points))
                return game.round_num
        logging.error("Didn't finish game in %s steps, ending test" % num_steps)
        self.assertTrue(False, "didn't finish game in right amount of steps")

    def do_ai_test_with_json(self, seed, num_players):
        names = ['PeterAI', 'MananAI', 'AndyAI', 'MarkAI', 'KevinAI', 'RyanAI', 'TabithaAI']
        ais = {}
        players = []
        for n in names[0:num_players]:
            ais[n] = SimpleAIPlayer(n)
            players.append(Player(n))

        game = GameState(seed, players[0], num_players, deck_template='decks/deck_test_60.csv')
        for p in players[1:num_players]:
            game.add_player(p)
        game.start_game()

        ref = Referee(game)

        json = ref.get_current_state_as_json_for_player(game.cur_player_index)
        parsed_json = from_json(json)
        json_game = parsed_json['game']

        game = None #force ourselves to use json from now on, and fail fast if
        #accidentally use game

        num_steps = 100 * len(players)

        logging.debug(json)

        for i in range(num_steps):
            logging.debug("On step %s of simulation" % i)
            cur_plyr = json_game['players'][json_game['cur_player_index']]
            cur_ai = ais[cur_plyr['name']]
            move = cur_ai.decide_what_to_do_json(parsed_json)
            json = ref.perform_move(move)
            parsed_json = from_json(json)
            json_game = parsed_json['game']
            stage = json_game['stage']
            if stage not in [Stage.GAME_OVER, Stage.END_GAME, Stage.PLAYING]:
                self.assertTrue(False, "stage is not valid: %s" % stage)
            logging.debug("stage is %s" % stage)
            if stage == Stage.GAME_OVER:
                logging.warning("**********************************************")
                logging.warning("******* Success, game over and %s won after %s rounds  ******" % (
                json_game['winner'], json_game['round_num']))
                json_players = json_game['players']
                for p in json_players:
                    logging.warning("Player %s had %s pts" % (p['name'], p['points']))
                return json_game['round_num']
        logging.error("Didn't finish game in %s steps, ending test" % num_steps)
        self.assertTrue(False, "didn't finish game in right amount of steps")


    def setUp(self):
        logging.info("\n--------- running %s -------------" % self.id())


def fake_player(n):
    return Player(str(n))


class RobotConfusedError(Exception):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #    unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(TestAllTheThings('test_multiple_simple_ai_tests'))
    unittest.TextTestRunner(verbosity=2).run(suite)