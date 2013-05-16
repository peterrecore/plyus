import logging
import csv
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

    @staticmethod 
    def create_deck_from_csv(filename):

        def card_from_line(line):
            return Building(int(line[0]), line[1], int(line[2]), line[3])

        with open(filename, 'r') as myfile:
            lines = csv.reader(myfile)
            return [card_from_line(line) for line in lines]


def create_building_map(buildings):
    m = {}
    m.update([(b.id, b) for b in buildings]) 
    return m

class NotYourTurnError(Exception):
    def __init__(self, attempted_player, cur_player_index):
        self.attempted_player = attempted_player
        self.cur_player = cur_player_index

    def __repr__(self):
        return ("NotYourTurnError(attempted_player=%s, cur_player=%s" 
            % (self.attempted_player, self.cur_player))

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
    def __repr__(self):
        return "IllegalActionError(attempted_action=%s)" % (self.attempted_action)





#Each Round consists of two phases
class Phase:
    PICK_CHARACTERS = 'PICK_CHARACTERS'
    PLAY_TURNS = 'PLAY_TURNS'

#The Play turn phase consists of several steps
class Step:
    COINS_OR_DISTRICT = 'COINS_OR_DISTRICT'
    KEEP_CARD = 'KEEP_CARD'
#    MURDER = 'MURDER'
#    STEAL = 'STEAL'
#    RAZE = 'RAZE'
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
            ,'use_power':self.handle_use_power
        }
        self.power_handlers = {
             1:self.handle_power_1
            ,2:self.handle_power_2
            ,3:self.handle_power_3
            ,4:self.handle_power_4
            ,5:self.handle_power_5
            ,6:self.handle_power_6
            ,7:self.handle_power_7
            ,8:self.handle_power_8
        }
    def check_for_victory(self, game_state):
        #when soeone has built 8 things, game is over
        if self.game_state.end_game:
            rankings = []
            for p in self.game_state.players:

                basic_points = 0
                bonus_points = 0
                colors = {}
                for d in p.districts_on_table:
                    basic_points += d.points
                    colors[d.color] = True

                if len(colors.keys()) == 5:
                    p.rainbow_bonus = True
                    bonus_points += 3


                if len(p.districts_on_table) >= 8:
                    bonus_points += 2

                if p.first_to_eight_districts:
                    bonus_points += 2

                p.points = basic_points + bonus_points
                p.ranking = (p.points, p.gold, basic_points)
            #TODO:  implement official tiebreaker                        
            ranked_players = sorted(self.game_state.players, key=lambda p:p.ranking, reverse=True )
            self.game_state.winner = ranked_players[0].name

            return True
        return False 

    #TODO: validate that move is a valid move object.  possibly 
    # make an actual Move class that ensures validity
    def perform_move(self, move):
        logging.debug('game_state is %s' % self.game_state)

        player_index = move['player']
        player = self.game_state.players[player_index]
        action = move['action']

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

        #building an 8th district triggers the end of the game
        if len(cur_player.districts_on_table) >= 8:
            #if no one else has trigged the end yet, this player is first
            #to get 8 districts, and gets a bonus
            if not self.game_state.end_game:
                cur_player.first_to_eight_districts = True
            self.game_state.end_game = True

        logging.debug(" -- action handled.")
        # return the new state of the game
        return self.game_state


    def handle_use_power(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS,
                                     Step.BUILD_DISTRICT,
                                     Step.FINISH,
                                     Step.COINS_OR_DISTRICT)

        round = self.game_state.round
        if round.has_used_power[cur_player.position]:
            raise IllegalActionError("Already Used Power")

        handler = self.power_handlers[cur_player.character]
        handler(action, cur_player)
        round.has_used_power[cur_player.position] = True

    def handle_finish(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.BUILD_DISTRICT, Step.FINISH)

        round = self.game_state.round
        cur_char = round.plyr_to_char_map[cur_player.position]
        logging.info("cur_player is %s, cur_char=%s" % (cur_player,cur_char))
        next_char = lowest_higher_than(round.char_to_plyr_map.keys(), cur_char)  

        #TODO:  do we really need last_char_to_play_this_round?
        logging.info("next_char is %s and last_char_to_play is %s" 
            % (next_char, round.last_char_to_play_this_round))
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

        if target_id != 'skip':
            target = self.game_state.buildings[target_id]

            if target in cur_player.districts_on_table:
                logging.info("can't build 2 of same thing")
                raise IllegalActionError()

            if target not in cur_player.districts_in_hand:
                logging.info("Can't build something not in your hand")
                raise IllegalActionError()

            cost = target.cost
            if cost > cur_player.gold :
                logging.info("not enough gold!")
                raise IllegalActionError()
 
            cur_player.districts_in_hand.remove(target)
            cur_player.districts_on_table.append(target)
            cur_player.gold = cur_player.gold - cost


        self.game_state.step = Step.FINISH

    def handle_draw_cards(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)

        cur_player.take_cards(self.game_state.building_card_deck)
        self.game_state.step = Step.KEEP_CARD
        logging.info("possible cards are %s", cur_player.districts_buffer)

    #TODO: target should be an ID, not an index to keep consistent
    # with rest of actions
    def handle_keep_card(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.KEEP_CARD)
        if 'target' not in action:
            logging.error("keep card action with no target")
            raise IllegalActionError()

        target_index = action['target']
        if target_index < 0 or target_index > len(cur_player.districts_buffer): 
            logging.error("trying to keep card that wasn't drawn")
            raise IllegalActionError()

        target = cur_player.districts_buffer[target_index]
        cur_player.districts_in_hand.append(target)
        cur_player.districts_buffer.remove(target)
        self.game_state.building_card_deck.extend(cur_player.districts_buffer)
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
            logging.info("Done Picking.  cur_char=%s, cur_plyr_pos=%s " 
                % (current_character, self.game_state.cur_player_index))
            self.game_state.phase = Phase.PLAY_TURNS
            self.game_state.step = Step.COINS_OR_DISTRICT

        #otherwise move on to the next player
        else:
            self.game_state.advance_cur_player_index()


    def dispense_bonus_gold(self, color, cur_plyr):
        num_color = sum(1 for d in cur_plyr.districts_on_table if d.color == color)
        cur_plyr.gold += num_color
        logging("Player %s gained %s bonus gold" % (cur_plyr.name, num_color))

    def handle_power_1(self, action, cur_plyr):
        pass

    def handle_power_2(self, action, cur_plyr):
        pass

    def handle_power_3(self, action, cur_plyr):
        pass

    def handle_power_4(self, action, cur_plyr):
        dispense_bonus_gold("yellow", cur_plyr)

    def handle_power_5(self, action, cur_plyr):
        dispense_bonus_gold("blue", cur_plyr)

    def handle_power_6(self, action, cur_plyr):
        dispense_bonus_gold("green", cur_plyr)

    def handle_power_7(self, action, cur_plyr):
        pass

    def handle_power_8(self, action, cur_plyr):
        dispense_bonus_gold("red", cur_plyr)

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
        #TODO:  replace magic number with actual number of cards in starting hand.
        p.districts_in_hand.extend(draw_n(draw_pile, 2)) 



#TODO: refactor so referee is the only one who knows about random_gen
#      make all gamestate methods more testable by injecting the randomly chosen
#      items rather than doing the random choosing internally
class GameState:

    def initialize_game(self, r, players, deck):
        self.end_game = False
        self.players = players
        self.random_gen = r
        self.building_card_deck = deck
        self.buildings = create_building_map(self.building_card_deck) 
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

#TODO:  make sure we can't have 2 players with the same name.  or else
# make sure we handle that case properly
class Player:
    def __init__(self, n):
        self.name = n

        self.gold = 2
        self.districts_on_table = []
        self.districts_in_hand = []
        self.character = None
        self.rainbow_bonus = False
        self.first_to_eight_districts = False

    #current player chooses to get gold
    def take_gold(self):
        self.gold += 2

    #when current player chooses to draw cards
    def take_cards(self, deck):
        if len(deck) < 2:
            #TODO: figure out and implement rule on reshuffling district cards 
            raise FatalPlyusError("District deck is out of cards.")
        self.districts_buffer = draw_n(deck, 2)

    def set_position(self, i):
        self.position = i

    def __repr__(self):
        return "Player(name=%s, pos=%s, char= %s, gold=%s, hand=%r, dists=%s)" % (self.name, 
            self.position, self.character, self.gold, ids(self.districts_in_hand),len(self.districts_on_table))

# this is sort of a hack for now, to make it convenient to run tests
# right from sublime.
# TODO:  figure out how to run tests easy without this here
if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    import unittest
    unittest.main(module='tests')