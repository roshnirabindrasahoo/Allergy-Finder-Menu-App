from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Allergen, User
from ..schemas import AllergenOut, AllergySetIn
from ..auth import get_current_user

router = APIRouter(prefix="/api/allergens", tags=["allergens"])

@router.get("", response_model=list[AllergenOut])
def list_allergens(db: Session = Depends(get_db)):
    return db.query(Allergen).order_by(Allergen.id).all()

@router.post("/seed")
def seed_allergens(db: Session = Depends(get_db)):
    seed = ["Peanuts","Tree Nuts","Dairy","Eggs","Gluten","Soy","Fish","Shellfish","Sesame"]
    for name in seed:
        if not db.query(Allergen).filter(Allergen.name==name).first():
            db.add(Allergen(name=name))
    db.commit()
    return {"ok": True, "count": db.query(Allergen).count()}

@router.put("/me")
def set_my_allergies(payload: AllergySetIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).get(user["id"])
    if not u: raise HTTPException(status_code=404, detail="User not found")
    u.allergies.clear()
    if payload.allergyIds:
        alls = db.query(Allergen).filter(Allergen.id.in_(payload.allergyIds)).all()
        for a in alls: u.allergies.append(a)
    db.commit()
    return {"ok": True}
