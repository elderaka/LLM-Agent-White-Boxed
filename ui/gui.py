
import tkinter as tk

class GameUI:
    def __init__(self, root, state, director, agents, font):
        self.root = root
        self.state = state
        self.director = director
        self.agents = agents
        self.font = font
        self.canvas = tk.Canvas(root, width=640, height=384, bg="#111")
        self.canvas.pack(fill="both", expand=True)
        self.log = tk.Text(root, height=8, bg="#000", fg="#0f0", insertbackground="#0f0")
        self.log.configure(font=font)
        self.log.pack(fill="x")
        self.entry = tk.Entry(root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.turn_label = tk.Label(root, text="Round 1")
        self.turn_label.pack()
        self.typing = False
        self.waiting_player = False
        self.player_id = None
        for eid,a in self.agents.items():
            if hasattr(a,"enqueue_many"):
                self.player_id = eid
                break
        self.draw()
        self.root.after(400, self.step_turn)
    def draw(self):
        self.canvas.delete("all")
        w = self.state.map["bounds"]["w"]
        h = self.state.map["bounds"]["h"]
        cw = 20
        ch = 20
        for y in range(h):
            for x in range(w):
                self.canvas.create_rectangle(x*cw, y*ch, x*cw+cw, y*ch+ch, outline="#222", fill="#181818")
        for e in self.state.entities():
            x = e["pos"]["x"]
            y = e["pos"]["y"]
            color = "#4af" if e["kind"]=="pc" else "#f44"
            if e["hp"]["current"]==0:
                color = "#555"
            self.canvas.create_rectangle(x*cw+2,y*ch+2,x*cw+cw-2,y*ch+ch-2, fill=color, outline="")
            self.canvas.create_text(x*cw+cw/2,y*ch+ch/2, text=e["name"][0].upper(), fill="#fff")
        self.root.update_idletasks()
    def type_line(self, text):
        if self.typing:
            return
        self.typing = True
        self._type_index = 0
        self._type_text = text+"\n"
        def step():
            if self._type_index<len(self._type_text):
                self.log.insert("end", self._type_text[self._type_index])
                self.log.see("end")
                self._type_index+=1
                self.root.after(10, step)
            else:
                self.typing = False
        step()
    def step_turn(self):
        if self.state.tm is None:
            self.root.after(500, self.step_turn)
            return
        eid = self.state.current_actor_id()
        if not eid:
            self.root.after(500, self.step_turn)
            return
        agent = self.agents.get(eid)
        if agent is None:
            self.state.advance_turn()
            self.root.after(100, self.step_turn)
            return
        if eid==self.player_id and getattr(agent,"queue",[])==[]:
            self.waiting_player = True
            self.turn_label.configure(text=f"Round {self.state.tm.round} — Your turn")
            self.root.after(300, self.step_turn)
            return
        self.waiting_player = False
        acted = 0
        for _ in range(2):
            p = agent.propose()
            if p.get("kind")=="noop":
                break
            res = self.director.step(p)
            if "narration" in res and res["narration"]:
                self.type_line(res["narration"])
            acted += 1
            self.draw()
        if acted==0 and eid==self.player_id:
            self.type_line("...")
        self.state.advance_turn()
        self.turn_label.configure(text=f"Round {self.state.tm.round}")
        self.root.after(300, self.step_turn)
    def on_enter(self, e):
        txt = self.entry.get().strip()
        self.entry.delete(0,"end")
        if not txt:
            return
        me = None
        for eid,a in self.agents.items():
            if hasattr(a,"enqueue_many"):
                me = a
                mid = eid
                break
        if me is None:
            return
        try:
            from engine.agent import LLMRoleplayAgent
            llm_agent = LLMRoleplayAgent(self.state, self.state.rulebook, mid)
            prompt = (
                "You are a translator that converts a player's natural-language command into "
                "a JSON object with fields: say (optional) and plan (array of actions).\n"
                "Actions allowed: move {x,y}, attack {targetId}, talk {text}. Adjacent = 4-neighborhood.\n"
                "Plan at most 3 actions. Use entity coordinates for move targets.\n"
                "Player utterance: " + txt + "\nOutput JSON only."
            )
            textresp = llm_agent.llm.ask(prompt)
            seq = llm_agent.parse_plan(textresp)
            if seq:
                me.enqueue_many(seq)
                self.type_line("queued "+str(len(seq))+" action(s)")
                return
        except Exception:
            pass

        try:
            from engine.parser import parse
            seq = parse(txt, self.state, mid)
            me.enqueue_many(seq)
            self.type_line("queued "+str(len(seq))+" action(s)")
        except Exception:
            me.enqueue_many([{ "actor": mid, "kind": "talk", "text": txt }])
            self.type_line("fallback talk")
