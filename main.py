
import json, os, tkinter as tk, tkinter.font as tkfont
from engine.state import State
from engine.director import Director
from engine.agent import AgentAI, PlayerAgent, LLMRoleplayAgent
from engine.iox import EventLog
from ui.gui import GameUI

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def run(mode, scenario):
    root = tk.Tk()
    root.title("JJE-Agent")
    font = tkfont.Font(family="Courier", size=11)
    state = State()
    evlog = EventLog(os.path.join("io","events.jsonl"))
    rulebook = load_json(os.path.join("data","rules","rulebook.json"))
    scenepath = os.path.join("data","scenarios",scenario,"index.json")
    campaign = load_json(scenepath)
    state.load_campaign(campaign, rulebook)
    director = Director(rulebook, evlog, state)
    agents = {}
    for e in state.map["entities"]:
        eid = e["id"]
        if e["kind"]=="pc":
            if mode=="player" and (not agents):
                agents[eid] = PlayerAgent(state, rulebook, eid)
            else:
                persona = {"name":e["name"],"class":e.get("template","pc"),"style":e.get("ai",{}).get("style","")}
                agents[eid] = LLMRoleplayAgent(state, rulebook, eid, persona=persona)
        else:
            agents[eid] = AgentAI(state, rulebook, eid, "monster")
    ui = GameUI(root, state, director, agents, font)
    root.mainloop()

def chooser():
    c = tk.Tk()
    c.title("Start")
    v_mode = tk.StringVar(value="player")
    v_scn = tk.StringVar()
    modes = tk.Frame(c); modes.pack(fill="x")
    tk.Label(modes, text="Mode").pack(anchor="w")
    tk.Radiobutton(modes, text="Player", variable=v_mode, value="player").pack(anchor="w")
    tk.Radiobutton(modes, text="Observer", variable=v_mode, value="observer").pack(anchor="w")
    scn = tk.Frame(c); scn.pack(fill="x")
    tk.Label(scn, text="Scenario").pack(anchor="w")
    scenarios = [d for d in os.listdir(os.path.join("data","scenarios")) if os.path.isdir(os.path.join("data","scenarios",d))]
    if not scenarios:
        scenarios = ["demo"]
    v_scn.set(scenarios[0])
    for s in scenarios:
        tk.Radiobutton(scn, text=s, variable=v_scn, value=s).pack(anchor="w")
    def go():
        m = v_mode.get()
        s = v_scn.get()
        c.destroy()
        run(m, s)
    tk.Button(c, text="Start", command=go).pack(fill="x")
    c.mainloop()

if __name__=="__main__":
    chooser()
