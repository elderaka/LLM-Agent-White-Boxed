
import re

dirs = {
    "right": (1,0), "r": (1,0), "east": (1,0),
    "left": (-1,0), "l": (-1,0), "west": (-1,0),
    "up": (0,-1), "u": (0,-1), "north": (0,-1),
    "down": (0,1), "d": (0,1), "south": (0,1)
}

counts = {
    "twice": 2, "thrice": 3
}

# map simple number words to digits for parsing phrases like "two to the right"
number_words = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10"
}

def nearest_foe(state, eid):
    me = state.entity_by_id(eid)
    allies, foes = state.teams(eid)
    if not foes:
        return None
    foes_sorted = sorted(foes, key=lambda e: abs(e["pos"]["x"]-me["pos"]["x"])+abs(e["pos"]["y"]-me["pos"]["y"]))
    return foes_sorted[0]["id"]

def parse(text, state, eid):
    t = text.strip().lower()
    t = t.replace(",", " then ")
    t = re.sub(r"\band then\b", " then ", t)
    parts = re.split(r"\bthen\b|&&|&|;", t)
    seq = []
    me = state.entity_by_id(eid)
    x0 = me["pos"]["x"]; y0 = me["pos"]["y"]
    def enqueue_move(nx, ny):
        seq.append({"actor":eid,"kind":"move","dest":{"x":nx,"y":ny}})
    for part in parts:
        s = part.strip()
        if not s:
            continue
            # normalize simple number words to digits ("two" -> "2")
            for w, d in number_words.items():
                s = re.sub(r"\b" + re.escape(w) + r"\b", d, s)
        mxy = re.search(r"\bmove\s+(to\s+)?(-?\d+)\s+(-?\d+)\b", s)
        if mxy:
            tx = int(mxy.group(2)); ty = int(mxy.group(3))
            cx = x0; cy = y0
            while cx!=tx or cy!=ty:
                dx = 1 if tx>cx else -1 if tx<cx else 0
                dy = 1 if ty>cy else -1 if ty<cy else 0
                nx = cx+dx if dx!=0 else cx
                ny = cy+dy if dx==0 else cy
                enqueue_move(nx, ny)
                cx, cy = nx, ny
            x0, y0 = cx, cy
            continue
        if "move" in s or "step" in s or "go" in s:
            # accept optional numeric words (already normalized) and optional intervening "to" or "to the"
            tokens = re.findall(r"(?:\b(\d+)\s*(?:to\s+|to the\s+)?)?\b(right|left|up|down|east|west|north|south|r|l|u|d)\b|\b(twice|thrice)\b", s)
            if tokens:
                c = 0
                for tok in re.finditer(r"(\d+)?\s*(?:to\s+|to the\s+)?(right|left|up|down|east|west|north|south|r|l|u|d)|\b(twice|thrice)\b", s):
                    g = tok.groups()
                    if g[2]:
                        nrep = counts[g[2]]
                        if c==0:
                            continue
                        last_dir = last_dir_vec
                        for _ in range(nrep-1):
                            x0 += last_dir[0]; y0 += last_dir[1]
                            enqueue_move(x0, y0)
                        continue
                    num = g[0]
                    dirw = g[1]
                    n = int(num) if num else 1
                    dx, dy = dirs[dirw]
                    last_dir_vec = (dx, dy)
                    c += 1
                    for _ in range(n):
                        x0 += dx; y0 += dy
                        enqueue_move(x0, y0)
                continue
        if "attack" in s or "hit" in s or "strike" in s:
            m = re.search(r"(attack|hit|strike)\s+([a-z]+[0-9]+)", s)
            if m:
                tgt = m.group(2)
            else:
                tgt = nearest_foe(state, eid)
            if tgt:
                seq.append({"actor":eid,"kind":"attack","target":tgt})
                continue
        seq.append({"actor":eid,"kind":"talk","text":part.strip()})
    if not seq:
        seq.append({"actor":eid,"kind":"talk","text":text})
    return seq
