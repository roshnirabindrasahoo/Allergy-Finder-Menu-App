# backend/app/routers/menus.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import MenuItem, Allergen, User
from ..schemas import MenuItemCreate, MenuItemOut
from ..auth import get_current_user, get_optional_user, require_role

router = APIRouter(prefix="/api/menus", tags=["menus"])

@router.post("", dependencies=[Depends(require_role("restaurant"))])
def create_menu_item(payload: MenuItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    mi = MenuItem(
        restaurant_id=user["id"],
        item_name=payload.item_name,
        description=payload.description or "",
        price=payload.price or 0,
    )
    db.add(mi)
    db.flush()
    if payload.allergenIds:
        alls = db.query(Allergen).filter(Allergen.id.in_(payload.allergenIds)).all()
        mi.allergens = alls
    db.commit()
    return {"id": mi.id}

@router.get("", response_model=list[MenuItemOut])
def list_menu_items(
    safeForUser: bool = False,
    excludeAllergenIds: str | None = Query(default=None, description="Comma-separated allergen IDs to exclude"),
    q: str | None = Query(default=None, min_length=1, description="Search item_name/description"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    qry = db.query(MenuItem)

    if q:
        like = f"%{q.strip()}%"
        qry = qry.filter(or_(MenuItem.item_name.ilike(like), MenuItem.description.ilike(like)))

    qry = qry.order_by(MenuItem.id.desc()).offset(offset).limit(limit)
    items: list[MenuItem] = qry.all()

    def serialize(mi: MenuItem):
        return {
            "id": mi.id,
            "item_name": mi.item_name,
            "description": mi.description or "",
            "price": float(mi.price or 0),
            "allergens": [a.name for a in mi.allergens],
        }

    if safeForUser:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required for safe filter")
        u = db.get(User, user["id"])
        u_allergen_names = {a.name for a in u.allergies}
        items = [mi for mi in items if not ({a.name for a in mi.allergens} & u_allergen_names)]

    if excludeAllergenIds:
        ids = [int(x.strip()) for x in excludeAllergenIds.split(",") if x.strip().isdigit()]
        if ids:
            excl_names = {a.name for a in db.query(Allergen).filter(Allergen.id.in_(ids)).all()}
            items = [mi for mi in items if not ({a.name for a in mi.allergens} & excl_names)]

    return [serialize(mi) for mi in items]

@router.get("/mine", dependencies=[Depends(require_role("restaurant"))])
def list_my_menu_items(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == user["id"])
        .order_by(MenuItem.id.desc())
        .all()
    )
    return [
        {
            "id": mi.id,
            "item_name": mi.item_name,
            "description": mi.description or "",
            "price": float(mi.price or 0),
            "allergens": [a.name for a in mi.allergens],
        }
        for mi in items
    ]

@router.delete("/{item_id}", status_code=204, dependencies=[Depends(require_role("restaurant"))])
def delete_menu_item(item_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    mi = db.get(MenuItem, item_id)
    if not mi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    if mi.restaurant_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this item")
    mi.allergens.clear()
    db.delete(mi)
    db.commit()
    return
