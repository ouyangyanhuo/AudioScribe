"""FastAPI service template for Voicebox backend.

Usage:
1. Copy this file to backend/services/<domain>.py
2. Replace <Domain> and <domain> placeholders
3. Import and use in your route handlers
"""

from sqlalchemy.orm import Session

from ..database.models import <Domain>Model


def get_items(db: Session, limit: int = 100) -> list[<Domain>Model]:
    """Get a list of items"""
    return db.query(<Domain>Model).limit(limit).all()


def get_item_by_id(db: Session, item_id: str) -> <Domain>Model | None:
    """Get a single item by ID"""
    return db.query(<Domain>Model).filter(<Domain>Model.id == item_id).first()


def create_item(db: Session, name: str, **kwargs) -> <Domain>Model:
    """Create a new item"""
    item = <Domain>Model(name=name, **kwargs)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_id: str, **kwargs) -> <Domain>Model | None:
    """Update an existing item"""
    item = get_item_by_id(db, item_id)
    if not item:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: str) -> bool:
    """Delete an item. Returns True if deleted, False if not found."""
    item = get_item_by_id(db, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
