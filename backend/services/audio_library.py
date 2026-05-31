"""Audio library service for reusable reference samples."""

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from .. import config
from ..database import AudioLibraryItem as DBAudioLibraryItem, ProfileSample as DBProfileSample, VoiceProfile as DBVoiceProfile
from ..models import AudioLibraryItemResponse
from ..utils.audio import load_audio, save_audio, validate_and_load_reference_audio
from ..utils.cache import clear_profile_cache


def _library_dir() -> Path:
    path = config.get_data_dir() / "audio-library"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _to_response(row: DBAudioLibraryItem) -> AudioLibraryItemResponse:
    tags = []
    if row.tags:
        try:
            parsed = json.loads(row.tags)
            if isinstance(parsed, list):
                tags = [str(t) for t in parsed]
        except Exception:
            tags = []
    return AudioLibraryItemResponse(
        id=row.id,
        name=row.name,
        description=row.description,
        language=row.language,
        gender=row.gender,
        style=row.style,
        tags=tags,
        audio_path=row.audio_path,
        duration=row.duration,
        source=row.source,
        created_at=row.created_at,
    )


def list_items(
    db: Session,
    *,
    language: str | None = None,
    gender: str | None = None,
    style: str | None = None,
    query: str | None = None,
) -> list[AudioLibraryItemResponse]:
    q = db.query(DBAudioLibraryItem)
    if language:
        q = q.filter(DBAudioLibraryItem.language == language)
    if gender:
        q = q.filter(DBAudioLibraryItem.gender == gender)
    if style:
        q = q.filter(DBAudioLibraryItem.style == style)
    if query:
        like = f"%{query}%"
        q = q.filter(DBAudioLibraryItem.name.like(like) | DBAudioLibraryItem.description.like(like))
    rows = q.order_by(DBAudioLibraryItem.created_at.desc()).all()
    return [_to_response(row) for row in rows]


async def create_item(
    db: Session,
    *,
    file_path: str,
    name: str,
    description: str | None = None,
    language: str | None = None,
    gender: str | None = None,
    style: str | None = None,
    tags: Iterable[str] | None = None,
) -> AudioLibraryItemResponse:
    import asyncio

    is_valid, error_msg, audio, sr = await asyncio.to_thread(validate_and_load_reference_audio, file_path)
    if not is_valid:
        raise ValueError(f"Invalid reference audio: {error_msg}")

    item_id = str(uuid.uuid4())
    dest = _library_dir() / f"{item_id}.wav"
    await asyncio.to_thread(save_audio, audio, str(dest), sr)
    duration = float(len(audio) / sr) if sr else None

    row = DBAudioLibraryItem(
        id=item_id,
        name=name,
        description=description,
        language=language,
        gender=gender,
        style=style,
        tags=json.dumps(list(tags or []), ensure_ascii=False),
        audio_path=config.to_storage_path(dest),
        duration=duration,
        source="user",
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row)


def get_item_path(db: Session, item_id: str) -> Path | None:
    row = db.query(DBAudioLibraryItem).filter_by(id=item_id).first()
    if not row:
        return None
    return config.resolve_storage_path(row.audio_path)


def delete_item(db: Session, item_id: str) -> bool:
    row = db.query(DBAudioLibraryItem).filter_by(id=item_id).first()
    if not row:
        return False
    if row.source == "default":
        raise ValueError("Default audio library items cannot be deleted")

    path = config.resolve_storage_path(row.audio_path)
    if path is not None and path.exists():
        path.unlink()
    db.delete(row)
    db.commit()
    return True


async def use_as_profile_sample(
    db: Session,
    *,
    item_id: str,
    profile_id: str,
    reference_text: str,
) -> AudioLibraryItemResponse:
    import asyncio

    item = db.query(DBAudioLibraryItem).filter_by(id=item_id).first()
    if not item:
        raise ValueError("Audio library item not found")
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        raise ValueError("Profile not found")

    source_path = config.resolve_storage_path(item.audio_path)
    if source_path is None or not source_path.exists():
        raise ValueError("Audio library file not found")

    audio, sr = await asyncio.to_thread(load_audio, str(source_path), sr=None)
    sample_id = str(uuid.uuid4())
    profile_dir = config.get_profiles_dir() / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    dest = profile_dir / f"{sample_id}.wav"
    await asyncio.to_thread(save_audio, audio, str(dest), sr)

    db.add(
        DBProfileSample(
            id=sample_id,
            profile_id=profile_id,
            audio_path=config.to_storage_path(dest),
            reference_text=reference_text,
        )
    )
    profile.updated_at = datetime.utcnow()
    db.commit()
    clear_profile_cache(profile_id)
    return _to_response(item)
