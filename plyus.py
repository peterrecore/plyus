import logging
from util import draw_n
from util import lowest_higher_than
from util import reverse_map
from util import ids


class Building(object):

    def __init__(self,i, c, p, n, cost=None):
        self.id = i
        self.color = c
        self.points = p
        self.name = n
        self.cost = cost
        if cost is None:
            self.cost = p 

    def __repr__(self):
        return "Building(id=%s, %s, %s, %s, %s)"% (self.id,self.name , self.color, self.points, self.cost)

    def __eq__(self, other):
        if type(self) is type(other):
            return self.id == other.id


def create_building_map():
    m = {}
    m.update([(b.id, b) for b in create_all_buildings()]) 
    return m

def create_all_buildings():
    r = [
     Building(1, "green", 1,"NYSE"),
     Building(2, "green",2,"Federal Reserve"),
     Building(3, "green",2,"Fort Knox"),
     Building(4, "red",1,"National Guard"),
     Building(5, "red",5,"Orbital Lasers"),
     Building(6, "yellow",3,"White House"),
     Building(7, "blue",2,"Boy Scout HQ"),
     Building(8, "blue",5,"Bhudda Statue"),
     Building(9, "purple",6,"Kennedy Space Center")
     ]
    return r

#TODO this global is a hack until we load decks from a database 
buildings = create_building_map() 

def building_for_id(id):
    return buildings[id]




class NotYourTurnError(Exception):
    def __init__(self, attempted_player, cur_player_index):
        self.attempted_player = attempted_player
        self.cur_player = cur_player_index

    def __repr__(self):
        return "NotYourTurnError(attempted_player=%s, cur_player=%s" % (self.attempted_player, self.cur_player)

class NoSuchActionError(Exception):
    def __init__(self, attempted_action):
        self.attempted_action = attempted_action

    def __repr__(self):
        return "NoSuchActionError(attempted_action=%s" % (self.attempted_action)


class FatalPlyusError(Exception):
    def __init__(self, explanation):
        self.explanation = explanation

#TODO: refactor errors so we can include an explanation in each
#TODO: refactor errors so they log themselves 

class IllegalActionError(Exception):
    def __init__(self, attempted_action=""):
        self.attempted_action = attempted_action





#Each Round consists of two phases
class Phase:
    PICK_CHARACTERS = 'PICK_CHARACTERS'
    PLAY_TURNS = 'PLAY_TURNS'

#The Play turn phase consists of several steps
class Step:
    COINS_OR_DISTRICT = 'COINS_OR_DISTRICT'
    KEEP_CARD = 'KEEP_CARD'
    USE_POWER = 'USE_POWER'
    BUILD_DISTRICT = 'BUILD_DISTRICT' 
    NONE = 'NO_STEP' 
    FINISH = 'FINISH'

class Round:
    def __init__(self, players,random_gen):
        self.players = players
        self.random_gen = random_gen
        self.plyr_to_char_map = {} #maps 
        self.char_to_plyr_map = {}
        self.has_used_power = {}

        for p in players:
            self.plyr_to_char_map[p.position] = False
            self.has_used_power[p.position] = False

        face_up_num, face_down_num = self.char_setup_for_n_players(len(players))
        self.character_draw_pile = [1,2,3,4,5,6,7,8]
        random_gen.shuffle(self.character_draw_pile)
        self.face_up_chars = draw_n(self.character_draw_pile, face_up_num)
        self.face_down_chars = draw_n(self.character_draw_pile, face_down_num)

    def mark_character_picked(self, character, player):
        self.plyr_to_char_map[player] = character
        self.char_to_plyr_map[character] = player
        self.character_draw_pile.remove(character)

    def char_setup_for_n_players(self, n):
        if n == 2: return (3,2)
        if n == 3: return (2,2)
        if n == 4: return (2,1)
        if n == 5: return (1,1)
        raise FatalPlyusError("Wrong number of players: %s" % n)
    
    def done_picking(self):
        #if no player still needs to choose, we're done picking
        return False not in self.plyr_to_char_map.values()

    def __repr__(self):
        return "Round(draw:%s, up:%s, down:%s\n    plyr_to_char:%s  char_to_plyr:%s" % (self.character_draw_pile,
            self.face_up_chars, self.face_down_chars, self.plyr_to_char_map, self.char_to_plyr_map)

class Referee:
    def __init__(self, rg, gs):
        self.game_state = gs
        self.random_gen = rg
        self.action_handlers = {
             'pick_character':self.handle_pick_character
            ,'take_gold':self.handle_take_gold
            ,'build_district':self.handle_build_district
            ,'draw_cards':self.handle_draw_cards
            ,'keep_card':self.handle_keep_card
            ,'finish':self.handle_finish
        }

    def check_for_victory(self, game_state):
        pass

    def perform_action(self, player, action):
        logging.info('game_state is %s' % self.game_state)
        logging.info('%s is attempting to take action: %s', player, action)
        # verify that this player is allowed to act right now
        if player.position != self.game_state.cur_player_index:
            e = NotYourTurnError(player.position, self.game_state.cur_player_index)
            logging.warn("about to raise not your turn: %r", e)
            raise e

        # verify that this action is legal
        if action["name"] not in self.action_handlers:
            raise NoSuchActionError(action["name"])

        # perform the action
        cur_player = self.game_state.players[self.game_state.cur_player_index]
        handler = self.action_handlers[action["name"]]
        handler(action,cur_player) 

        logging.info(" -- action handled.")
        # return the new state of the game

    def handle_finish(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.BUILD_DISTRICT, Step.FINISH)

        round = self.game_state.round
        cur_char = round.plyr_to_char_map[cur_player.position]
        logging.info("cur_player is %s, cur_char=%s" % (cur_player,cur_char))
        next_char = lowest_higher_than(round.char_to_plyr_map.keys(), cur_char)  

        #TODO:  do we really need last_char_to_play_this_round?
        logging.info("next_char is %s and last_char_to_play is %s" % (next_char, round.last_char_to_play_this_round))
        # if everyone has played, start a new round
        if (next_char is None):
            #everyone_has_played: start next round
            self.check_for_victory(self.game_state)
            self.game_state.start_new_round()

        else:
            #figure out who the next player is, based on the next character to play.
            #reset the step for that player.
            next_player = round.char_to_plyr_map[next_char]
            self.game_state.cur_player_index = next_player
            self.cur_player_index = round.char_to_plyr_map[next_char]
            self.game_state.step = Step.COINS_OR_DISTRICT


    def handle_take_gold(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)

        cur_player.take_gold()
        self.game_state.step = Step.BUILD_DISTRICT

    def handle_build_district(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.BUILD_DISTRICT)

        if 'target' not in action:
            logging.error("build action with no target")
            raise IllegalActionError()

        target_id = action['target']
        target = building_for_id(target_id)

        if target in cur_player.districts_on_table:
            logging.info("can't build 2 of same thing")
            raise IllegalActionError()

        if target not in cur_player.districtsInHand:
            logging.info("Can't build something not in your hand")
            raise IllegalActionError()

        # if the user didn't skip, then move the card from hand to table
        if target != "skip" :   
            cost = target.cost
            if cost > cur_player.gold :
                logging.info("not enough gold!")
                raise IllegalActionError()
 
            cur_player.districtsInHand.remove(target)
            cur_player.districts_on_table.append(target)
            cur_player.gold = cur_player.gold - cost

        self.game_state.step = Step.FINISH

    def handle_draw_cards(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)

        cur_player.take_cards(self.game_state.building_card_deck)
        self.game_state.step = Step.KEEP_CARD
        logging.info("possible cards are %s", cur_player.bufferHand)

    def handle_keep_card(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.KEEP_CARD)
        if 'target' not in action:
            logging.error("keep card action with no target")
            raise IllegalActionError()

        target_index = action['target']
        if target_index < 0 or target_index > len(cur_player.bufferHand): 
            logging.error("trying to keep card that wasn't drawn")
            raise IllegalActionError()

        target = cur_player.bufferHand[target_index]
        cur_player.districtsInHand.append(target)
        self.game_state.step = Step.BUILD_DISTRICT

    def handle_pick_character(self, action, cur_player):
        self.validate_phase_and_step(Phase.PICK_CHARACTERS, Step.NONE)

        if 'target' not in action:
            logging.error("pick char action with no target")
            raise IllegalActionError()

        target = action['target']

        if (target not in self.game_state.round.character_draw_pile):
            logging.error("pick char action with target not in draw pile")

        cur_player.character = target
        round = self.game_state.round
        round.mark_character_picked(target, cur_player.position)
        #if all players have picked a character
        if (self.game_state.round.done_picking()):
            # it's time to play turns, in character number order.
            # so figure out which character's turn it is, and set them
            # to be current player.
            current_character = lowest_higher_than(round.plyr_to_char_map.values(),0)
            self.game_state.cur_player_index = round.char_to_plyr_map[current_character]
            round.last_char_to_play_this_round = max(round.plyr_to_char_map.values())
            logging.info("Done Picking.  cur_char=%s, cur_plyr_pos=%s " % (current_character, self.game_state.cur_player_index))
            self.game_state.phase = Phase.PLAY_TURNS
            self.game_state.step = Step.COINS_OR_DISTRICT

        #otherwise move on to the next player
        else:
            self.game_state.advance_cur_player_index()


    def validate_phase_and_step(self, phase, *steps):
        if self.game_state.phase is not phase:
            raise IllegalActionError

        if self.game_state.step not in steps:
            raise IllegalActionError

    def validate_step(self, *steps):
        if self.game_state.step not in steps:
            raise IllegalActionError


def init_player(p, i, draw_pile):
        p.set_position(i) 
        p.districtsInHand.extend(draw_n(draw_pile, 2)) #TODO:  replace magic number with actual number of cards in starting hand.
#TODO: refactor so referee is the only one who knows about random_gen
#      make all gamestate methods more testable by injecting the randomly chosen
#      items rather than doing the random choosing internally
class GameState:

    def initialize_game(self, r, players):
        self.players = players
        self.random_gen = r
        self.building_card_deck = create_all_buildings()
        self.random_gen.shuffle(self.players)
        self.random_gen.shuffle(self.building_card_deck)

        self.num_players = len(self.players)

        [init_player(p, i, self.building_card_deck) for i,p in enumerate(players)]

        self.round_num = -1
        self.round = Round(players, self.random_gen)
        self.player_with_crown_token = 0 #this player gets to go first when picking a char

        self.start_new_round()


    def advance_cur_player_index(self):
        self.cur_player_index = (self.cur_player_index + 1) % self.num_players

    def __repr__(self):
        return ("phase=%s, step=%s, cur_player_index: %s, round=%s" % 
            (self.phase, self.step, self.cur_player_index, self.round))

    def start_new_round(self):
        self.round = Round(self.players, self.random_gen)
        self.cur_player_index = self.player_with_crown_token
        self.phase = Phase.PICK_CHARACTERS
        self.step = Step.NONE


class Player:
    def __init__(self, n):
        self.name = n

        self.gold = 2
        self.districts_on_table = []
        self.districtsInHand = []
        self.character = None

    #current player chooses to get gold
    def take_gold(self):
        self.gold += 2

    #when current player chooses to draw cards
    def take_cards(self, deck):
        self.bufferHand = draw_n(deck, 2)

    def set_position(self, i):
        self.position = i

    def __repr__(self):
        return "Player(name=%s, pos=%s, char= %s, gold=%s, hand=%r)" % (self.name, 
            self.position, self.character, self.gold, ids(self.districtsInHand))

# this is sort of a hack for now, to make it convenient to run tests
# right from sublime.
# TODO:  figure out how to run tests easy without this here
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    import unittest
    unittest.main(module='tests')