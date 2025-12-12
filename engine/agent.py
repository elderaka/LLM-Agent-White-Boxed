
import math, json, os
from engine.llm_client import LLMClient

class AgentAI:
    def __init__(self, state, rulebook, eid, kind):
        self.state = state
        self.rulebook = rulebook
        self.eid = eid
        self.kind = kind
    def propose(self):
        me = self.state.entity_by_id(self.eid)
        if me is None or me["hp"]["current"]<=0:
            return {"actor":self.eid,"kind":"noop"}
        allies, foes = self.state.teams(self.eid)
        if len(foes)==0:
            return {"actor":self.eid,"kind":"talk","text":"..."}
        foes_sorted = sorted(foes, key=lambda e: abs(e["pos"]["x"]-me["pos"]["x"])+abs(e["pos"]["y"]-me["pos"]["y"]))
        target = foes_sorted[0]
        dx = target["pos"]["x"]-me["pos"]["x"]
        dy = target["pos"]["y"]-me["pos"]["y"]
        dist = abs(dx)+abs(dy)
        if dist==1:
            return {"actor":self.eid,"kind":"attack","target":target["id"]}
        step = {"x":me["pos"]["x"]+(1 if dx>0 else -1 if dx<0 else 0),"y":me["pos"]["y"]+(1 if dy>0 else -1 if dy<0 else 0)}
        if not self.state.in_bounds(step) or self.state.occupied(step, ignore=self.eid):
            for p in self.state.neighbors(self.eid):
                if self.state.in_bounds(p) and not self.state.occupied(p, ignore=self.eid):
                    step = p
                    break
        return {"actor":self.eid,"kind":"move","dest":step}

class PlayerAgent:
    def __init__(self, state, rulebook, eid):
        self.state = state
        self.rulebook = rulebook
        self.eid = eid
        self.queue = []
    def enqueue_many(self, lst):
        self.queue.extend(lst)
    def propose(self):
        if self.queue:
            return self.queue.pop(0)
        return {"actor":self.eid,"kind":"noop"}

class LLMRoleplayAgent:
    def __init__(self, state, rulebook, eid, persona=None, model_name=None):
        self.state = state
        self.rulebook = rulebook
        self.eid = eid
        self.queue = []
        self.persona = persona or {}
        self.llm = LLMClient(model_name=model_name)
    def observation(self):
        me = self.state.entity_by_id(self.eid)
        allies, foes = self.state.teams(self.eid)
        last = self.state.last_events(8)
        obs = {
            "self": me,
            "allies": [{"id":e["id"],"name":e["name"],"pos":e["pos"],"hp":e["hp"]} for e in allies],
            "foes": [{"id":e["id"],"name":e["name"],"pos":e["pos"],"hp":e["hp"]} for e in foes],
            "map": self.state.map["bounds"],
            "scene_mode": self.state.mode,
            "recent_events": last
        }
        return obs
    def build_prompt(self):
        me = self.state.entity_by_id(self.eid)
        rule = self.rulebook
        persona = self.persona
        obs = self.observation()
        p = []
        p.append("You are a turn-based agent in a tabletop skirmish. Speak in-character briefly, then output a JSON plan.")
        p.append("Use only these atomic actions: move {x,y}, attack {targetId}, talk {text}. Adjacent squares are 4-neighborhood.")
        p.append("Plan at most 3 actions. If no legal attack, move closer. If bloodied, you may talk.")
        p.append("Return a JSON object with fields: say (short line), plan (array of actions). Nothing else.")
        p.append("Persona: "+json.dumps(persona, ensure_ascii=False))
        p.append("Rulebook: "+json.dumps(rule, ensure_ascii=False))
        p.append("You are: "+json.dumps({"id":me["id"],"name":me["name"],"hp":me["hp"],"ac":me.get("ac",12)}, ensure_ascii=False))
        p.append("Observation: "+json.dumps(obs, ensure_ascii=False))
        p.append("Output JSON only.")
        return "\n".join(p)
    def parse_plan(self, text):
        data = self.llm.extract_json(text) if isinstance(text, str) else None
        if not data or "plan" not in data:
            return [{"actor":self.eid,"kind":"talk","text":"..."}]
        out = []
        say = data.get("say")
        if isinstance(say, str) and say.strip():
            out.append({"actor":self.eid,"kind":"talk","text":say.strip()})
        for step in data["plan"]:
            k = (step.get("kind") or step.get("type") or "").lower()
            if k=="move" and "x" in step and "y" in step:
                out.append({"actor":self.eid,"kind":"move","dest":{"x":int(step["x"]), "y":int(step["y"])}})
            elif k=="attack" and "targetId" in step:
                out.append({"actor":self.eid,"kind":"attack","target":step["targetId"]})
            elif k=="talk" and "text" in step:
                out.append({"actor":self.eid,"kind":"talk","text":step["text"]})
        if not out:
            out = [{"actor":self.eid,"kind":"talk","text":"..."}]
        return out
    def propose(self):
        if self.queue:
            return self.queue.pop(0)
        try:
            prompt = self.build_prompt()
            text = self.llm.ask(prompt)
            plan = self.parse_plan(text)
            self.queue.extend(plan[1:])
            return plan[0]
        except Exception as e:
            bot = AgentAI(self.state, self.rulebook, self.eid, "fallback")
            return bot.propose()
