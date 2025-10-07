import re

def normalize(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^\w\s\-\/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
