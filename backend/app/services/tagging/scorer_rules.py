from rapidfuzz import fuzz
from .normalize import normalize

PHRASE_BOOST = 1.10
NEGATION_PENALTY = 0.60
CTX_POS = [("contains {kw}", 0.10), ("with {kw}", 0.08), ("{kw} sauce", 0.08), ("{kw} butter", 0.12)]
CTX_NEG = [("no {kw}", NEGATION_PENALTY), ("{kw}-free", NEGATION_PENALTY), ("{kw} free", NEGATION_PENALTY), ("without {kw}", NEGATION_PENALTY)]

def score_rules(text: str, rules: dict[str, list[str]]) -> dict[str, float]:
    t = normalize(text)
    scores = {}
    for allergen, kws in rules.items():
        best = 0.0
        for kw in kws:
            s = fuzz.partial_ratio(kw, t) / 100.0
            if " " in kw: s *= PHRASE_BOOST
            for pat, boost in CTX_POS:
                if pat.format(kw=kw) in t: s += boost
            for pat, pen in CTX_NEG:
                if pat.format(kw=kw) in t: s = max(0.0, s - pen)
            best = max(best, min(s, 1.0))
        scores[allergen] = min(best, 1.0)
    if "vegan" in t:
        for a in ("Dairy","Eggs","Fish","Shellfish"):
            scores[a] = max(0.0, scores.get(a,0)-0.6)
    if "gluten-free" in t or "gluten free" in t or "no gluten" in t:
        scores["Gluten"] = max(0.0, scores.get("Gluten",0)-0.6)
    return scores
