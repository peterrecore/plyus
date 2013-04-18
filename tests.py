from plyus import *
import unittest
import json
import random

class TestAllTheThings(unittest.TestCase):

    def testDraw(self):
        given = [1,2,3,4,5]

        result = draw_n(given,2)
        self.assertTrue((len(result) == 2))
        self.assertListEqual(result,[1,2])
        self.assertListEqual(given,[3,4,5])

    def testBuilding(self):
        foo = Building("blue",3,"NASA")
        self.assertTrue(foo.name == "NASA")


    def test_json(self):
        x = json.loads("[1,2,3]")
        self.assertTrue(len(x) == 3)

    def test_using_json_from_file(self):
        players = [fake_player(1), fake_player(2)]

        r = random.Random(42)
        game = GameState()
        game.initialize_game(r, players)

        ref = Referee(r, game)

        with open("moves.json") as f:
            moves = json.loads(f.read())

        for move in moves:
            player_index = move['player']
            player = players[player_index]
            action = move['action']

            ref.perform_action(player, action)

def fake_player(n):
    return Player("player " + str(n))
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()



