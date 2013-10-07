import logging
import util
import random
from plyus.misc import *
from plyus.round import Round 
from plyus import db

#TODO: refactor so referee is the only one who knows about random_gen
#      make all gamestate methods more testable by injecting the randomly chosen
#      items rather than doing the random choosing internally
class GameState(db.Model):
    __tablename__ = 'gamestates'
    id = db.Column(db.Integer, primary_key=True)
    stage = db.Column(db.String)
    step = db.Column(db.String)
    phase = db.Column(db.String)
    players = db.relationship("Player", order_by="Player.position")
    base_seed = db.Column(db.Integer) 
    building_card_deck = db.relationship(BuildingDeck, uselist=False)
    num_players = db.Column(db.Integer)  
    round_num = db.Column(db.Integer)
    cur_player_index = db.Column(db.Integer)
    player_with_crown_token = db.Column(db.Integer)
    winner = db.Column(db.Integer)
    round = db.relationship("Round", uselist=False, backref="game_state")


    def initialize_game(self, base_seed, players, deck_template):

        self.stage = Stage.PRE_GAME
        self.step = Step.NO_STEP
        self.players = players
        self.base_seed = base_seed 
        self.building_card_deck = BuildingDeck(deck_template)
        self.cur_player_index = 0
        self.round_num = -1
        rand_gen = self.get_random_gen()
        rand_gen.shuffle(self.players)
        rand_gen.shuffle(self.building_card_deck.cards)

        self.num_players = len(self.players)

        for i,p in enumerate(self.players):
            p.set_position(i) 
            #TODO:  replace magic number with actual number of cards in starting hand.
            p.buildings_in_hand.extend(util.draw_n(self.building_card_deck.cards, 4)) 

        self.round = Round(self)
        self.player_with_crown_token = 0 #this player gets to go first when picking a role
        self.stage = Stage.PLAYING
        self.start_new_round()
        self.winner = None

    def to_dict_for_public(self):
        d = {}
        fields_to_copy = ['round_num','player_with_crown_token','stage',
                          'phase','step','cur_player_index','num_players',
                          'winner']
        for k in fields_to_copy:
            d[k] = self.__dict__[k] 

        d['players'] = [p.to_dict_for_public(self.building_card_deck) for p in self.players]

        r = self.round.to_dict_for_public()

        d['round'] = r
        return d

    def to_dict_for_player(self, player):
        d = self.to_dict_for_public()

        r = self.round.to_dict_for_public()
        logging.debug("in todictforplayer %s" % (player))
        if player.position == self.cur_player_index and self.phase == Phase.PICK_ROLES:
            logging.debug("assigning role_draw_pile now")
            r['role_draw_pile'] = self.round.role_draw_pile
        else:
            logging.debug(" %s not equal %s" % (player.position, self.cur_player_index)) 
            logging.debug("or  %s not equal %s" % (self.phase, Phase.PICK_ROLES)) 
        d['round'] = r
        return d
         
    def advance_cur_player_index(self):
        self.cur_player_index = (self.cur_player_index + 1) % self.num_players

    def __repr__(self):
        return ("phase=%s, step=%s, cur_player_index: %s, round=%s" % 
            (self.phase, self.step, self.cur_player_index, self.round))

    def finish_round(self):
        logging.debug("made it to finish_round with stage as %s" % self.stage)
        #TODO: announce dead player if any

        # if we are in the end_game (someone built 8 things)
        # and we are done with the round, game is over
        if self.stage == Stage.END_GAME:
            self.do_game_over_calculations()
            self.stage = Stage.GAME_OVER 
        logging.info("after end game check, stage is %s" % self.stage)
        #if the konig was around, give that player the crown
        m = self.round.gen_role_to_plyr_map()
        if 4 in m:
            #TODO:  announce which player now has the crown
            self.player_with_crown_token = m[4]

    def start_new_round(self):
        logging.info("starting new round")
        self.round = Round(self)
        self.cur_player_index = self.player_with_crown_token
        self.phase = Phase.PICK_ROLES
        self.step = Step.PICK_ROLE
        self.round_num += 1

        for p in self.players:
            p.revealed_roles = []

    def get_cur_plyr(self):
        return self.players[self.cur_player_index]

    # this should only be called at the end of a round, after
    # all players have taken their turn and we are in the
    # END_GAME stage
    def do_game_over_calculations(self):

        rankings = []
        for p in self.players:

            basic_points = 0
            bonus_points = 0
            colors = {}
            buildings = map(self.building_card_deck.card_for_id, p.buildings_on_table)
            for d in buildings:
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

    def get_random_gen(self):
        cur_plyr = self.get_cur_plyr()
        seed = str(self.base_seed) + str(self.round_num * 117) + str(self.cur_player_index * 13) 

        seed = seed + self.step
        str(cur_plyr.name) + str(cur_plyr.buildings_in_hand)
        return random.Random(seed)
