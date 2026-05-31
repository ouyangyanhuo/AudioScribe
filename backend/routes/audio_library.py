"""Audio library endpoints."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import audio_library

router = APIRouter(prefix="/audio-library", tags=["audio-library"])


@router.get("", response_model=list[models.AudioLibraryItemResponse])
async def list_audio_library(
    language: str | None = None,
    gender: str | None = None,
    style: str | None = None,
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return audio_library.list_items(db, language=language, gender=gender, style=style, query=q)


@router.get("/{item_id}/audio")
async def get_audio_library_audio(item_id: str, db: Session = Depends(get_db)):
    path = audio_library.get_item_path(db, item_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Audio library item not found")
    return FileResponse(path, media_type="audio/wav")


@router.post("", response_model=models.AudioLibraryItemResponse)
async def upload_audio_library_item(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(None),
    language: str | None = Form(None),
    gender: str | None = Form(None),
    style: str | None = Form(None),
    tags: str | None = Form(None),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".webm", ".opus"}:
        suffix = ".wav"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        total = 0
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > 50 * 1024 * 1024:
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large (max 50 MB)")
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        tag_values = [t.strip() for t in (tags or "").split(",") if t.strip()]
        return await audio_library.create_item(
            db,
            file_path=tmp_path,
            name=name,
            description=description,
            language=language,
            gender=gender,
            style=style,
            tags=tag_values,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.delete("/{item_id}")
async def delete_audio_library_item(item_id: str, db: Session = Depends(get_db)):
    try:
        if not audio_library.delete_item(db, item_id):
            raise HTTPException(status_code=404, detail="Audio library item not found")
        return {"message": "Audio library item deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{item_id}/use-as-sample/{profile_id}", response_model=models.AudioLibraryItemResponse)
async def use_audio_library_item_as_sample(
    item_id: str,
    profile_id: str,
    data: models.AudioLibraryUseAsSampleRequest,
    db: Session = Depends(get_db),
):
    try:
        return await audio_library.use_as_profile_sample(
            db,
            item_id=item_id,
            profile_id=profile_id,
            reference_text=data.reference_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
