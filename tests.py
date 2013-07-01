import unittest
import json
import random
import logging
import collections
from util import *
from plyus import *


class Object(object):
    def __init__(self, d):
        self.__dict__ = d

class TestAllTheThings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.WARNING) 
        logging.warning("Warning level set.")

    def test_create_deck_from_file(self):
        deck = BuildingDeck('decks/deck_test_30.csv')
        self.assertEqual(len(deck.cards), 30)
        self.assertEqual(deck.full_cards[2], Building(3,"green",2,"Fort Knox"))
        self.assertEqual(deck.card_for_id(3), Building(3,"green",2,"Fort Knox"))
        self.assertEqual(deck.card_for_id(3).color, "green")



    def test_draw(self):
        given = [1,2,3,4,5]
        result = draw_n(given,2)
        self.assertEqual(len(result), 2)
        self.assertListEqual(result,[1,2])
        self.assertListEqual(given,[3,4,5])

    def test_building(self):
        foo = Building(1,"blue",3,"NASA")
        self.assertTrue(foo.name == "NASA")

    @unittest.skip("skipping until we rewrite to not make it so fragile.")
    def test_valid_moves(self):
        self.do_test_using_json_from_file("moves.json","valid_moves")


    def test_create_round(self):
        random_generator = random.Random(42)
        players = [fake_player("Peter"),fake_player("Manan")]
        [p.set_position(i) for i,p in enumerate(players)]
        r = Round(players, random_generator)

        self.assertEqual(len(r.face_up_roles), 0)
        self.assertEqual(len(r.face_down_roles), 1)
        self.assertEqual(len(r.role_draw_pile),7)

    #when the wrong player tries to take a move
    # we expect an Error.
    def test_wrong_turn(self):
        with self.assertRaises(NotYourTurnError):
            players = [fake_player("peter"), fake_player("manan")]

            r = random.Random(42)
            game = GameState()
            game.initialize_game(r, players,'decks/default.csv')

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
        test_method = self.do_ai_test_with_json
        #test_method = self.do_ai_test
        for a in range(3):
            total_rounds += test_method(r, 2)
            total_rounds += test_method(r, 3)
            total_rounds += test_method(r, 4)
            total_rounds += test_method(r, 5)
            total_rounds += test_method(r, 6)
        logging.warning("total_rounds: %s" % total_rounds)

    def do_ai_test(self, r, num_players):
        names = ['PeterAI', 'MananAI','AndyAI','MarkAI','KevinAI','RyanAI','TabithaAI'] 
        ais = {}
        players = []
        for n in names[0:num_players]:
           ais[n] = SimpleAIPlayer(n)
           players.append(Player(n))


        test_deck = Building.create_deck_from_csv()
        game = GameState()
        game.initialize_game(r,players, deck_template='decks/deck_test_60.csv')
        ref = Referee(r,game)
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
            if game.stage == Stage.GAME_OVER :
               logging.warning("**********************************************")
               logging.warning("******* Success, game over and %s won   ******" % game.winner) 
               for p in game.players:
                 logging.warning("Player %s had %s pts" % (p.name, p.points))
               return game.round_num
        logging.error("Didn't finish game in %s steps, ending test" % num_steps)
        self.assertTrue(False, "didn't finish game in right amount of steps") 

    def do_ai_test_with_json(self, r, num_players):
        names = ['PeterAI', 'MananAI','AndyAI','MarkAI','KevinAI','RyanAI','TabithaAI'] 
        ais = {}
        players = []
        for n in names[0:num_players]:
           ais[n] = SimpleAIPlayer(n)
           players.append(Player(n))


        game = GameState()
        game.initialize_game(r,players, deck_template='decks/deck_test_60.csv')
        ref = Referee(r,game)

        json = ref.get_current_state_as_json_for_player(game.cur_player_index)
        parsed_json = util.from_json(json) 
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
            parsed_json = util.from_json(json)
            json_game = parsed_json['game']
            stage = json_game['stage']
            if stage not in [Stage.GAME_OVER, Stage.END_GAME, Stage.PLAYING]:
                self.assertTrue(False, "stage is not valid: %s" % stage)
            logging.debug("stage is %s" % stage)
            if stage == Stage.GAME_OVER :
               logging.warning("**********************************************")
               logging.warning("******* Success, game over and %s won after %s rounds  ******" % (json_game['winner'],json_game['round_num'])) 
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
        
class SimpleAIPlayer():
    def __init__(self, name):
        self.name = name

        self.ponder_map = {
            Step.COINS_OR_BUILDING:self.ponder_coins_or_building
            ,Step.BUILD_BUILDING:self.ponder_build_building
            ,Step.FINISH:self.ponder_finish
            ,Step.KEEP_CARD:self.ponder_keep_card
            ,Step.HIDE_ROLE:self.ponder_hide_role
            ,Step.PICK_ROLE:self.ponder_pick_role
        }

    def ponder_coins_or_building(self, game, me):
        if (not game.round.has_taken_bonus[me.position] and
            me.cur_role in [4,5,6,8]):
            return {"name":"take_bonus"}

        if len(me.buildings_in_hand) > 0:
            return {"name":"take_gold"}

        return  {"name":"draw_cards"}

    def ponder_keep_card(self, game, me):
        return {"name":"keep_card", "target":0}

    def ponder_build_building(self, game, me):
        dists = me.buildings_in_hand
        if len(dists) >= 1:
            cost = dists[0].cost
            if me.gold >= cost:
                t = dists[0].id
                return {"name":"build_building", "target":t}

        return {"name":"build_building","target": "skip"}


    def ponder_finish(self, game, me):
        if game.round.has_used_power[me.position]:
            return {"name":"finish"}

        if me.cur_role in [1,2] :
            if self.likely_victim == 1:
               self.likely_victim = 7
            return {"name":"use_power","target":self.likely_victim}

        if me.cur_role == 3:
            discard = []
            if len(me.buildings_in_hand) >= 1:
                discard.append(me.buildings_in_hand[0].id)
                return {"name":"use_power","target":"deck", "discards":discard}
            #if we have no cards, arbitrarily shaft the player after us.
            victim_pos = (me.position + 1) % game.num_players
            return {"name":"use_power", "target":victim_pos}

        if me.cur_role == 8:
            victim = game.players[(me.position + 1) % game.num_players]
            logging.debug("razing victim is %s" % victim)
            potential_target = None
            if 0 < len(victim.buildings_on_table) < 8:
                potential_target = sorted(victim.buildings_on_table, key=lambda d:d.cost)[0]
            if (potential_target and
               potential_target.cost <= me.gold and
               5 not in victim.revealed_roles):
                return {"name":"use_power","target_player_id":victim.position, "target_card_id":potential_target.id}

        return {"name":"finish"}

    def ponder_hide_role(self, game, me):
        hide_role = game.round.role_draw_pile[0]
        return {"name":"hide_role", "target":hide_role}

    def ponder_pick_role(self, game, me):
        #pick the first role we see
        my_role = game.round.role_draw_pile[0]

        #this method of choosing a good victim will be absoultely wrong
        #whenever we are the last player to pick.  But no one
        #said that SimpleAI was supposed to be smart. 
        self.likely_victim = game.round.role_draw_pile[1]

        return {"name":"pick_role", "target":my_role}


    def decide_what_to_do_json(self, some_json):
        def convert_to_int_keys(d):
            for k,v in d.items():
                d[int(k)] = v
                del d[k]


        d = some_json['game']
        game = Object(d)

        r = Object(game.round)
        game.round = r

        #conversion here is needed because json turned the integer keys into
        #strings, but we still want ints
        convert_to_int_keys(r.has_taken_bonus)
        convert_to_int_keys(r.has_used_power)

        for p in game.players:
            logging.debug("p is ### %s ###" % p)
            game.players[p['position']] = Object(p)

        d = some_json['me']
        me = Object(d)
        return self.decide_what_to_do(game, me)

    def decide_what_to_do_native(self, game):
        me = game.players[game.cur_player_index]
        return self.decide_what_to_do(game, me)

    def decide_what_to_do(self, game, me):
        a = None


        if game.step in self.ponder_map:
            ponderer = self.ponder_map[game.step]
            a = ponderer(game, me)

        if a is None:
            msg = "AI doesn't know what to do.  Step is %s " % game.step
            logging.warning(msg)
            raise RobotConfusedError(msg)

        d = {"player" : me.position , "action":a} 
        return d


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
#    unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(TestAllTheThings('test_multiple_simple_ai_tests'))
    unittest.TextTestRunner(verbosity=2).run(suite)