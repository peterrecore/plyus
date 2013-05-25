import logging
import csv
import util 
from util import lowest_higher_than
from util import reverse_map
from util import ids
from collections import defaultdict
from errors import NotYourTurnError
from errors import IllegalActionError
from errors import NoSuchActionError
from errors import FatalPlyusError 

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


#Each Round consists of two phases
class Phase:
    PICK_ROLES = 'PICK_ROLES'
    PLAY_TURNS = 'PLAY_TURNS'

#The Play turn phase consists of several steps
class Step:
    COINS_OR_BUILDING = 'COINS_OR_BUILDING'
    KEEP_CARD = 'KEEP_CARD'
    MURDER = 'MURDER'
    STEAL = 'STEAL'
    RAZE = 'RAZE'
    BUILD_BUILDING = 'BUILD_BUILDING' 
    PICK_ROLE = 'PICK_ROLE' 
    HIDE_ROLE = 'HIDE_ROLE' 
    FINISH = 'FINISH'

class Round:
    def __init__(self, players,random_gen):
        self.players = players
        self.random_gen = random_gen

        self.plyr_to_role_map = defaultdict(list) 
        self.role_to_plyr_map = {}
        self.has_used_power = {}
        self.has_taken_bonus = {}
        self.num_seven_builds_left = 3
        self.dead_role = None
        self.mugged_role = None


        for p in players:
            #TODO: cleanup before committing for 2/3 player mode
            #self.plyr_to_role_map[p.position] = False no need to init now that this is a defaultdict
            self.has_used_power[p.position] = False
            self.has_taken_bonus[p.position] = False
            p.roles = []
            p.cur_role = None

        face_up_num, face_down_num = self.role_setup_for_n_players(len(players))
        self.role_draw_pile = [1,2,3,4,5,6,7,8]
        random_gen.shuffle(self.role_draw_pile)
        self.face_up_roles = util.draw_n(self.role_draw_pile, face_up_num)
        self.face_down_roles = util.draw_n(self.role_draw_pile, face_down_num)

    def mark_role_picked(self, role, player):
        self.plyr_to_role_map[player].append(role)
        self.role_to_plyr_map[role] = player
        self.role_draw_pile.remove(role)

    def role_setup_for_n_players(self, n):
        # return (num_face_up, num_face_down)
        if n == 2: return (0,1)
        if n == 3: return (0,1)
        if n == 4: return (2,1)
        if n == 5: return (1,1)
        if n == 6: return (0,1)
        raise FatalPlyusError("Wrong number of players: %s" % n)
    
    def done_picking(self):
        #if no player still needs to choose, we're done picking
        # easy case - if everyone has picked one role we're done

        roles_picked = util.flatten(self.plyr_to_role_map.values())
        num_roles_picked = len(roles_picked)
        num_players = len(self.players)

        num_roles_per_player = 1

        if num_players <= 3:
            num_roles_per_player = 2

        return num_roles_picked >= num_players * num_roles_per_player

    def __repr__(self):
        return "Round(draw:%s, up:%s, down:%s\n    plyr_to_role:%s  role_to_plyr:%s" % (self.role_draw_pile,
            self.face_up_roles, self.face_down_roles, self.plyr_to_role_map, self.role_to_plyr_map)

class Referee:
    def __init__(self, rg, gs):
        self.game_state = gs
        self.random_gen = rg
        self.action_handlers = {
             'pick_role':self.handle_pick_role
            ,'hide_role':self.handle_hide_role
            ,'take_gold':self.handle_take_gold
            ,'build_building':self.handle_build_building
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

        #building an 8th building triggers the end of the game
        if len(cur_player.buildings_on_table) >= 8:
            #if no one else has trigged the end yet, this player is first
            #to get 8 buildings, and gets a bonus
            if not self.game_state.end_game:
                cur_player.first_to_eight_buildings = True
            self.game_state.end_game = True

        logging.debug(" -- action handled.")
        # return the new state of the game
        return self.game_state


    def handle_use_power(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS,
                                     Step.BUILD_BUILDING,
                                     Step.FINISH,
                                     Step.COINS_OR_BUILDING)

        round = self.game_state.round
        if round.has_used_power[cur_player.position]:
            raise IllegalActionError("Already Used Power")

        handler = self.power_handlers[cur_player.cur_role]
        handler(action, cur_player)
        round.has_used_power[cur_player.position] = True

    def handle_finish(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.BUILD_BUILDING, Step.FINISH)

        round = self.game_state.round
    #TODO:  cleanup as part of 2/3 change
    #   cur_role = round.plyr_to_role_map[cur_player.position]
        cur_role = cur_player.cur_role

        logging.info("cur_player is %s, cur_role=%s" % (cur_player,cur_role))
        next_role = lowest_higher_than(round.role_to_plyr_map.keys(), cur_role)  
        if next_role == round.dead_role:
            next_role = lowest_higher_than(round.role_to_plyr_map.keys(), cur_role+1)  

        logging.info("next_role is %s  " % next_role)
        # if everyone has played, start a new round
        if (next_role is None):
            #everyone_has_played: start next round
            self.game_state.finish_round()
            self.game_state.start_new_round()

        else:
            #figure out who the next player is, based on the next cur_role to play.
            #reset the step for that player.
            next_player = round.role_to_plyr_map[next_role]
            self.game_state.cur_player_index = next_player
            self.cur_player_index = round.role_to_plyr_map[next_role]
            self.game_state.players[next_player].cur_role = next_role
            self.game_state.step = Step.COINS_OR_BUILDING

    #some things happen before a player "takes an action"
    # which means after they draw cards or take gold
    # we will consider this equivalent to the "start of the turn"
    def pre_action_effects(self, cur_player):
        rnd = self.game_state.round
        if cur_player.cur_role == rnd.mugged_role:
           stolen = cur_player.gold 
           cur_player.gold = 0
           mugger = rnd.role_to_plyr_map[2]
           rnd.players[mugger].gold += stolen
           #TODO: announce gold was stolen

    #some things happen after a player "takes an action"
    # which means after they draw cards or take gold
    def post_action_effects(self, cur_player):
        if cur_player.cur_role == 6:
            cur_player.gold += 1
            #TODO:  merchant getting a bonus gold needs to be an announced event
        if cur_player.cur_role == 7:
            cards = util.draw_n(self.game_state.building_card_deck, 2)
            cur_player.buildings_in_hand.extend(cards)
            #TODO: announce player getting bonus cards

    def handle_take_gold(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_BUILDING)
        self.pre_action_effects(cur_player)
        cur_player.take_gold()
        self.post_action_effects(cur_player)
        self.game_state.step = Step.BUILD_BUILDING

    def handle_build_building(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.BUILD_BUILDING)


        if 'target' not in action:
            logging.error("build action with no target")
            raise IllegalActionError()

        target_id = action['target']

        if target_id != 'skip':
            target = self.game_state.buildings[target_id]

            if target in cur_player.buildings_on_table:
                logging.info("can't build 2 of same thing")
                raise IllegalActionError()

            if target not in cur_player.buildings_in_hand:
                logging.info("Can't build something not in your hand")
                raise IllegalActionError()

            cost = target.cost
            if cost > cur_player.gold :
                logging.info("not enough gold!")
                raise IllegalActionError()
 
            cur_player.buildings_in_hand.remove(target)
            cur_player.buildings_on_table.append(target)
            cur_player.gold = cur_player.gold - cost

        #unless current role is 7, we only get one build so next step is finish
        r = self.game_state.round
        r.num_seven_builds_left -= 1
        if (cur_player.cur_role == 7 and r.num_seven_builds_left > 0):
            self.game_state.step = Step.BUILD_BUILDING
        else:
            self.game_state.step = Step.FINISH

    def handle_draw_cards(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_BUILDING)

        self.pre_action_effects(cur_player)
        cur_player.take_cards(self.game_state.building_card_deck)
        self.game_state.step = Step.KEEP_CARD
        logging.info("possible cards are %s", cur_player.buildings_buffer)

    #TODO: target should be an ID, not an index to keep consistent
    # with rest of actions
    def handle_keep_card(self, action, cur_player):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.KEEP_CARD)
        if 'target' not in action:
            logging.error("keep card action with no target")
            raise IllegalActionError()

        target_index = action['target']
        if target_index < 0 or target_index > len(cur_player.buildings_buffer): 
            logging.error("trying to keep card that wasn't drawn")
            raise IllegalActionError()

        target = cur_player.buildings_buffer[target_index]
        cur_player.buildings_in_hand.append(target)
        cur_player.buildings_buffer.remove(target)
        self.game_state.building_card_deck.extend(cur_player.buildings_buffer)
        self.post_action_effects(cur_player)
        self.game_state.step = Step.BUILD_BUILDING



    def handle_hide_role(self, action, cur_player):
        self.validate_phase_and_step(Phase.PICK_ROLES, Step.HIDE_ROLE)

        if 'target' not in action:
            logging.error("hide role action with no target")
            raise IllegalActionError()

        target = action['target']

        if (target not in self.game_state.round.role_draw_pile):
            logging.error("hide role action with target not in draw pile")

        round = self.game_state.round
        round.role_draw_pile.remove(target)
        round.face_down_roles.append(target)

        self.game_state.advance_cur_player_index()
        self.game_state.step = Step.PICK_ROLE

    def handle_pick_role(self, action, cur_player):
        self.validate_phase_and_step(Phase.PICK_ROLES, Step.PICK_ROLE)

        if 'target' not in action:
            logging.error("pick role action with no target")
            raise IllegalActionError()

        target = action['target']

        if (target not in self.game_state.round.role_draw_pile):
            logging.error("pick role action with target not in draw pile")

        round = self.game_state.round

        cur_player.roles.append(target)
        round.mark_role_picked(target, cur_player.position)

        # handle 2 player special case
        # players must place a role card face down after their middle picks
        # to maintain uncertainty
        num_roles_picked_so_far = len(round.role_to_plyr_map)
        if (self.game_state.num_players == 2 and num_roles_picked_so_far in [2,3]):
            self.game_state.step = Step.HIDE_ROLE
            return

        #if all players have picked a role
        if (self.game_state.round.done_picking()):
            # it's time to play turns, in role number order.
            # so figure out which role's turn it is, and set them
            # to be current player.

            roles_in_play = util.flatten(round.plyr_to_role_map.values())

            current_role = lowest_higher_than(roles_in_play,0)
            cur_plyr_index =  round.role_to_plyr_map[current_role]
            self.game_state.cur_player_index = cur_plyr_index

            self.game_state.players[cur_plyr_index].cur_role = current_role

            logging.info("Done Picking.  cur_role=%s, roles= %s, cur_plyr_pos=%s " 
                % (current_role, cur_player.roles, self.game_state.cur_player_index))
            self.game_state.phase = Phase.PLAY_TURNS
            self.game_state.step = Step.COINS_OR_BUILDING

        #otherwise move on to the next player
        else:
            self.game_state.advance_cur_player_index()


    def handle_take_bonus(self, action, cur_plyr):
        self.validate_phase_and_step(Phase.PLAY_TURNS,
                             Step.BUILD_BUILDING,
                             Step.FINISH,
                             Step.COINS_OR_BUILDING)
        color_map = {4:"yellow", 5:"blue", 6:"green",8:"red"}

        if cur_plyr.cur_role not in color_map:
            raise IllegalActionError("role %s doesn't get bonus gold" % cur_plyr.cur_role)

        if self.game_state.round.has_taken_bonus[cur_plyr.position]:
            raise IllegalActionError("player has already taken bonus this round")

        color = color_map[cur_plyr.cur_role]

        num_color = sum(1 for d in cur_plyr.buildings_on_table if d.color == color)
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

        #TODO: if player targets a face up role, announce this as a bold move
        self.game_state.round.dead_role = target

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

        #TODO: if player targets a face up role, announce this as a bold move
        self.game_state.round.mugged_role = target

    def handle_power_3(self, action, cur_plyr):
        if not 'target' in action:
           raise IllegalActionError("No target specified")
        target = action['target']
        
        if target == cur_plyr.position:
           raise IllegalActionError("Can't target yourself.")        

        if target not in range(self.game_state.num_players) and target != "deck":
           raise IllegalActionError("Invalid target: %s" % target)        

        hand = cur_plyr.buildings_in_hand

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

            other_hand = self.game_state.players[target].buildings_in_hand
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
    # or taking gold. the extra building ability is handled in build_building 
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

        if len(target_plyr.buildings_on_table) >= 8:
            raise IllegalActionError("Not allowed to target player with 8 buildings")

        if target_plyr.cur_role == 5:
            raise IllegalActionError("Not allowed to target player with role #5")

        logging.warning("target_plyer is %s" % str(target_plyr))
        logging.warning("target card is %s" % str(target_card))
        if target_card not in target_plyr.buildings_on_table:
            raise IllegalActionError("Target Player does not have target building")


        cost_to_raze = target_card.cost - 1

        if cost_to_raze > cur_plyr.gold:
            raise IllegalActionError("Not enough gold to destroy target building")

        cur_plyr.gold -= cost_to_raze
        target_plyr.buildings_on_table.remove(target_card)


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

        for i,p in enumerate(players):
            p.set_position(i) 
            #TODO:  replace magic number with actual number of cards in starting hand.
            p.buildings_in_hand.extend(util.draw_n(self.building_card_deck, 2)) 

        self.round_num = -1
        self.round = Round(players, self.random_gen)
        self.player_with_crown_token = 0 #this player gets to go first when picking a role

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
        m = self.round.role_to_plyr_map
        if 4 in m:
            #TODO:  announce which player now has the crown
            self.player_with_crown_token = m[4]

    def start_new_round(self):
        self.round = Round(self.players, self.random_gen)
        self.cur_player_index = self.player_with_crown_token
        self.phase = Phase.PICK_ROLES
        self.step = Step.PICK_ROLE
        self.round_num += 1

    def check_for_victory(self):
        #when soeone has built 8 things, game is over
        if self.end_game:
            rankings = []
            for p in self.players:

                basic_points = 0
                bonus_points = 0
                colors = {}
                for d in p.buildings_on_table:
                    basic_points += d.points
                    colors[d.color] = True

                if len(colors.keys()) == 5:
                    p.rainbow_bonus = True
                    bonus_points += 3


                if len(p.buildings_on_table) >= 8:
                    bonus_points += 2

                if p.first_to_eight_buildings:
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
        self.buildings_on_table = []
        self.buildings_in_hand = []
        self.cur_role = None
        self.roles = [] 
        self.rainbow_bonus = False
        self.first_to_eight_buildings = False

    #current player chooses to get gold
    def take_gold(self):
        self.gold += 2

    #when current player chooses to draw cards
    def take_cards(self, deck):
        if len(deck) < 2:
            #TODO: figure out and implement rule on reshuffling building cards 
            raise FatalPlyusError("Building deck is out of cards.")
        self.buildings_buffer = util.draw_n(deck, 2)

    def set_position(self, i):
        self.position = i

    def __repr__(self):
        return "Player(name=%s, pos=%s, cur_role= %s, roles=%s, gold=%s, hand=%r, dists=%s)" % (self.name, 
            self.position, self.cur_role, self.roles, self.gold, ids(self.buildings_in_hand),self.buildings_on_table)

# this is sort of a hack for now, to make it convenient to run tests
# right from sublime.
# TODO:  figure out how to run tests easy without this here
if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    import unittest
    unittest.main(module='tests')