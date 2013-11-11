import logging
import util
from plyus.mutable import MutableList 
from plyus.mutable import JSONEncoded
from plyus.errors import FatalPlyusError
from plyus import db


class Round(db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    game_state_id = db.Column(db.Integer, db.ForeignKey('gamestates.id'))
    has_used_power = db.Column(MutableList.as_mutable(JSONEncoded))    
    has_taken_bonus = db.Column(MutableList.as_mutable(JSONEncoded))    
    num_seven_builds_left = db.Column(db.Integer)
    dead_role = db.Column(db.Integer)
    mugged_role = db.Column(db.Integer)

    role_draw_pile = db.Column(MutableList.as_mutable(JSONEncoded))    
    face_up_roles = db.Column(MutableList.as_mutable(JSONEncoded))    
    face_down_roles = db.Column(MutableList.as_mutable(JSONEncoded))    

    def gen_plyr_to_role_map(self):
        m = {}
        for p in self.game_state.players:
            l = []
            l.extend(p.roles)
            m[p.position] = l 
        return m

    def gen_role_to_plyr_map(self):
        m = {}
        for p in self.game_state.players:
            for r in p.roles:
                m[r] = p.position
        return m


    def __init__(self, game_state):
        self.game_state = game_state

        self.has_used_power = [] 
        self.has_taken_bonus = [] 
        self.num_seven_builds_left = 3
        self.dead_role = None
        self.mugged_role = None

        players = game_state.players

        for p in players:
            self.has_used_power.append(False)
            self.has_taken_bonus.append(False)
            p.roles = []
            p.cur_role = None


        face_up_num, face_down_num = self.role_setup_for_n_players(len(players))
        self.role_draw_pile = [1,2,3,4,5,6,7,8]
        game_state.get_random_gen().shuffle(self.role_draw_pile)
        self.face_up_roles = util.draw_n(self.role_draw_pile, face_up_num)
        self.face_down_roles = util.draw_n(self.role_draw_pile, face_down_num)

    def mark_role_picked(self, role, player_id):
        if player_id not in range(0,self.game_state.num_players):
            raise FatalPlyusError("bad player-id")

        logging.info("marking %s as picked by %s" % (role, player_id))

        # logging.info("before appending, plyr_to_role_map is %s" % (repr(self.plyr_to_role_map)))
        # self.plyr_to_role_map[player_id].append(role)
        # logging.info("after appending, plyr_to_role_map is %s" % (repr(self.plyr_to_role_map)))
        # self.role_to_plyr_map[role] = player_id
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

        roles_picked = util.flatten(self.gen_plyr_to_role_map().values())
        logging.info("roles_picked is %s" % roles_picked)
        num_roles_picked = len(roles_picked)
        num_players = len(self.game_state.players)

        num_roles_per_player = 1

        if num_players <= 3:
            num_roles_per_player = 2

        return num_roles_picked >= num_players * num_roles_per_player

    def __repr__(self):
        return "Round(draw:%s, up:%s, down:%s\n    plyr_to_role:%s  role_to_plyr:%s" % (self.role_draw_pile,
            self.face_up_roles, self.face_down_roles, self.gen_plyr_to_role_map(), self.gen_role_to_plyr_map())

    def to_dict_for_public(self):
        d = {}
        fields_to_copy = ['face_up_roles', 'has_used_power', 'has_taken_bonus', 'num_seven_builds_left']

        for k in fields_to_copy:
            d[k] = self.__dict__[k]

        return d
