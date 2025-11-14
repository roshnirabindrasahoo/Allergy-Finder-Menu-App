# backend/app/models.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base

# ------------------------------------------------------------
# Association tables (define BEFORE the ORM classes)
# ------------------------------------------------------------

# Users ↔ Allergens (a customer can have many allergens; an allergen can belong to many users)
user_allergies = Table(
    "user_allergies",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True),
    # optional unique/indexes are inherent via the composite primary key
)

# MenuItems ↔ Allergens (a menu item can have many allergens; an allergen can appear on many items)
menu_item_allergens = Table(
    "menu_item_allergens",
    Base.metadata,
    Column("menu_item_id", ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True),
)

# ------------------------------------------------------------
# ORM models
# ------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="customer", nullable=False)  # "customer" | "restaurant"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Allergies selected by the user (customers)
    allergies: Mapped[List["Allergen"]] = relationship(
        "Allergen",
        secondary=user_allergies,
        back_populates="users",
        lazy="selectin",
    )

    # If you want an easy relationship to menu items the restaurant owns:
    menu_items: Mapped[List["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="restaurant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_role", "role"),
    )


class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    # Users that have this allergen set
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_allergies,
        back_populates="allergies",
        lazy="selectin",
    )

    # Menu items that include this allergen
    menu_items: Mapped[List["MenuItem"]] = relationship(
        "MenuItem",
        secondary=menu_item_allergens,
        back_populates="allergens",
        lazy="selectin",
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Optional[float]] = mapped_column(Float)

    # Owning restaurant (User with role="restaurant")
    restaurant: Mapped["User"] = relationship(
        "User",
        back_populates="menu_items",
        lazy="joined",
    )

    # Allergens predicted/assigned for this item
    allergens: Mapped[List[Allergen]] = relationship(
        "Allergen",
        secondary=menu_item_allergens,  # NOTE: variable (not string) so SQLA can resolve it
        back_populates="menu_items",
        lazy="selectin",
    )

    __table_args__ = (
        # A restaurant should not have two menu items with the exact same name (optional rule—remove if not desired)
        UniqueConstraint("restaurant_id", "item_name", name="uq_menuitem_restaurant_name"),
        Index("ix_menu_items_item_name", "item_name"),
    )

# --- Staging table for uploads awaiting commit ---
class FileUpload(Base):
    __tablename__ = "file_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # list[dict] holding parsed rows (preview), including predicted allergens
    data_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    restaurant: Mapped["User"] = relationship("User", lazy="joined")



