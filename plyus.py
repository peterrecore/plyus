import logging

class Building:
    def __init__(self,c, p, n):
        self.color = c
        self.points = p
        self.name = n

class NotYourTurnError(Exception):
    def __init__(self, attempted_player, current_player):
        self.attempted_player = attempted_player
        self.current_player = current_player

    def __repr__(self):
        return "NotYourTurnError(attempted_player=%s, current_player=%s" % (self.attempted_player, self.current_player)

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

def create_building_card_deck():
    r = [
     Building("green", 1,"NYSE"),
     Building("green",2,"Federal Reserve"),
     Building("green",2,"Fort Knox"),
     Building("red",1,"National Guard"),
     Building("red",5,"Orbital Lasers"),
     Building("yellow",3,"White House"),
     Building("blue",2,"Boy Scout HQ"),
     Building("blue",5,"Bhudda Statue"),
     Building("purple",6,"Kennedy Space Center")
     ]
    return r

def draw_n(some_list, n):
    #TODO: check to make sure there are enough elements to return
    r = some_list[0:n]
    del some_list[0:n]
    return r

#Each Round consists of two phases
class Phase:
    PICK_CHARACTERS = 'PICK_CHARACTERS'
    PLAY_TURNS = 'PLAY_TURNS'

#The Play turn phase consists of several steps
class Step:
    COINS_OR_DISTRICT = 'COINS_OR_DISTRICT'
    USE_POWER = 'USE_POWER'
    BUILD_DISTRICT = 'BUILD_DISTRICT' 
    NONE = 'NO STEP' 

class Round:
    def __init__(self, players,random_generator):
        self.players = players
        self.random_generator = random_generator
        self.has_chosen_character = {}
        self.has_used_power = {}

        for p in players:
            self.has_chosen_character[p.position] = False
            self.has_used_power[p.position] = False

        face_up_num, face_down_num = self.char_setup_for_n_players(len(players))
        self.character_draw_pile = [1,2,3,4,5,6,7,8]
        random_generator.shuffle(self.character_draw_pile)
        self.face_up_chars = draw_n(self.character_draw_pile, face_up_num)
        self.face_down_chars = draw_n(self.character_draw_pile, face_down_num)

    def char_setup_for_n_players(self, n):
        if n == 2: return (3,2)
        if n == 3: return (2,2)
        if n == 4: return (2,1)
        if n == 5: return (1,1)
        raise FatalPlyusError("Wrong number of players: %s" % n)
    
    def done_picking(self):
        #if no player still needs to choose, we're done picking
        return False not in self.has_chosen_character.values()


    def __repr__(self):
        return "Round(draw:%s, up:%s, down:%s has_chosen:%s" % (self.character_draw_pile,
            self.face_up_chars, self.face_down_chars, self.has_chosen_character)
class Referee:
    def __init__(self, rg, gs):
        self.game_state = gs
        self.random_generator = rg
        self.action_handlers = {
             'pick_character':self.handle_pick_character
            ,'take_gold':self.handle_take_gold
            ,'draw_cards':self.handle_draw_cards
        }


    def perform_action(self, player, action):
        logging.info('%s is attempting to take action: %s', player, action)
        logging.info('game_state is %s' % self.game_state)
        # verify that this player is allowed to act right now
        if player.position != self.game_state.current_player:
            e = NotYourTurnError(player.position, self.game_state.current_player)
            logging.warn("about to raise not your turn: %r", e)
            raise e

        # verify that this action is legal
        if action["name"] not in self.action_handlers:

            raise NoSuchActionError(action["name"])


        # perform the action
        handler = self.action_handlers[action["name"]]
        handler(action) 

        # return the new state of the game

    def handle_take_gold(self, action):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)

        self.game_state.get_current_player().take_gold()
        self.game_state.step = Step.BUILD_DISTRICT

    def handle_draw_cards(self, action):
        self.validate_phase_and_step(Phase.PLAY_TURNS, Step.COINS_OR_DISTRICT)

        self.game_state.get_current_player().take_gold()

        self.game_state.get_current_player().take_cards(self.game_state.drawPile)
        self.game_state.step = Step.BUILD_DISTRICT

    def handle_pick_character(self, action):
        self.validate_phase_and_step(Phase.PICK_CHARACTERS, Step.NONE)

        if 'target' not in action:
            logging.error("pick char action with no target")
            raise IllegalActionError()

        target = action['target']

        if (target not in self.game_state.round.character_draw_pile):
            logging.error("pick char action with target not in draw pile")

        p = self.game_state.players[self.game_state.current_player]

        p.character = target
        self.game_state.round.has_chosen_character[p.position] = True
        #if all players have picked a character
        if (self.game_state.round.done_picking()):
            self.game_state.phase = Phase.PLAY_TURNS
            self.game_state.step = Step.COINS_OR_DISTRICT
        #STARTHERE - figure out which character's turn it is,
        #otherwise move on to the next player
        else:
            self.game_state.advance_current_player()

    def validate_phase_and_step(self, phase, step):
        if self.game_state.phase is not phase:
            raise IllegalActionError

        if self.game_state.step is not step:
            raise IllegalActionError

#TODO: refactor so referee is the only one who knows about random_generator
#      make all gamestate methods more testable by injecting the randomly chosen
#      items rather than doing the random choosing internally
class GameState:

    def initialize_game(self, r, players):
        self.players = players
        self.random_generator = r
        self.draw_pile = create_building_card_deck()
        self.random_generator.shuffle(self.players)

        self.num_players = len(self.players)

        [p.set_position(i) for i,p in enumerate(players)]
        self.round_num = -1
        self.round = Round(players, self.random_generator)
        self.player_with_crown_token = 0 #this player gets to go first when picking a char

        self.start_new_round()

    def advance_current_player(self):
        self.current_player = (self.current_player + 1) % self.num_players

    def __repr__(self):
        return ("phase=%s, step=%s, current_player: %s, round=%s" % 
            (self.phase, self.step, self.current_player, self.round))

    def start_new_round(self):
        self.round = Round(self.players, self.random_generator)
        self.current_player = self.player_with_crown_token
        self.phase = Phase.PICK_CHARACTERS
        self.step = Step.NONE


class Player:
    def __init__(self, n):
        self.name = n

        self.gold = 0
        self.districtsOnTable = []
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
        return "Player(name=%s, pos=%s, char= %s, gold=%s" % (self.name, self.position, self.character, self.gold)

# this is sort of a hack for now, to make it convenient to run tests
# right from sublime.
# TODO:  figure out how to run tests easy without this here
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    import unittest
    unittest.main(module='tests')