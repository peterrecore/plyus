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
        #counter = collections.Counter()
        total_rounds = 0
        for a in range(100):
            total_rounds += self.do_simple_ai_test(r, 2)
            total_rounds += self.do_simple_ai_test(r, 3)
            total_rounds += self.do_simple_ai_test(r, 4)
        logging.warning("total_rounds: %s" % total_rounds)

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
            if game.check_for_victory() :
               logging.warning("**********************************************")
               logging.warning("******* Success, game over and %s won   ******" % game.winner) 
               for p in game.players:
                 logging.warning("Player %s had %s pts" % (p.name, p.points))
               return game.round_num
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

        self.ponder_map = {
            Step.COINS_OR_DISTRICT:self.ponder_coins_or_district
            ,Step.BUILD_DISTRICT:self.ponder_build_district
            ,Step.FINISH:self.ponder_finish
            ,Step.KEEP_CARD:self.ponder_keep_card
        }

    def ponder_coins_or_district(self, game, me):
        if (not game.round.has_taken_bonus[me.position] and
            me.character in [4,5,6,8]):
            return {"name":"take_bonus"}

        if len(me.districts_in_hand) > 0:
            return {"name":"take_gold"}

        return  {"name":"draw_cards"}

    def ponder_keep_card(self, game, me):
        return {"name":"keep_card", "target":0}

    def ponder_build_district(self, game, me):
        dists = me.districts_in_hand
        if len(dists) >= 1:
            cost = dists[0].cost
            if me.gold >= cost:
                t = dists[0].id
                return {"name":"build_district", "target":t}

        return {"name":"build_district","target": "skip"}


    def ponder_finish(self, game, me):
        if not game.round.has_used_power[me.position]:
            if me.character in [1,2] :
                return {"name":"use_power","target":self.likely_victim}

            if me.character == 3:
                discard = []
                if len(me.districts_in_hand) >= 1:
                    discard.append(me.districts_in_hand[0].id)
                    return {"name":"use_power","target":"deck", "discards":discard}
                #if we have no cards, arbitrarily shaft the player after us.
                victim_pos = (me.position + 1) % game.num_players
                return {"name":"use_power", "target":victim_pos}

            if me.character == 8:
                victim = game.players[(me.position + 1) % game.num_players]
                logging.warning("victim is %s" % victim)
                potential_target = None
                if len(victim.districts_on_table) > 0:
                    potential_target = sorted(victim.districts_on_table, key=lambda d:d.cost)[0]
                if (potential_target and
                   potential_target.cost <= me.gold and
                   victim.character != 5):
                    return {"name":"use_power","target_player_id":victim.position, "target_card_id":potential_target.id}
        return {"name":"finish"}

    def ponder_pick_character(self, game, me):
        my_char = game.round.character_draw_pile[0]

        #this method of choosing a good victim will be absoultely wrong
        #whenever we are the last player to pick.  But no one
        #said that SimpleAI was supposed to be smart. 
        self.likely_victim = game.round.character_draw_pile[1]

        # can't target #1 as #2, so 7 will get the arbitrary shafting.
        if my_char == 2 and self.likely_victim == 1:
            self.likely_victim = 7

        return {"name":"pick_character", "target":my_char}



    def decide_what_to_do(self, game):
        me = game.players[game.cur_player_index]
        a = None

        if game.phase == Phase.PICK_CHARACTERS:
            a = self.ponder_pick_character(game, me)

        if game.step in self.ponder_map:
            ponderer = self.ponder_map[game.step]
            a = ponderer(game, me)

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
