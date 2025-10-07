# backend/app/models.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# ---------- Association tables ----------

user_allergies = Table(
    "user_allergies",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True),
)

menu_allergens = Table(
    "menu_allergens",
    Base.metadata,
    Column("menu_id", ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("menu_id", "allergen_id", name="uq_menu_allergen"),
)

# ---------- Core entities ----------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'customer' | 'restaurant' | 'admin'
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    allergies: Mapped[list["Allergen"]] = relationship(
        "Allergen", secondary=user_allergies, back_populates="users"
    )
    menu_items: Mapped[list["MenuItem"]] = relationship(
        "MenuItem", back_populates="restaurant", cascade="all, delete-orphan"
    )

class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User", secondary=user_allergies, back_populates="allergies"
    )
    menu_items: Mapped[list["MenuItem"]] = relationship(
        "MenuItem", secondary=menu_allergens, back_populates="allergens"
    )

class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    restaurant: Mapped["User"] = relationship("User", back_populates="menu_items")
    allergens: Mapped[list["Allergen"]] = relationship(
        "Allergen", secondary=menu_allergens, back_populates="menu_items"
    )

# ---------- Ingestion (files & parsed rows) ----------

class FileUpload(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    filetype: Mapped[str] = mapped_column(String, nullable=False)  # 'csv' | 'pdf'
    sha256: Mapped[str] = mapped_column(String, index=True, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ParsedRow(Base):
    __tablename__ = "parsed_rows"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), index=True)
    row_index: Mapped[int] = mapped_column(Integer)  # 0-based
    item_name: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    parsing_meta: Mapped[str] = mapped_column(Text, default="")  # optional JSON-as-text
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("file_id", "row_index", name="uq_file_row"),
    )

# ---------- Predictions (versioned) ----------

class AllergenPrediction(Base):
    __tablename__ = "allergen_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    parsed_row_id: Mapped[int | None] = mapped_column(
        ForeignKey("parsed_rows.id", ondelete="CASCADE"), nullable=True, index=True
    )
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=True, index=True
    )
    allergen_id: Mapped[int] = mapped_column(ForeignKey("allergens.id", ondelete="CASCADE"), index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # 'auto' | 'weak' | 'rejected'
    rules_version: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("parsed_row_id", "allergen_id", name="uq_row_allergen"),
        UniqueConstraint("menu_item_id", "allergen_id", name="uq_item_allergen"),
    )
