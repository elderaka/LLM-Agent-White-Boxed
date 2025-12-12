
import os, random, json
from engine.llm_client import LLMClient

class Narrator:
    def __init__(self):
        self.llm = None
        try:
            self.llm = LLMClient("gemini-1.5-flash")
        except Exception:
            self.llm = None
        self.moves = [
            "{a} slips {dir}.",
            "{a} darts {dir}.",
            "{a} glides {dir}, eyes fixed.",
            "{a} pads {dir} over the grit.",
            "{a} stalks {dir}."
        ]
        self.misses = [
            "{a}'s swing finds air near {t}.",
            "{t} twists; {a}'s strike whiffs.",
            "{a} lashes out; {t} isn't there.",
            "Steel hisses past {t}."
        ]
        self.hits = [
            "{a} tags {t} ({d}).",
            "{a}'s blow lands on {t} ({d}).",
            "{t} grunts—hit by {a} ({d}).",
            "{a} bites into {t} ({d})."
        ]
        self.downs = [
            "{t} buckles and drops.",
            "{t} collapses, breath ragged, still.",
            "{t} hits the ground and stops moving."
        ]
    def llm_line(self, ctx):
        if not self.llm:
            return None
        prompt = []
        prompt.append("Write one vivid third-person tabletop narration line, <=120 chars, no emojis, no quotes.")
        prompt.append("Context: "+json.dumps(ctx, ensure_ascii=False))
        txt = self.llm.ask("\n".join(prompt)).strip()
        return txt.split("\n")[0][:160]
    def coin(self, lst):
        return random.choice(lst)
    def dir_word(self, src, dst):
        dx = dst["x"]-src["x"]; dy = dst["y"]-src["y"]
        if abs(dx)>=abs(dy):
            return "right" if dx>0 else "left" if dx<0 else "forward"
        else:
            return "down" if dy>0 else "up"
    def narrate(self, event, state):
        kind = event.get("event")
        if kind=="move":
            a = state.entity_by_id(event["actor"])["name"]
            src = event.get("from") or {"x":0,"y":0}
            dst = event["to"]
            ctx = {"type":"move","actor":a,"from":src,"to":dst}
            line = self.llm_line(ctx)
            if line:
                return line
            return self.coin(self.moves).format(a=a, dir=self.dir_word(src,dst))
        if kind=="attack":
            a = state.entity_by_id(event["actor"])["name"]
            t = state.entity_by_id(event["target"])["name"]
            if event.get("hit"):
                d = event.get("dmg",0)
                ctx = {"type":"attack_hit","actor":a,"target":t,"damage":d}
                line = self.llm_line(ctx)
                if line:
                    return line
                return self.coin(self.hits).format(a=a,t=t,d=d)
            else:
                ctx = {"type":"attack_miss","actor":a,"target":t}
                line = self.llm_line(ctx)
                if line:
                    return line
                return self.coin(self.misses).format(a=a,t=t)
        if kind=="down":
            t = state.entity_by_id(event["target"])["name"] if state.entity_by_id(event["target"]) else "Target"
            ctx = {"type":"down","target":t}
            line = self.llm_line(ctx)
            if line:
                return line
            return self.coin(self.downs).format(t=t)
        if kind=="talk":
            a = state.entity_by_id(event["actor"])["name"]
            text = event.get("text","...")
            ctx = {"type":"talk","actor":a,"text":text}
            line = self.llm_line(ctx)
            if line:
                return line
            return f"{a}: {text}"
        return ""
