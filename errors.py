#TODO: refactor errors so we can include an explanation in each
#TODO: refactor errors so they log themselves 

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



class IllegalActionError(Exception):
    def __init__(self, attempted_action=""):
        self.attempted_action = attempted_action
    def __repr__(self):
        return "IllegalActionError(attempted_action=%s)" % (self.attempted_action)
