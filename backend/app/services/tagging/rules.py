import json, hashlib, os

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_rules():
    path = os.path.join(os.path.dirname(__file__), "../../rules/allergen_keywords.json")
    data = _load_json(path)
    ver = hashlib.sha1(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
    return data, ver

def load_synonyms():
    path = os.path.join(os.path.dirname(__file__), "../../rules/synonyms.json")
    if not os.path.exists(path):
        return {}, "none"
    data = _load_json(path)
    ver = hashlib.sha1(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
    return data, ver
