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

class Round:
	PICK_CHARACTERS = 1
	PLAY_TURNS = 2

class Step:
	COINS_OR_DISTRICT = 1
	USE_POWER = 2
	BUILD_DISTRICT = 3

class Phase:
	pass

class Referee:
	def __init__(self, r, gs):
		self.game_state = gs
		self.random_generator = r
		self.action_handlers = {
			 'take_gold':self.handle_take_gold
			,'draw_cards':self.handle_draw_cards
		}

	def perform_action(self, player, action):
		logging.info('player: %s took action: %s', player, action)

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
		self.game_state.get_current_player().take_gold()
		self.game_state.advance_current_player() 

	def handle_draw_cards(self, action):
		self.game_state.get_current_player().take_cards(self.game_state.drawPile)
		self.game_state.advance_current_player() 


class GameState:

	def initialize_game(self, r, players):
		self.players = players
		self.random_generator = r
		self.drawPile = create_building_card_deck()
		self.random_generator.shuffle(self.players)

		self.num_players = len(self.players)

		[p.set_position(i) for i,p in enumerate(players)]
		#current_player is the player who is taking their 
		# turn building things
		self.current_player = 0

	def get_current_player(self):
		return self.players[self.current_player]	

	def advance_current_player(self):
		self.current_player = (self.current_player + 1) % self.num_players

class Player:
	def __init__(self, n):
		self.name = n

		self.gold = 0
		self.districtsOnTable = []
		self.districtsInHand = []

	#current player chooses to get gold
	def take_gold(self):
		self.gold += 2

	#when current player chooses to draw cards
	def take_cards(self, deck):
		self.bufferHand = draw_n(deck, 2)

	def set_position(self, i):
		self.position = i

	def __repr__(self):
		return "Player(name=%s, position=%s, gold=%s" % (self.name, self.position, self.gold)
