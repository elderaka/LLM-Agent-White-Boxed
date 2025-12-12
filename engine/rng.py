
import random, hashlib

class RNG:
    def __init__(self, seed):
        h = hashlib.sha256(seed.encode()).hexdigest()
        self.seed = int(h[:16],16)
        self.r = random.Random(self.seed)
    def d(self, sides):
        return self.r.randint(1, sides)
    def roll_str(self, s):
        t = s.lower().replace(" ","")
        if "d" not in t:
            return int(t)
        parts = t.split("d")
        a = int(parts[0]) if parts[0] else 1
        b = parts[1]
        mod = 0
        if "+" in b:
            b,m = b.split("+",1)
            mod = int(m)
        elif "-" in b:
            b,m = b.split("-",1)
            mod = -int(m)
        total = 0
        for _ in range(a):
            total += self.d(int(b))
        return total + mod
    def d20(self):
        return self.d(20)
