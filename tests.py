import unittest
import json
import random
import logging
from util import *
from plyus import *

class TestAllTheThings(unittest.TestCase):

    def testDraw(self):
        given = [1,2,3,4,5]
        result = draw_n(given,2)
        self.assertTrue((len(result) == 2))
        self.assertListEqual(result,[1,2])
        self.assertListEqual(given,[3,4,5])

    def testBuilding(self):
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

    @unittest.skip("not right now")
    def test_wrong_turn(self):
        with self.assertRaises(NotYourTurnError):
            self.do_test_using_json_from_file("moves.json","wrong_turn")

    def do_test_using_json_from_file(self, file, move_set):
        players = [fake_player("peter"), fake_player("manan")]

        r = random.Random(42)
        game = GameState()
        game.initialize_game(r, players)

        ref = Referee(r, game)

        with open(file) as f:
            move_sets = json.loads(f.read())

        moves = move_sets[move_set]
        for move in moves:
            player_index = move['player']
            player = players[player_index]
            action = move['action']

            ref.perform_action(player, action)
    def setUp(self):
        logging.info("\n--------- running %s -------------" % self.id())
def fake_player(n):
    return Player(str(n))
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
