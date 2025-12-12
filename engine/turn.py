
from engine.rng import RNG

class TurnManager:
    def __init__(self, state):
        self.state = state
        self.order = []
        self.idx = 0
        self.round = 1
    def start(self):
        ents = [e for e in self.state.entities() if e["hp"]["current"]>0]
        rolls = []
        for e in ents:
            mod = e.get("initiative_mod",0)
            r = self.state.rng.d20() + mod
            rolls.append((r, e["id"]))
        rolls.sort(key=lambda x:(-x[0], x[1]))
        self.order = [eid for _,eid in rolls]
        self.idx = 0
        self.round = 1
    def current(self):
        if not self.order:
            return None
        eid = self.order[self.idx%len(self.order)]
        ent = self.state.entity_by_id(eid)
        if not ent or ent["hp"]["current"]<=0:
            self.advance()
            return self.current()
        return eid
    def advance(self):
        self.idx += 1
        if self.idx%len(self.order)==0:
            self.round += 1
    def alive(self, eid):
        e = self.state.entity_by_id(eid)
        return e and e["hp"]["current"]>0
