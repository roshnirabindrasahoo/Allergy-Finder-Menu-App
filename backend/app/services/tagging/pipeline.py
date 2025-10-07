import os
from .rules import load_rules, load_synonyms
from .scorer_rules import score_rules

RULES, RULES_VER = load_rules()
SYN, SYN_VER = load_synonyms()

TAU_HIGH = float(os.getenv("TAGGER_TAU_HIGH", "0.90"))
TAU_LOW  = float(os.getenv("TAGGER_TAU_LOW",  "0.50"))
MODEL_VERSION = f"rules@{RULES_VER}"

def expand_synonyms(text: str) -> str:
    if not SYN: return text or ""
    t = text or ""
    for canonical, variants in SYN.items():
        for v in variants:
            t = t.replace(v.lower(), canonical.lower())
    return t

def tag_text(item_name: str, description: str):
    base = (item_name or "") + " " + (description or "")
    base = expand_synonyms(base)
    rule_scores = score_rules(base, RULES)

    accepted, weak = [], []
    for a, s in rule_scores.items():
        if s >= TAU_HIGH: accepted.append((a, s))
        elif s >= TAU_LOW: weak.append((a, s))
    meta = {"rules_version": RULES_VER, "model_version": MODEL_VERSION, "synonyms_version": SYN_VER}
    return accepted, weak, meta
