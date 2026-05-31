"""Server-side user settings persisted in SQLite."""

from typing import Any

from sqlalchemy.orm import Session

from ..database import DownloadSettings as DBDownloadSettings
from ..database import GenerationSettings as DBGenerationSettings

SINGLETON_ID = 1


def _apply_patch(row: Any, patch: dict[str, Any]) -> None:
    columns = type(row).__table__.columns
    for key, value in patch.items():
        col = columns.get(key)
        if col is None:
            continue
        if value is None and not col.nullable:
            continue
        setattr(row, key, value)


def _get_or_create_generation_row(db: Session) -> DBGenerationSettings:
    row = db.query(DBGenerationSettings).filter(DBGenerationSettings.id == SINGLETON_ID).first()
    if row is None:
        row = DBGenerationSettings(id=SINGLETON_ID)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _get_or_create_download_row(db: Session) -> DBDownloadSettings:
    row = db.query(DBDownloadSettings).filter(DBDownloadSettings.id == SINGLETON_ID).first()
    if row is None:
        row = DBDownloadSettings(id=SINGLETON_ID)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_generation_settings(db: Session) -> DBGenerationSettings:
    return _get_or_create_generation_row(db)


def update_generation_settings(db: Session, patch: dict[str, Any]) -> DBGenerationSettings:
    row = _get_or_create_generation_row(db)
    _apply_patch(row, patch)
    db.commit()
    db.refresh(row)
    return row


def get_download_settings(db: Session) -> DBDownloadSettings:
    return _get_or_create_download_row(db)


def update_download_settings(db: Session, patch: dict[str, Any]) -> DBDownloadSettings:
    row = _get_or_create_download_row(db)
    _apply_patch(row, patch)
    db.commit()
    db.refresh(row)
    return row


def get_download_settings_snapshot() -> tuple[str, bool]:
    try:
        from ..database import session as db_session

        if db_session.SessionLocal is None:
            return "modelscope", False
        db = db_session.SessionLocal()
        try:
            row = get_download_settings(db)
            return row.model_source, row.github_mirror_enabled
        finally:
            db.close()
    except Exception:
        return "modelscope", False
