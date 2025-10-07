from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, exists, and_, or_
from ..db import get_db
from ..models import MenuItem, Allergen, User, menu_allergens
from ..schemas import MenuItemCreate, MenuItemOut
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/menus", tags=["menus"])

# ---------- CREATE ----------
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("restaurant"))]
)
def create_menu_item(
    payload: MenuItemCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a menu item for the authenticated restaurant.
    NOTE: We intentionally ignore allergenIds here because tagging is automated
    during ingestion/commit. This keeps the source of truth consistent.
    """
    # Basic validation
    if not payload.item_name or payload.price is None:
        raise HTTPException(status_code=400, detail="item_name and price are required")

    mi = MenuItem(
        restaurant_id=user["id"],
        item_name=payload.item_name.strip(),
        description=(payload.description or "").strip(),
        price=payload.price or 0,
    )
    db.add(mi)
    db.commit()
    db.refresh(mi)
    return {"id": mi.id}

# ---------- LIST ----------
@router.get("", response_model=list[MenuItemOut])
def list_menu_items(
    safeForUser: bool = Query(False, description="Exclude items containing the current user's allergens"),
    restaurantId: int | None = Query(None, description="Only items from this restaurant"),
    q: str | None = Query(None, description="Search term for name/description"),
    excludeAllergenIds: str | None = Query(None, description="Comma-separated allergen IDs to exclude"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns menu items with optional:
      - safeForUser filtering (excludes items intersecting user's allergens)
      - restaurantId filtering
      - full-text-ish search on name/description
      - excludeAllergenIds filtering
      - pagination
    """
    # Base selectable with eager load to avoid N+1 on allergens
    stmt = select(MenuItem).options(selectinload(MenuItem.allergens))

    # Scope to a restaurant if provided
    if restaurantId:
        stmt = stmt.where(MenuItem.restaurant_id == restaurantId)

    # Search across name/description
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(MenuItem.item_name.ilike(like), MenuItem.description.ilike(like)))

    # Exclude by explicit allergen IDs (comma-separated -> list[int])
    excl_ids: list[int] = []
    if excludeAllergenIds:
        excl_ids = [int(x.strip()) for x in excludeAllergenIds.split(",") if x.strip().isdigit()]
        if excl_ids:
            # WHERE NOT EXISTS (SELECT 1 FROM menu_allergens ma WHERE ma.menu_id = MenuItem.id AND ma.allergen_id IN (:ids))
            stmt = stmt.where(
                ~exists(
                    select(menu_allergens.c.menu_id)
                    .where(
                        and_(
                            menu_allergens.c.menu_id == MenuItem.id,
                            menu_allergens.c.allergen_id.in_(excl_ids),
                        )
                    )
                )
            )

    # Safe for logged-in user based on their saved allergen profile
    if safeForUser:
        u = db.get(User, user["id"])
        if not u:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch user's allergen IDs once (filtering by name is fine too, IDs are faster)
        user_allergen_ids = [a.id for a in u.allergies]
        if user_allergen_ids:
            stmt = stmt.where(
                ~exists(
                    select(menu_allergens.c.menu_id)
                    .where(
                        and_(
                            menu_allergens.c.menu_id == MenuItem.id,
                            menu_allergens.c.allergen_id.in_(user_allergen_ids),
                        )
                    )
                )
            )

    # Order newest first; then paginate
    stmt = stmt.order_by(MenuItem.id.desc()).offset((page - 1) * pageSize).limit(pageSize)

    items = db.scalars(stmt).all()

    def serialize(mi: MenuItem):
        return {
            "id": mi.id,
            "item_name": mi.item_name,
            "description": mi.description or "",
            "price": float(mi.price or 0),
            "allergens": [a.name for a in mi.allergens],
        }

    return [serialize(mi) for mi in items]
