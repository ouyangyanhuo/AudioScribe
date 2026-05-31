"""FastAPI route template for Voicebox backend.

Usage:
1. Copy this file to backend/routes/<domain>.py
2. Replace <Domain> and <domain> placeholders
3. Register in backend/routes/__init__.py
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.session import get_db
from .. import models

router = APIRouter()


@router.get("/<domain>")
async def list_items(db: Session = Depends(get_db)):
    """List all items"""
    from ..database.models import <Domain>Model
    return db.query(<Domain>Model).all()


@router.get("/<domain>/{item_id}")
async def get_item(item_id: str, db: Session = Depends(get_db)):
    """Get a single item by ID"""
    from ..database.models import <Domain>Model
    item = db.query(<Domain>Model).filter(<Domain>Model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/<domain>")
async def create_item(data: models.<Domain>Create, db: Session = Depends(get_db)):
    """Create a new item"""
    from ..database.models import <Domain>Model
    item = <Domain>Model(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/<domain>/{item_id}")
async def update_item(item_id: str, data: models.<Domain>Update, db: Session = Depends(get_db)):
    """Update an existing item"""
    from ..database.models import <Domain>Model
    item = db.query(<Domain>Model).filter(<Domain>Model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/<domain>/{item_id}")
async def delete_item(item_id: str, db: Session = Depends(get_db)):
    """Delete an item"""
    from ..database.models import <Domain>Model
    item = db.query(<Domain>Model).filter(<Domain>Model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
