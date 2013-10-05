import logging
import util
import random
from util import lowest_higher_than
from plyus.misc import *
from errors import NotYourTurnError
from errors import IllegalActionError
from errors import NoSuchActionError
from errors import FatalPlyusError 

class Referee:
    def __init__(self, gs):
        self.game_state = gs
        self.random_gen = gs.get_random_gen()
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
    #TODO: validate that the player submitting this move
    # matches the player in the move.  This might need to happen
    # at a higher layer
    def perform_move(self, move):
        logging.info("-- in round %s, move is {%s}" % (self.game_state.round_num, move))

        logging.debug('game_state is %s' % self.game_state)

        player_index = move['player']
        if player_index not in range(0,self.game_state.num_players):
            raise IllegalActionError("Not a valid player")

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
        cur_player = self.game_state.get_cur_plyr()
        handler = self.action_handlers[action["name"]]
        handler(action,cur_player) 

        #building an 8th building triggers the end of the game
        if len(cur_player.buildings_on_table) >= 8:
            #if no one else has trigged the END_GAME yet, this player is first
            #to get 8 buildings, and gets a bonus
            if self.game_state.stage == Stage.PLAYING: 
                cur_player.first_to_eight_buildings = True
                self.game_state.stage = Stage.END_GAME

        new_cur_player = self.game_state.cur_player_index
        logging.debug(" -- move handled.")
      
        return self.get_current_state_as_json_for_player(new_cur_player)

    def get_current_state_as_json_for_player(self, player_index):
        # return the new state of the game
        for_player = self.game_state.players[player_index]
        d = {}
        d['game'] = self.game_state.to_dict_for_player(for_player)
        d['me'] = for_player.to_dict_for_private(self.game_state.building_card_deck)
        j = util.to_json(d)
        return j 


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
        cur_role = cur_player.cur_role

        role_to_plyr_map = round.gen_role_to_plyr_map()

        logging.info("cur_player is %s, cur_role=%s" % (cur_player,cur_role))
        next_role = lowest_higher_than(role_to_plyr_map.keys(), cur_role)  
        if next_role == round.dead_role:
            next_role = lowest_higher_than(role_to_plyr_map.keys(), cur_role+1)  

        logging.info("next_role is %s  " % next_role)
        # if everyone has played, start a new round
        if (next_role is None):
            #everyone_has_played: start next round
            self.game_state.finish_round()
            self.game_state.start_new_round()

        else:
            #figure out who the next player is, based on the next cur_role to play.
            #reset the step for that player.
            next_player = role_to_plyr_map[next_role]
            self.game_state.cur_player_index = next_player
            self.cur_player_index = role_to_plyr_map[next_role]
            self.game_state.players[next_player].cur_role = next_role
            self.game_state.step = Step.COINS_OR_BUILDING

    #some things happen before a player "takes an action"
    # which means after they draw cards or take gold
    # we will consider this equivalent to the "start of the turn"
    def pre_action_effects(self, cur_player):
        rnd = self.game_state.round

        cur_player.revealed_roles.append(cur_player.cur_role)
        if cur_player.cur_role == rnd.mugged_role:
           stolen = cur_player.gold 
           cur_player.gold = 0
           mugger = rnd.gen_role_to_plyr_map()[2]
           logging.info("Mugger[ %s ] has mugged [%s]" % (mugger, cur_player.name))
           self.game_state.players[mugger].gold += stolen
           #TODO: announce gold was stolen

    #some things happen after a player "takes an action"
    # which means after they draw cards or take gold
    def post_action_effects(self, cur_player):
        if cur_player.cur_role == 6:
            cur_player.gold += 1
            #TODO:  merchant getting a bonus gold needs to be an announced event
        if cur_player.cur_role == 7:
            cards = util.draw_n(self.game_state.building_card_deck.cards, 2)
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

            if target_id in cur_player.buildings_on_table:
                logging.info("can't build 2 of same thing")
                raise IllegalActionError()

            if target_id not in cur_player.buildings_in_hand:
                logging.info("Can't build something not in your hand")
                raise IllegalActionError()

            target = self.game_state.building_card_deck.card_for_id(target_id)

            cost = target.cost
            if cost > cur_player.gold :
                logging.info("not enough gold!")
                raise IllegalActionError()
 
            cur_player.buildings_in_hand.remove(target_id)
            cur_player.buildings_on_table.append(target_id)
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
        cur_player.take_cards(self.game_state.building_card_deck.cards)
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

        target_id = cur_player.buildings_buffer[target_index]
        cur_player.buildings_in_hand.append(target_id)
        cur_player.buildings_buffer.remove(target_id)
        self.game_state.building_card_deck.cards.extend(cur_player.buildings_buffer)
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
        role_to_plyr_map = round.gen_role_to_plyr_map()

        # handle 2 player special case
        # players must place a role card face down after their middle picks
        # to maintain uncertainty
        num_roles_picked_so_far = len(role_to_plyr_map)
        if (self.game_state.num_players == 2 and num_roles_picked_so_far in [2,3]):
            self.game_state.step = Step.HIDE_ROLE
            return

        #if all players have picked a role
        if (self.game_state.round.done_picking()):
            # it's time to play turns, in role number order.
            # so figure out which role's turn it is, and set them
            # to be current player.

            roles_in_play = util.flatten(round.gen_plyr_to_role_map().values())

            current_role = lowest_higher_than(roles_in_play,0)
            cur_plyr_index =  role_to_plyr_map[current_role]
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

        deck = self.game_state.building_card_deck

        cards_on_table = map(deck.card_for_id, cur_plyr.buildings_on_table)

        num_color = sum(1 for c in cards_on_table if c.color == color)
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
                if d not in hand:
                    raise IllegalActionError("Can't discard something \
                        that's not in your hand: %s" % d)
                hand.remove(d)
                self.game_state.building_card_deck.cards.append(d)
            n = len(discards)
            replacements = util.draw_n(self.game_state.building_card_deck.cards, n)
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

        if target_player_pos not in range(self.game_state.num_players):
           raise IllegalActionError("Invalid target: %s" % target_player_pos)   

        target_plyr = self.game_state.players[target_player_pos]

        if len(target_plyr.buildings_on_table) >= 8:
            raise IllegalActionError("Not allowed to target player with 8 buildings")

        if target_plyr.cur_role == 5:
            raise IllegalActionError("Not allowed to target player with role #5")

        logging.info("target_plyer is %s" % str(target_plyr))
        logging.info("razing target is %s" % str(target_card_id))
        if target_card_id not in target_plyr.buildings_on_table:
            raise IllegalActionError("Target Player does not have target building")


        target_card = self.game_state.building_card_deck.card_for_id(target_card_id)
        cost_to_raze = target_card.cost - 1

        if cost_to_raze > cur_plyr.gold:
            raise IllegalActionError("Not enough gold to destroy target building")

        cur_plyr.gold -= cost_to_raze
        target_plyr.buildings_on_table.remove(target_card_id)


    def validate_phase_and_step(self, phase, *steps):
        if self.game_state.phase != phase:
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

