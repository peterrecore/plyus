import logging
import csv
import util 
from util import lowest_higher_than
from util import reverse_map
from util import ids
from collections import defaultdict

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
    MURDER = 'MURDER'
    STEAL = 'STEAL'
    RAZE = 'RAZE'
    BUILD_DISTRICT = 'BUILD_DISTRICT' 
    PICK_CHAR = 'PICK_CHAR' 
    HIDE_CHAR = 'HIDE_CHAR' 
    FINISH = 'FINISH'

class Round:
    def __init__(self, players,random_gen):
        self.players = players
        self.random_gen = random_gen

        self.plyr_to_char_map = defaultdict(list) 
        self.char_to_plyr_map = {}
        self.has_used_power = {}
        self.has_taken_bonus = {}
        self.num_seven_builds_left = 3
        self.dead_char = None
        self.mugged_char = None


        for p in players:
            #TODO: cleanup before committing for 2/3 player mode
            #self.plyr_to_char_map[p.position] = False no need to init now that this is a defaultdict
            self.has_used_power[p.position] = False
            self.has_taken_bonus[p.position] = False
            p.chars = []
            p.cur_char = None

        face_up_num, face_down_num = self.char_setup_for_n_players(len(players))
        self.character_draw_pile = [1,2,3,4,5,6,7,8]
        random_gen.shuffle(self.character_draw_pile)
        self.face_up_chars = util.draw_n(self.character_draw_pile, face_up_num)
        self.face_down_chars = util.draw_n(self.character_draw_pile, face_down_num)

    def mark_character_picked(self, character, player):
        self.plyr_to_char_map[player].append(character)
        self.char_to_plyr_map[character] = player
        self.character_draw_pile.remove(character)

    def char_setup_for_n_players(self, n):
        # return (num_face_up, num_face_down)
        if n == 2: return (0,1)
        if n == 3: return (0,1)
        if n == 4: return (2,1)
        if n == 5: return (1,1)
        if n == 6: return (0,1)
        raise FatalPlyusError("Wrong number of players: %s" % n)
    
    def done_picking(self):
        #if no player still needs to choose, we're done picking
        # easy case - if everyone has picked one char we're done

        chars_picked = util.flatten(self.plyr_to_char_map.values())
        num_chars_picked = len(chars_picked)
        num_players = len(self.players)

        num_chars_per_player = 1

        if num_players <= 3:
            num_chars_per_player = 2

        return num_chars_picked >= num_players * num_chars_per_player

    def __repr__(self):
        return "Round(draw:%s, up:%s, down:%s\n    plyr_to_char:%s  char_to_plyr:%s" % (self.character_draw_pile,
            self.face_up_chars, self.face_down_chars, self.plyr_to_char_map, self.char_to_plyr_map)

class Referee:
    def __init__(self, rg, gs):
        self.game_state = gs
        self.random_gen = rg
        self.action_handlers = {
             'pick_character':self.handle_pick_character
            ,'hide_character':self.handle_hide_character
            ,'take_gold':self.handle_take_gold
            ,'build_district':self.handle_build_district
            ,'draw_cards':self.handle_draw_cards
            ,'keep_card':self.handle_keep_card
            ,'finish':self.handle_finish
            ,'use_power':self.handle_use_power
            ,'take_bonus':self.handle_take_bonus
        }
        self.power_handlers = {
             1:self.handle_power_1
            ,2:self.handle_power_2
            ,3:self.handle_power_3
            ,8:self.handle_power_8
        }


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

        handler = self.power_handlers[cur_player.cur_char]
        handler(action, cur_player)
        round.has_used_power[cur_player.position] = True

    def handle_finish(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.BUILD_DISTRICT, Step.FINISH)

        round = self.game_state.round
    #TODO:  cleanup as part of 2/3 change
    #   cur_char = round.plyr_to_char_map[cur_player.position]
        cur_char = cur_player.cur_char

        logging.info("cur_player is %s, cur_char=%s" % (cur_player,cur_char))
        next_char = lowest_higher_than(round.char_to_plyr_map.keys(), cur_char)  
        if next_char == round.dead_char:
            next_char = lowest_higher_than(round.char_to_plyr_map.keys(), cur_char+1)  

        logging.info("next_char is %s  " % next_char)
        # if everyone has played, start a new round
        if (next_char is None):
            #everyone_has_played: start next round
            self.game_state.finish_round()
            self.game_state.start_new_round()

        else:
            #figure out who the next player is, based on the next cur_char to play.
            #reset the step for that player.
            next_player = round.char_to_plyr_map[next_char]
            self.game_state.cur_player_index = next_player
            self.cur_player_index = round.char_to_plyr_map[next_char]
            self.game_state.players[next_player].cur_char = next_char
            self.game_state.step = Step.COINS_OR_DISTRICT

    #some things happen before a player "takes an action"
    # which means after they draw cards or take gold
    # we will consider this equivalent to the "start of the turn"
    def pre_action_effects(self, cur_player):
        rnd = self.game_state.round
        if cur_player.cur_char == rnd.mugged_char:
           stolen = cur_player.gold 
           cur_player.gold = 0
           mugger = rnd.char_to_plyr_map[2]
           rnd.players[mugger].gold += stolen
           #TODO: announce gold was stolen

    #some things happen after a player "takes an action"
    # which means after they draw cards or take gold
    def post_action_effects(self, cur_player):
        if cur_player.cur_char == 6:
            cur_player.gold += 1
            #TODO:  merchant getting a bonus gold needs to be an announced event
        if cur_player.cur_char == 7:
            cards = util.draw_n(self.game_state.building_card_deck, 2)
            cur_player.districts_in_hand.extend(cards)
            #TODO: announce player getting bonus cards

    def handle_take_gold(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)
        self.pre_action_effects(cur_player)
        cur_player.take_gold()
        self.post_action_effects(cur_player)
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

        #unless current char is 7, we only get one build so next step is finish
        r = self.game_state.round
        r.num_seven_builds_left -= 1
        if (cur_player.cur_char == 7 and r.num_seven_builds_left > 0):
            self.game_state.step = Step.BUILD_DISTRICT
        else:
            self.game_state.step = Step.FINISH

    def handle_draw_cards(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)

        self.pre_action_effects(cur_player)
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
        self.post_action_effects(cur_player)
        self.game_state.step = Step.BUILD_DISTRICT



    def handle_hide_character(self, action, cur_player):
        self.validate_phase_and_step(Phase.PICK_CHARACTERS, Step.HIDE_CHAR)

        if 'target' not in action:
            logging.error("hide char action with no target")
            raise IllegalActionError()

        target = action['target']

        if (target not in self.game_state.round.character_draw_pile):
            logging.error("hide char action with target not in draw pile")

        round = self.game_state.round
        round.character_draw_pile.remove(target)
        round.face_down_chars.append(target)

        self.game_state.advance_cur_player_index()
        self.game_state.step = Step.PICK_CHAR

    def handle_pick_character(self, action, cur_player):
        self.validate_phase_and_step(Phase.PICK_CHARACTERS, Step.PICK_CHAR)

        if 'target' not in action:
            logging.error("pick char action with no target")
            raise IllegalActionError()

        target = action['target']

        if (target not in self.game_state.round.character_draw_pile):
            logging.error("pick char action with target not in draw pile")

        round = self.game_state.round

        cur_player.chars.append(target)
        round.mark_character_picked(target, cur_player.position)

        # handle 2 player special case
        # players must place a char card face down after their middle picks
        # to maintain uncertainty
        num_chars_picked_so_far = len(round.char_to_plyr_map)
        if (self.game_state.num_players == 2 and num_chars_picked_so_far in [2,3]):
            self.game_state.step = Step.HIDE_CHAR
            return

        #if all players have picked a character
        if (self.game_state.round.done_picking()):
            # it's time to play turns, in character number order.
            # so figure out which character's turn it is, and set them
            # to be current player.

            chars_in_play = util.flatten(round.plyr_to_char_map.values())

            current_character = lowest_higher_than(chars_in_play,0)
            cur_plyr_index =  round.char_to_plyr_map[current_character]
            self.game_state.cur_player_index = cur_plyr_index

            self.game_state.players[cur_plyr_index].cur_char = current_character

            logging.info("Done Picking.  cur_char=%s, chars= %s, cur_plyr_pos=%s " 
                % (current_character, cur_player.chars, self.game_state.cur_player_index))
            self.game_state.phase = Phase.PLAY_TURNS
            self.game_state.step = Step.COINS_OR_DISTRICT

        #otherwise move on to the next player
        else:
            self.game_state.advance_cur_player_index()


    def handle_take_bonus(self, action, cur_plyr):
        self.validate_phase_and_step(Phase.PLAY_TURNS,
                             Step.BUILD_DISTRICT,
                             Step.FINISH,
                             Step.COINS_OR_DISTRICT)
        color_map = {4:"yellow", 5:"blue", 6:"green",8:"red"}

        if cur_plyr.cur_char not in color_map:
            raise IllegalActionError("character %s doesn't get bonus gold" % cur_plyr.cur_char)

        if self.game_state.round.has_taken_bonus[cur_plyr.position]:
            raise IllegalActionError("player has already taken bonus this round")

        color = color_map[cur_plyr.cur_char]

        num_color = sum(1 for d in cur_plyr.districts_on_table if d.color == color)
        cur_plyr.gold += num_color
        logging.info("Player %s gained %s bonus gold" % (cur_plyr.name, num_color))
        self.game_state.round.has_taken_bonus[cur_plyr.position] = True

    def handle_power_1(self, action, cur_plyr):
        #TODO:  make a decorator that validates a target is present
        if not 'target' in action:
            raise IllegalActionError("No target specified")
        target = action['target']
        if target == 1:
            raise IllegalActionError("You can't target yourself")

        if target not in [2,3,4,5,6,7,8]:
            raise IllegalActionError("Invalid target specified: %s" % target)

        #TODO: if player targets a face up character, announce this as a bold move
        self.game_state.round.dead_char = target

    def handle_power_2(self, action, cur_plyr):
        #TODO:  make a decorator that validates a target is present
        if not 'target' in action:
            raise IllegalActionError("No target specified")
        target = action['target']

        if target == 1:
            raise IllegalActionError("You can't target #1, that wouldn't be fair!")

        if target == 2:
            raise IllegalActionError("You can't target yourself. That would be silly.")

        if target not in [3,4,5,6,7,8]:
            raise IllegalActionError("Invalid target specified: %s" % target)

        #TODO: if player targets a face up character, announce this as a bold move
        self.game_state.round.mugged_char = target

    def handle_power_3(self, action, cur_plyr):
        if not 'target' in action:
           raise IllegalActionError("No target specified")
        target = action['target']
        
        if target == cur_plyr.position:
           raise IllegalActionError("Can't target yourself.")        

        if target not in range(self.game_state.num_players) and target != "deck":
           raise IllegalActionError("Invalid target: %s" % target)        

        hand = cur_plyr.districts_in_hand

        if target == "deck":

            if len(hand) <= 0:
                return  # exchanging 0 cards is a no op

            if not 'discards' in action:
                raise IllegalActionError("No list of cards to discard.")

            discards = action['discards']    

            for d in discards:
                b = self.game_state.buildings[d] 
                if b not in hand:
                    raise IllegalActionError("Can't discard something \
                        that's not in your hand: %s" % b)
                hand.remove(b)
                self.game_state.building_card_deck.append(b)
            n = len(discards)
            replacements = util.draw_n(self.game_state.building_card_deck, n)
            hand.extend(replacements)
        else:
            #swap hands with someone else.  did it by copying contents instead of swapping actual
            #lists in case sqlalchemy needs it this way.  might be overly paranoid .
            #blame my bad experience with JDO ages ago.

            other_hand = self.game_state.players[target].districts_in_hand
            buff = hand[:] 
            hand[:] = other_hand
            other_hand[:] = buff


    # here only for completeness, doesn't do anything
    # crown is assigned at end of round.
    def handle_power_4(self, action, cur_plyr):
        pass

    # here only for completeness, doesn't do anything
    # immunity is handled in handle_power_8 
    def handle_power_5(self, action, cur_plyr):
        pass

    # here only for completeness, doesn't do anything
    # the automatic bonus of 1 gold is handled when keeping a card
    # or taking gold 
    def handle_power_6(self, action, cur_plyr):
        pass

    # here only for completeness, doesn't do anything
    # the automatic bonus of 2 cards gold is handled when keeping a card
    # or taking gold. the extra building ability is handled in build_district 
    def handle_power_7(self, action, cur_plyr):
        pass

    def handle_power_8(self, action, cur_plyr):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.FINISH)
        if not 'target_player_id' in action:
           raise IllegalActionError("No target player specified")
        target_player_pos = action['target_player_id']

        if not 'target_card_id' in action:
           raise IllegalActionError("No target card specified")
        target_card_id = action['target_card_id']
        target_card = self.game_state.buildings[target_card_id]

        if target_player_pos not in range(self.game_state.num_players):
           raise IllegalActionError("Invalid target: %s" % target_player_pos)   

        target_plyr = self.game_state.players[target_player_pos]

        if len(target_plyr.districts_on_table) >= 8:
            raise IllegalActionError("Not allowed to target player with 8 districts")

        if target_plyr.cur_char == 5:
            raise IllegalActionError("Not allowed to target player with character #5")

        logging.warning("target_plyer is %s" % str(target_plyr))
        logging.warning("target card is %s" % str(target_card))
        if target_card not in target_plyr.districts_on_table:
            raise IllegalActionError("Target Player does not have target district")


        cost_to_raze = target_card.cost - 1

        if cost_to_raze > cur_plyr.gold:
            raise IllegalActionError("Not enough gold to destroy target district")

        cur_plyr.gold -= cost_to_raze
        target_plyr.districts_on_table.remove(target_card)


    def validate_phase_and_step(self, phase, *steps):
        if self.game_state.phase is not phase:
            logging.error("attempting action that requires phase %s, but current phase is %s" %
                (phase, self.game_state.phase))
            raise IllegalActionError

        if self.game_state.step not in steps:
            logging.error("attempting action that requires step %s, but current step is %s" %
                (steps, self.game_state.step))
            raise IllegalActionError

    def validate_step(self, *steps):
        if self.game_state.step not in steps:
            logging.error("attempting action that requires step %s, but current step is %s" %
                (steps, self.game_state.step))
            raise IllegalActionError


def init_player(p, i, draw_pile):
        p.set_position(i) 
        #TODO:  replace magic number with actual number of cards in starting hand.
        p.districts_in_hand.extend(util.draw_n(draw_pile, 2)) 



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

    def finish_round(self):
        #TODO: announce dead player if any

        self.check_for_victory()

        #if the konig was around, give that player the crown
        m = self.round.char_to_plyr_map
        if 4 in m:
            #TODO:  announce which player now has the crown
            self.player_with_crown_token = m[4]

    def start_new_round(self):
        self.round = Round(self.players, self.random_gen)
        self.cur_player_index = self.player_with_crown_token
        self.phase = Phase.PICK_CHARACTERS
        self.step = Step.PICK_CHAR
        self.round_num += 1

    def check_for_victory(self):
        #when soeone has built 8 things, game is over
        if self.end_game:
            rankings = []
            for p in self.players:

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
            ranked_players = sorted(self.players, key=lambda p:p.ranking, reverse=True )
            self.winner = ranked_players[0].name

            return True
        return False 

#TODO:  make sure we can't have 2 players with the same name.  or else
# make sure we handle that case properly
class Player:
    def __init__(self, n):
        self.name = n

        self.gold = 2
        self.districts_on_table = []
        self.districts_in_hand = []
        self.cur_char = None
        self.chars = [] 
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
        self.districts_buffer = util.draw_n(deck, 2)

    def set_position(self, i):
        self.position = i

    def __repr__(self):
        return "Player(name=%s, pos=%s, cur_char= %s, chars=%s, gold=%s, hand=%r, dists=%s)" % (self.name, 
            self.position, self.cur_char, self.chars, self.gold, ids(self.districts_in_hand),self.districts_on_table)

# this is sort of a hack for now, to make it convenient to run tests
# right from sublime.
# TODO:  figure out how to run tests easy without this here
if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    import unittest
    unittest.main(module='tests')