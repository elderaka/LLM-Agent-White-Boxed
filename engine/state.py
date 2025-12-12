
import json, os, random
from engine.rng import RNG
from engine.turn import TurnManager

class State:
    def __init__(self):
        self.rulebook = None
        self.campaign = None
        self.scene = None
        self.mode = None
        self.map = {"version":0,"bounds":{"w":20,"h":12},"entities":[]}
        self.flags = {}
        self.rng = RNG("session_demo")
        self.tm = None
    def load_campaign(self, campaign, rulebook):
        self.rulebook = rulebook
        self.campaign = campaign
        entry = campaign["entry_scene"]
        path = os.path.join("data","scenarios",campaign["id"],"scenes",entry+".json")
        self.scene = self._load(path)
        self.mode = self.scene["mode"]
        if "setup" in self.scene:
            self._apply_setup(self.scene["setup"])
        if self.mode=="combat":
            self.start_combat()
    def start_combat(self):
        self.tm = TurnManager(self)
        self.tm.start()
    def current_actor_id(self):
        if self.tm:
            return self.tm.current()
        return None
    def advance_turn(self):
        if self.tm:
            self.tm.advance()
    def goto_scene(self, sid):
        path = os.path.join("data","scenarios",self.campaign["id"],"scenes",sid+".json")
        self.scene = self._load(path)
        self.mode = self.scene["mode"]
        if "setup" in self.scene:
            self._apply_setup(self.scene["setup"])
        if self.mode=="combat":
            self.start_combat()
        else:
            self.tm = None
    def _apply_setup(self, setup):
        mp = setup.get("map_id")
        if mp:
            mpath = os.path.join("data","scenarios",self.campaign["id"],"maps",mp+".json")
            self.map = self._load(mpath)
        spawns = setup.get("spawn",[])
        for s in spawns:
            if "qty" in s:
                for i,pos in enumerate(s["positions"]):
                    self._spawn_from_template(s["template"], s.get("id", s["template"]+"_"+str(i)), pos)
            else:
                self._spawn_from_template(s["template"], s["id"], s["pos"])
    def _load(self,p):
        with open(p,"r",encoding="utf-8") as f:
            return json.load(f)
    def _load_template(self, templ_id):
        for base in [os.path.join("data","bestiary"), os.path.join("data","agents"), os.path.join("data","agents","player")]:
            p = os.path.join(base, templ_id+".json")
            if os.path.exists(p):
                return self._load(p)
        return self._load(os.path.join("data","bestiary",templ_id+".json"))
    def _spawn_from_template(self, templ_id, eid, pos):
        t = self._load_template(templ_id)
        ent = {"id":eid,"kind":t["kind"],"template":templ_id,"name":t["name"],"pos":pos,"hp":{"current":t["hp"]["max"],"max":t["hp"]["max"]},"ac":t.get("ac",12),"speed":t.get("speed",6),"ai":t.get("ai",{}),"actions":t.get("actions",[]),"owner":t.get("owner","")}
        self.map["entities"].append(ent)
    def entity_by_id(self,eid):
        for e in self.map["entities"]:
            if e["id"]==eid:
                return e
        return None
    def entities(self):
        return self.map["entities"]
    def entity_ids_by_kind(self,k):
        return [e["id"] for e in self.map["entities"] if e["kind"]==k]
    def neighbors(self,eid):
        e = self.entity_by_id(eid)
        out = []
        for x,y in [(1,0),(-1,0),(0,1),(0,-1)]:
            out.append({"x":e["pos"]["x"]+x,"y":e["pos"]["y"]+y})
        return out
    def in_bounds(self, p):
        return 0<=p["x"]<self.map["bounds"]["w"] and 0<=p["y"]<self.map["bounds"]["h"]
    def occupied(self, p, ignore=None):
        for e in self.map["entities"]:
            if ignore and e["id"]==ignore:
                continue
            if e["pos"]["x"]==p["x"] and e["pos"]["y"]==p["y"] and e["hp"]["current"]>0:
                return True
        return False
    def teams(self, eid):
        me = self.entity_by_id(eid)
        if me["kind"]=="monster":
            foes = [e for e in self.map["entities"] if e["kind"]=="pc" and e["hp"]["current"]>0]
            allies = [e for e in self.map["entities"] if e["kind"]=="monster" and e["hp"]["current"]>0]
        else:
            foes = [e for e in self.map["entities"] if e["kind"]=="monster" and e["hp"]["current"]>0]
            allies = [e for e in self.map["entities"] if e["kind"]=="pc" and e["hp"]["current"]>0]
        return allies, foes
    def last_events(self, n):
        try:
            with open(os.path.join("io","events.jsonl"),"r",encoding="utf-8") as f:
                lines = f.readlines()[-n:]
                return [json.loads(x) for x in lines if x.strip()] if lines else []
        except:
            return []
