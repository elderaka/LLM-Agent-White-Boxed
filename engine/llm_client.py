
import os, re, json

class LLMClient:
    def __init__(self, model_name=None):
        key = os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        try:
            import google.generativeai as genai
        except Exception as e:
            raise RuntimeError("google-generativeai not installed") from e
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(model_name or "gemini-1.5-flash")
    def ask(self, prompt):
        r = self.model.generate_content(prompt)
        return getattr(r, "text", None) or ""
    def extract_json(self, text):
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        s = m.group(0)
        try:
            return json.loads(s)
        except:
            try:
                s2 = re.sub(r"```(?:json)?", "", s)
                return json.loads(s2)
            except:
                return None
