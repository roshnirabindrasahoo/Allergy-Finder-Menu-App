# backend/app/routers/ingest.py
from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..db import get_db
from ..models import FileUpload, MenuItem, Allergen
from ..schemas import ParsedRow

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

# ---------- Config ----------
MAX_CSV_BYTES = 2 * 1024 * 1024  # 2MB

# ---------- Load allergen rules once ----------
RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "allergen_keywords.json"

def _normalize_keywords(entry: Any) -> List[str]:
    if isinstance(entry, dict):
        keywords = entry.get("keywords", [])
    elif isinstance(entry, list):
        keywords = entry
    else:
        keywords = []
    out: List[str] = []
    for kw in keywords:
        if isinstance(kw, str):
            kw = kw.strip()
            if kw:
                out.append(kw)
    return out

def _load_rules() -> Dict[str, List[str]]:
    if RULES_PATH.exists():
        with RULES_PATH.open("r", encoding="utf-8") as f:
            raw_rules = json.load(f)
    else:
        raw_rules = {
            "Peanuts": {"keywords": ["peanut", "groundnut", "satay", "pad thai"]},
            "Soy": {"keywords": ["soy", "tofu", "edamame", "soy sauce", "tempeh", "miso"]},
            "Dairy": {"keywords": ["milk", "cheese", "butter", "cream", "paneer", "yogurt", "ghee"]},
            "Eggs": {"keywords": ["egg", "mayonnaise", "mayo", "aioli"]},
            "Gluten": {"keywords": ["wheat", "barley", "rye", "malt", "bread", "pasta", "noodles"]},
            "Fish": {"keywords": ["fish", "salmon", "tuna", "cod", "anchovy"]},
            "Shellfish": {"keywords": ["shrimp", "prawn", "crab", "lobster", "clam", "mussel", "oyster", "scallop"]},
            "Tree Nuts": {"keywords": ["almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut", "nutella"]},
            "Sesame": {"keywords": ["sesame", "tahini", "gomashio"]},
        }
    normalized: Dict[str, List[str]] = {}
    for allergen, entry in raw_rules.items():
        kws = _normalize_keywords(entry)
        if kws:
            normalized[allergen] = kws
    return normalized

ALLERGEN_RULES = _load_rules()
KEYWORD_REGEX: Dict[str, List[re.Pattern]] = {
    allergen: [re.compile(rf"\b{re.escape(kw)}\b", flags=re.IGNORECASE) for kw in keywords]
    for allergen, keywords in ALLERGEN_RULES.items()
}

# ---------- Helpers ----------
REQUIRED_HEADERS = {"item_name", "description", "price"}

def normalize_headers(cols: List[str]) -> Dict[str, str]:
    mapping = {}
    for c in cols:
        key = c.strip().lower()
        if key in {"item", "name", "itemname", "item_name"}:
            mapping[c] = "item_name"
        elif key in {"desc", "details", "description"}:
            mapping[c] = "description"
        elif key in {"price", "amount", "cost"}:
            mapping[c] = "price"
        else:
            mapping[c] = key
    return mapping

def coerce_price(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("$", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None

def predict_allergens(text: str) -> List[str]:
    if not text:
        return []
    found = []
    for allergen, patterns in KEYWORD_REGEX.items():
        if any(p.search(text) for p in patterns):
            found.append(allergen)
    return found

def pandas_read_csv_bytes(content: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as e:
        try:
            return pd.read_csv(io.BytesIO(content), engine="python")
        except Exception:
            raise HTTPException(status_code=422, detail=f"Could not parse CSV: {e}")

# ---------- Routes ----------

@router.post("/csv", dependencies=[Depends(require_role("restaurant"))])
def upload_csv_preview(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")
    content = file.file.read()
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV too large (max 2MB).")

    df = pandas_read_csv_bytes(content)
    colmap = normalize_headers(list(df.columns))
    df = df.rename(columns=colmap)
    missing = REQUIRED_HEADERS - set(df.columns.str.lower())
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required headers: {', '.join(sorted(missing))}. Expected: item_name, description, price",
        )

    rows: List[ParsedRow] = []
    for _, r in df.iterrows():
        item_name = str(r.get("item_name", "")).strip()
        if not item_name:
            continue
        description = r.get("description", None)
        description = None if (isinstance(description, float) and pd.isna(description)) else (str(description) if description is not None else None)
        price = coerce_price(r.get("price"))
        txt = f"{item_name} {description or ''}".strip()
        predicted = predict_allergens(txt)
        rows.append(ParsedRow(item_name=item_name, description=description, price=price, predicted_allergens=predicted))

    payload = [pr.model_dump() for pr in rows]
    f = FileUpload(restaurant_id=user["id"], data_json=payload)
    db.add(f)
    db.commit()
    db.refresh(f)

    return {"fileId": f.id, "preview": payload[:100], "issues": []}

@router.post("/commit", dependencies=[Depends(require_role("restaurant"))])
def commit_csv_preview(
    fileId: int = Query(..., ge=1),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = db.get(FileUpload, fileId)
    if not f:
        raise HTTPException(status_code=404, detail="fileId not found")
    if f.restaurant_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not allowed to commit this file")

    all_names = {a.name: a for a in db.query(Allergen).all()}
    created, updated = 0, 0

    for r in f.data_json:
        item_name = (r.get("item_name") or "").strip()
        if not item_name:
            continue
        description = (r.get("description") or "").strip()
        price = float(r.get("price") or 0.0)

        # ---- UPSERT per (restaurant_id, item_name)
        existing = (
            db.query(MenuItem)
            .filter(MenuItem.restaurant_id == user["id"], MenuItem.item_name == item_name)
            .first()
        )
        if existing:
            existing.description = description
            existing.price = price
            # reattach predicted allergens
            existing.allergens.clear()
            predicted = r.get("predicted_allergens") or []
            for name in predicted:
                a = all_names.get(name)
                if a:
                    existing.allergens.append(a)
            updated += 1
        else:
            mi = MenuItem(
                restaurant_id=user["id"],
                item_name=item_name,
                description=description,
                price=price,
            )
            predicted = r.get("predicted_allergens") or []
            attach = [all_names[name] for name in predicted if name in all_names]
            if attach:
                mi.allergens = attach
            db.add(mi)
            created += 1

    db.delete(f)
    db.commit()
    return {"ok": True, "created": created, "updated": updated}

@router.post("/retag", dependencies=[Depends(require_role("restaurant"))])
def retag_menu_items(
    mine: bool = Query(default=True, description="If true, retag only my restaurant's items"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Re-apply current rules to menu items.
    - If mine=true: only this restaurant's items
    - If mine=false: ALL items (use with admin token or temporarily via your account)
    """
    q = db.query(MenuItem)
    if mine:
        q = q.filter(MenuItem.restaurant_id == user["id"])

    items = q.all()
    all_names = {a.name: a for a in db.query(Allergen).all()}
    changed = 0

    for mi in items:
        text = f"{mi.item_name} {mi.description or ''}".strip()
        predicted = set(predict_allergens(text))
        current = set(a.name for a in mi.allergens)
        if predicted != current:
            # update attachments
            mi.allergens.clear()
            for name in predicted:
                a = all_names.get(name)
                if a:
                    mi.allergens.append(a)
            changed += 1

    db.commit()
    return {"ok": True, "items_scanned": len(items), "retagged": changed}
