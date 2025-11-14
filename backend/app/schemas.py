from __future__ import annotations

# backend/app/schemas.py
from typing import List, Optional

from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    token: str

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str  # customer | restaurant | admin

class UserLogin(BaseModel):
    email: str
    password: str

class AllergenOut(BaseModel):
    id: int
    name: str

class AllergySetIn(BaseModel):
    allergyIds: List[int] = Field(default_factory=list)

class MenuItemCreate(BaseModel):
    item_name: str
    description: Optional[str] = ""
    price: float = 0
    allergenIds: Optional[List[int]] = []

class MenuItemOut(BaseModel):
    id: int
    item_name: str
    description: str
    price: float
    allergens: List[str] = []

class IngestItem(BaseModel):
    item_name: str
    description: Optional[str] = ""
    price: float
    allergens: List[str] = Field(default_factory=list)

class IngestCommitIn(BaseModel):
    items: List[IngestItem]

class SuggestIn(BaseModel):
    item_name: Optional[str] = ""
    description: Optional[str] = ""



# ... your other schemas ...

class ParsedRow(BaseModel):
    item_name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: Optional[float] = None
    predicted_allergens: List[str] = []
