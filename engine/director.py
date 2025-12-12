
from engine.rng import RNG
from engine.narrator import Narrator

class Director:
    def __init__(self, rulebook, evlog, state):
        self.rulebook = rulebook
        self.evlog = evlog
        self.state = state
        self.rng = state.rng
        self.narr = Narrator()
    def legal_move(self, actor, dest):
        if not self.state.in_bounds(dest):
            return False, "out_of_bounds"
        if self.state.occupied(dest, ignore=actor["id"]):
            return False, "occupied"
        return True, ""
    def step(self, proposal):
        actor = self.state.entity_by_id(proposal["actor"])
        if actor is None or actor["hp"]["current"]<=0:
            return {"narration":""}
        if proposal["kind"]=="talk":
            text = proposal.get("text","...")
            ev = {"event":"talk","actor":actor["id"],"text":text}
            self.evlog.append(ev)
            return {"narration":self.narr.narrate(ev, self.state)}
        if proposal["kind"]=="move":
            dest = proposal["dest"]
            ok, why = self.legal_move(actor, dest)
            if not ok:
                ev = {"event":"move_reject","actor":actor["id"],"reason":why}
                self.evlog.append(ev)
                return {"narration":""}
            src = {"x":actor["pos"]["x"],"y":actor["pos"]["y"]}
            actor["pos"]=dest
            ev = {"event":"move","actor":actor["id"],"from":src,"to":dest}
            self.evlog.append(ev)
            return {"narration":self.narr.narrate(ev, self.state)}
        if proposal["kind"]=="attack":
            target = self.state.entity_by_id(proposal["target"])
            if target is None or target["hp"]["current"]<=0:
                ev = {"event":"attack_reject","actor":actor["id"],"reason":"invalid_target"}
                self.evlog.append(ev)
                return {"narration":""}
            rng = self.rng
            act = None
            for a in actor["actions"]:
                if a["id"]==proposal.get("action_id",a["id"]):
                    act = a
                    break
            if act is None and actor["actions"]:
                act = actor["actions"][0]
            to_hit = act.get("to_hit",0) if act else 0
            hit_roll = rng.d20() + to_hit
            if hit_roll>=target.get("ac",12):
                dmg = rng.roll_str((act or {}).get("damage","1d4"))
                target["hp"]["current"] = max(0, target["hp"]["current"]-dmg)
                ev = {"event":"attack","actor":actor["id"],"target":target["id"],"hit":True,"dmg":dmg}
                self.evlog.append(ev)
                if target["hp"]["current"]==0:
                    self.evlog.append({"event":"down","target":target["id"]})
                return {"narration":self.narr.narrate(ev, self.state)}
            else:
                ev = {"event":"attack","actor":actor["id"],"target":target["id"],"hit":False}
                self.evlog.append(ev)
                return {"narration":self.narr.narrate(ev, self.state)}
        return {"narration":""}
