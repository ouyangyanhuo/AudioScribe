"""Voice profile endpoints."""

import io
import json as _json
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from .. import config, models
from ..app import safe_content_disposition
from ..database import VoiceProfile as DBVoiceProfile, get_db
from ..services import channels, export_import, profiles
from ..services.profiles import _profile_to_response

router = APIRouter()


@router.post("/profiles", response_model=models.VoiceProfileResponse)
async def create_profile(data: models.VoiceProfileCreate, db: Session = Depends(get_db)):
    try:
        return await profiles.create_profile(data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles", response_model=list[models.VoiceProfileResponse])
async def list_profiles(db: Session = Depends(get_db)):
    return await profiles.list_profiles(db)


@router.post("/profiles/import", response_model=models.VoiceProfileResponse)
async def import_profile(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
    try:
        return await export_import.import_profile_from_zip(content, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}", response_model=models.VoiceProfileResponse)
async def get_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = await profiles.get_profile(profile_id, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profiles/{profile_id}", response_model=models.VoiceProfileResponse)
async def update_profile(profile_id: str, data: models.VoiceProfileCreate, db: Session = Depends(get_db)):
    try:
        profile = await profiles.update_profile(profile_id, data, db)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    if not await profiles.delete_profile(profile_id, db):
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}


@router.post("/profiles/{profile_id}/samples", response_model=models.ProfileSampleResponse)
async def add_profile_sample(
    profile_id: str,
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    db: Session = Depends(get_db),
):
    allowed_audio_exts = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".webm", ".opus"}
    uploaded_ext = Path(file.filename or "").suffix.lower()
    file_suffix = uploaded_ext if uploaded_ext in allowed_audio_exts else ".wav"

    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
        total_size = 0
        while chunk := await file.read(1024 * 1024):
            total_size += len(chunk)
            if total_size > 50 * 1024 * 1024:
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large (max 50 MB)")
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        return await profiles.add_profile_sample(profile_id, tmp_path, reference_text, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio file: {str(e)}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/profiles/{profile_id}/samples", response_model=list[models.ProfileSampleResponse])
async def get_profile_samples(profile_id: str, db: Session = Depends(get_db)):
    return await profiles.get_profile_samples(profile_id, db)


@router.delete("/profiles/samples/{sample_id}")
async def delete_profile_sample(sample_id: str, db: Session = Depends(get_db)):
    if not await profiles.delete_profile_sample(sample_id, db):
        raise HTTPException(status_code=404, detail="Sample not found")
    return {"message": "Sample deleted successfully"}


@router.put("/profiles/samples/{sample_id}", response_model=models.ProfileSampleResponse)
async def update_profile_sample(sample_id: str, data: models.ProfileSampleUpdate, db: Session = Depends(get_db)):
    sample = await profiles.update_profile_sample(sample_id, data.reference_text, db)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample


@router.post("/profiles/{profile_id}/avatar", response_model=models.VoiceProfileResponse)
async def upload_profile_avatar(profile_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "").suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        return await profiles.upload_avatar(profile_id, tmp_path, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/profiles/{profile_id}/avatar")
async def get_profile_avatar(profile_id: str, db: Session = Depends(get_db)):
    profile = await profiles.get_profile(profile_id, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if not profile.avatar_path:
        raise HTTPException(status_code=404, detail="No avatar found for this profile")
    avatar_path = config.resolve_storage_path(profile.avatar_path)
    if avatar_path is None or not avatar_path.exists():
        raise HTTPException(status_code=404, detail="Avatar file not found")
    return FileResponse(avatar_path)


@router.delete("/profiles/{profile_id}/avatar")
async def delete_profile_avatar(profile_id: str, db: Session = Depends(get_db)):
    if not await profiles.delete_avatar(profile_id, db):
        raise HTTPException(status_code=404, detail="Profile not found or no avatar to delete")
    return {"message": "Avatar deleted successfully"}


@router.get("/profiles/{profile_id}/export")
async def export_profile(profile_id: str, db: Session = Depends(get_db)):
    try:
        profile = await profiles.get_profile(profile_id, db)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        zip_bytes = export_import.export_profile_to_zip(profile_id, db)
        safe_name = "".join(c for c in profile.name if c.isalnum() or c in (" ", "-", "_")).strip() or "profile"
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": safe_content_disposition("attachment", f"profile-{safe_name}.voicebox.zip")},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}/channels")
async def get_profile_channels(profile_id: str, db: Session = Depends(get_db)):
    try:
        return {"channel_ids": await channels.get_profile_channels(profile_id, db)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/profiles/{profile_id}/channels")
async def set_profile_channels(profile_id: str, data: models.ProfileChannelAssignment, db: Session = Depends(get_db)):
    try:
        await channels.set_profile_channels(profile_id, data, db)
        return {"message": "Profile channels updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/profiles/{profile_id}/effects", response_model=models.VoiceProfileResponse)
async def update_profile_effects(profile_id: str, data: models.ProfileEffectsUpdate, db: Session = Depends(get_db)):
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if data.effects_chain is not None:
        from ..utils.effects import validate_effects_chain

        chain_dicts = [e.model_dump() for e in data.effects_chain]
        error = validate_effects_chain(chain_dicts)
        if error:
            raise HTTPException(status_code=400, detail=error)
        profile.effects_chain = _json.dumps(chain_dicts)
    else:
        profile.effects_chain = None

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)
