from plyus import *

class Object(object):
    def __init__(self, d):
        self.__dict__ = d
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
        logging.info("%s is picking a role, and game.round.role_draw_pile is : %s" % (me.name, game.round.role_draw_pile))
        my_role = game.round.role_draw_pile[0]

        #this method of choosing a good victim will be absoultely wrong
        #whenever we are the last player to pick.  But no one
        #said that SimpleAI was supposed to be smart. 
        self.likely_victim = game.round.role_draw_pile[1]

        return {"name":"pick_role", "target":my_role}


    def decide_what_to_do_json(self, some_json):
        d = some_json['game']
        game = Object(d)

        r = Object(game.round)
        game.round = r

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