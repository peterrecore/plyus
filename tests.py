import unittest
import json
import random
import logging
import collections
from util import *
from plyus import *

class TestAllTheThings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.WARNING) 

    def test_create_deck_from_file(self):
        deck = Building.create_deck_from_csv('decks/deck_test_30.csv') 
        self.assertEqual(len(deck), 30)
        self.assertEqual(deck[2], Building(3,"green",2,"Fort Knox"))
        self.assertEqual(deck[2].color, "green")

    def test_draw(self):
        given = [1,2,3,4,5]
        result = draw_n(given,2)
        self.assertTrue((len(result) == 2))
        self.assertListEqual(result,[1,2])
        self.assertListEqual(given,[3,4,5])

    def test_building(self):
        foo = Building(1,"blue",3,"NASA")
        self.assertTrue(foo.name == "NASA")

    def test_valid_moves(self):
        self.do_test_using_json_from_file("moves.json","valid_moves")


    def test_create_round(self):
        random_generator = random.Random(42)
        players = [fake_player("Peter"),fake_player("Manan")]
        [p.set_position(i) for i,p in enumerate(players)]
        r = Round(players, random_generator)

        self.assertEqual(len(r.face_up_chars), 3)
        self.assertEqual(len(r.face_down_chars), 2)
        self.assertEqual(len(r.character_draw_pile),3)

    #when the wrong player tries to take a move
    # we expect an Error.
    def test_wrong_turn(self):
        with self.assertRaises(NotYourTurnError):
            players = [fake_player("peter"), fake_player("manan")]

            r = random.Random(42)
            game = GameState()
            deck = create_def_deck()
            game.initialize_game(r, players,deck)

            ref = Referee(r, game)

            with open("moves.json") as f:
                move_sets = json.loads(f.read())

            moves = move_sets["wrong_turn"]
            for move in moves:
                ref.perform_move(move)

    def do_test_using_json_from_file(self, file, move_set):
        players = [fake_player("peter"), fake_player("manan")]

        test_deck = Building.create_deck_from_csv('decks/deck_test_30.csv')
        r = random.Random(42)
        game = GameState()
        game.initialize_game(r, players, deck=test_deck)

        ref = Referee(r, game)

        with open(file) as f:
            move_sets = json.loads(f.read())

        moves = move_sets[move_set]
        for move in moves:
            ref.perform_move(move)

    def test_multiple_simple_ai_tests(self):
        r = random.Random(42)
        counter = collections.Counter()
        for a in range(10):
            self.do_simple_ai_test(r, 2)
            self.do_simple_ai_test(r, 3)
            self.do_simple_ai_test(r, 4)
        logging.warning("counts: %s" % counter)

    def do_simple_ai_test(self, r, num_players):
        names = ['PeterAI', 'MananAI','AndyAI','MarkAI'] 
        ais = {}
        players = []
        for n in names[0:num_players]:
           ais[n] = SimpleAIPlayer(n)
           players.append(Player(n))


        test_deck = Building.create_deck_from_csv('decks/deck_test_60.csv')
        game = GameState()
        game.initialize_game(r,players, deck=test_deck)
        ref = Referee(r,game)
        num_steps = 100 * len(players)

        for i in range(num_steps):
            logging.debug("On step %s of simulation" % i)
            cur_plyr = game.players[game.cur_player_index]
            cur_ai = ais[cur_plyr.name]
            move = cur_ai.decide_what_to_do(game)
            ref.perform_move(move)
            if ref.check_for_victory(game) :
               logging.warning("**********************************************")
               logging.warning("******* Success, game over and %s won   ******" % game.winner) 
               for p in game.players:
                 logging.warning("Player %s had %s pts" % (p.name, p.points))
               return game.winner
        logging.error("Didn't finish game in %s steps, ending test" % num_steps)
        self.assertTrue(False) 

    def setUp(self):
        logging.info("\n--------- running %s -------------" % self.id())

def fake_player(n):
    return Player(str(n))

class RobotConfusedError(Exception):
    pass
        
class SimpleAIPlayer():
    def __init__(self, name):
        self.name = name

    def decide_what_to_do(self, game):
        me = game.players[game.cur_player_index]
        a = None
        if game.phase == Phase.PICK_CHARACTERS:
            target = game.round.character_draw_pile[0]
            a = {"name":"pick_character", "target":target}

        if game.step == Step.COINS_OR_DISTRICT:
            if len(me.districts_in_hand) > 0:
                a = {"name":"take_gold"}
            else:
                a = {"name":"draw_cards"}

        if game.step == Step.KEEP_CARD:
            a = {"name":"keep_card", "target":0}

        if game.step == Step.BUILD_DISTRICT:
            dists = me.districts_in_hand
            if len(dists) >= 1:
                cost = dists[0].cost
                if me.gold >= cost:
                    t = dists[0].id
                    a = {"name":"build_district", "target":t}
                else:
                    a = {"name":"build_district", "target":"skip"} 
            else:
                a = {"name":"build_district","target": "skip"}

        if game.step == Step.FINISH:
            a = {"name":"finish"}

        if a is None:
            msg = "AI doesn't know what to do.  Step is %s " % game.step
            logging.warning(msg)
            raise RobotConfusedError(msg)
        d = {"player" : me.position , "action":a} 
        return d

def create_def_deck():
    return Building.create_deck_from_csv('decks/default.csv') 


if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO)
    unittest.main()
