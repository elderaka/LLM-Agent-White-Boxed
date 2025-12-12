
import json, os, time

class EventLog:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            open(path,"w").close()
    def append(self, obj):
        with open(self.path,"a",encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False)+"\n")
