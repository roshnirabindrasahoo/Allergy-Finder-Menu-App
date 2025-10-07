from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..models import (
    MenuItem, Allergen, FileUpload, ParsedRow, AllergenPrediction
)
from ..auth import get_current_user, require_role
from ..services.tagging.pipeline import tag_text
import pandas as pd, io, pdfplumber, re, hashlib

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# --- CSV PREVIEW + PREDICT ---
@router.post("/csv")
async def ingest_csv(file: UploadFile = File(...),
                     user=Depends(require_role("restaurant")),
                     db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")
    content = await file.read()
    h = sha256_bytes(content)

    # idempotency: one FileUpload per identical file
    fu = db.query(FileUpload).filter(FileUpload.sha256 == h, FileUpload.restaurant_id == user["id"]).first()
    if not fu:
        fu = FileUpload(restaurant_id=user["id"], filename=file.filename, filetype="csv", sha256=h, pages=1)
        db.add(fu); db.flush()

    df = pd.read_csv(io.BytesIO(content))
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in ["item_name","price"] if c not in df.columns]
    if missing: raise HTTPException(400, f"Missing columns: {missing}")

    preview, issues = [], []
    amap = {a.name.lower(): a for a in db.query(Allergen).all()}

    for i, row in df.iterrows():
        name = str(row.get("item_name","")).strip()
        desc = str(row.get("description","") or "").strip()
        price = row.get("price", 0)
        try:
            price = float(price); assert price >= 0
        except Exception:
            issues.append(f"Row {i+1}: invalid price"); price = 0.0

        if not name:
            issues.append(f"Row {i+1}: item_name required")

        # store parsed_row (idempotent per file_id,row_index)
        pr = db.query(ParsedRow).filter(ParsedRow.file_id == fu.id, ParsedRow.row_index == i).first()
        if not pr:
            pr = ParsedRow(file_id=fu.id, row_index=i, item_name=name, description=desc, price=price, parsing_meta="")
            db.add(pr); db.flush()
        else:
            pr.item_name, pr.description, pr.price = name, desc, price

        # run tagger and store predictions
        accepted, weak, meta = tag_text(name, desc)
        def save(status, pairs):
            for allergen_name, score in pairs:
                aid = amap.get(allergen_name.lower()).id if amap.get(allergen_name.lower()) else None
                if not aid: continue
                # upsert prediction
                db.execute(text("""
                    INSERT INTO allergen_predictions (parsed_row_id, menu_item_id, allergen_id, score, status, rules_version, model_version)
                    VALUES (:pr, NULL, :aid, :sc, :st, :rv, :mv)
                    ON CONFLICT (parsed_row_id, allergen_id) DO UPDATE
                    SET score=EXCLUDED.score, status=EXCLUDED.status, rules_version=EXCLUDED.rules_version, model_version=EXCLUDED.model_version
                """), {"pr": pr.id, "aid": aid, "sc": float(score), "st": status, "rv": meta["rules_version"], "mv": meta["model_version"]})
        save("auto", accepted)
        save("weak", weak)

        preview.append({
            "item_name": name, "description": desc, "price": price,
            "predicted_allergens": [a for a,_ in accepted+weak]
        })

    db.commit()
    return {"fileId": fu.id, "preview": preview, "issues": issues}

# --- PDF PREVIEW + PREDICT (best-effort) ---
@router.post("/pdf")
async def ingest_pdf(file: UploadFile = File(...),
                     user=Depends(require_role("restaurant")),
                     db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "PDF file required")
    content = await file.read()
    h = sha256_bytes(content)

    fu = db.query(FileUpload).filter(FileUpload.sha256 == h, FileUpload.restaurant_id == user["id"]).first()
    if not fu:
        fu = FileUpload(restaurant_id=user["id"], filename=file.filename, filetype="pdf", sha256=h, pages=0)
        db.add(fu); db.flush()

    preview, issues = [], []
    amap = {a.name.lower(): a for a in db.query(Allergen).all()}

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        fu.pages = len(pdf.pages)
        row_idx = 0
        for pageno, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            for raw in text.split("\n"):
                line = raw.strip()
                m = re.search(r"(\d+(?:\.\d{1,2})?)\s*$", line)
                if not m: continue
                price = float(m.group(1))
                left = line[:m.start()].strip()
                parts = [p.strip() for p in left.split(" - ", 1)]
                name = parts[0] if parts else ""
                desc = parts[1] if len(parts) > 1 else ""
                if not name: continue

                pr = db.query(ParsedRow).filter(ParsedRow.file_id == fu.id, ParsedRow.row_index == row_idx).first()
                if not pr:
                    pr = ParsedRow(file_id=fu.id, row_index=row_idx, item_name=name, description=desc, price=price,
                                   parsing_meta=f'{{"page":{pageno+1}}}')
                    db.add(pr); db.flush()
                else:
                    pr.item_name, pr.description, pr.price = name, desc, price

                accepted, weak, meta = tag_text(name, desc)
                def save(status, pairs):
                    for allergen_name, score in pairs:
                        aid = amap.get(allergen_name.lower()).id if amap.get(allergen_name.lower()) else None
                        if not aid: continue
                        db.execute(text("""
                            INSERT INTO allergen_predictions (parsed_row_id, menu_item_id, allergen_id, score, status, rules_version, model_version)
                            VALUES (:pr, NULL, :aid, :sc, :st, :rv, :mv)
                            ON CONFLICT (parsed_row_id, allergen_id) DO UPDATE
                            SET score=EXCLUDED.score, status=EXCLUDED.status, rules_version=EXCLUDED.rules_version, model_version=EXCLUDED.model_version
                        """), {"pr": pr.id, "aid": aid, "sc": float(score), "st": status, "rv": meta["rules_version"], "mv": meta["model_version"]})

                save("auto", accepted)
                save("weak", weak)

                preview.append({"item_name": name, "description": desc, "price": price,
                                "predicted_allergens": [a for a,_ in accepted+weak]})
                row_idx += 1

    if not preview:
        issues.append("Could not auto-detect items. Prefer CSV or provide text-based PDF.")
    db.commit()
    return {"fileId": fu.id, "preview": preview, "issues": issues}

# --- COMMIT: create items + auto-apply predictions ---
@router.post("/commit")
def ingest_commit(fileId: int,
                  user=Depends(require_role("restaurant")),
                  db: Session = Depends(get_db)):
    fu = db.query(FileUpload).filter(FileUpload.id == fileId, FileUpload.restaurant_id == user["id"]).first()
    if not fu: raise HTTPException(404, "File not found for this restaurant")

    amap = {a.id: a for a in db.query(Allergen).all()}
    rows = db.query(ParsedRow).filter(ParsedRow.file_id == fu.id).order_by(ParsedRow.row_index).all()

    created = 0
    for pr in rows:
        if not pr.item_name: continue
        mi = MenuItem(restaurant_id=user["id"], item_name=pr.item_name,
                      description=pr.description or "", price=pr.price or 0)
        db.add(mi); db.flush()

        preds = db.query(AllergenPrediction).filter(AllergenPrediction.parsed_row_id == pr.id).all()
        for pred in preds:
            if pred.status in ("auto","weak"):
                db.execute(text("""
                    INSERT INTO menu_allergens (menu_id, allergen_id)
                    VALUES (:mid, :aid)
                    ON CONFLICT (menu_id, allergen_id) DO NOTHING
                """), {"mid": mi.id, "aid": pred.allergen_id})

        # (optional) copy predictions to item dimension for audit
        for pred in preds:
            db.execute(text("""
                INSERT INTO allergen_predictions (parsed_row_id, menu_item_id, allergen_id, score, status, rules_version, model_version)
                VALUES (NULL, :mi, :aid, :sc, :st, :rv, :mv)
                ON CONFLICT (menu_item_id, allergen_id) DO UPDATE
                SET score=EXCLUDED.score, status=EXCLUDED.status, rules_version=EXCLUDED.rules_version, model_version=EXCLUDED.model_version
            """), {"mi": mi.id, "aid": pred.allergen_id, "sc": float(pred.score),
                   "st": pred.status, "rv": pred.rules_version, "mv": pred.model_version})

        created += 1

    db.commit()
    return {"ok": True, "created": created}
