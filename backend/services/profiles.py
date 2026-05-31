"""Voice profile management for cloned IndexTTS2 voices."""

import hashlib
import json as _json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import config
from ..database import Generation as DBGeneration, ProfileSample as DBProfileSample, VoiceProfile as DBVoiceProfile
from ..models import EffectConfig, ProfileSampleResponse, VoiceProfileCreate, VoiceProfileResponse
from ..utils.audio import save_audio, validate_and_load_reference_audio
from ..utils.cache import _get_cache_dir, clear_profile_cache
from ..utils.images import process_avatar, validate_image

logger = logging.getLogger(__name__)


def _profile_to_response(
    profile: DBVoiceProfile,
    generation_count: int = 0,
    sample_count: int = 0,
) -> VoiceProfileResponse:
    effects_chain = None
    if profile.effects_chain:
        try:
            effects_chain = [EffectConfig(**e) for e in _json.loads(profile.effects_chain)]
        except Exception as e:
            logger.warning("Failed to parse effects_chain for profile %s: %s", profile.id, e)

    return VoiceProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        language=profile.language,
        avatar_path=profile.avatar_path,
        effects_chain=effects_chain,
        generation_count=generation_count,
        sample_count=sample_count,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def validate_profile_engine(profile, engine: str) -> None:
    if engine != "indextts2":
        raise ValueError("IndexTTS2 is the only supported TTS engine")


async def create_profile(data: VoiceProfileCreate, db: Session) -> VoiceProfileResponse:
    existing_profile = db.query(DBVoiceProfile).filter_by(name=data.name).first()
    if existing_profile:
        raise ValueError(f"A profile with the name '{data.name}' already exists. Please choose a different name.")

    db_profile = DBVoiceProfile(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        language=data.language,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    (config.get_profiles_dir() / db_profile.id).mkdir(parents=True, exist_ok=True)
    return _profile_to_response(db_profile)


async def add_profile_sample(
    profile_id: str,
    audio_path: str,
    reference_text: str,
    db: Session,
) -> ProfileSampleResponse:
    import asyncio

    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")

    is_valid, error_msg, audio, sr = await asyncio.to_thread(validate_and_load_reference_audio, audio_path)
    if not is_valid:
        raise ValueError(f"Invalid reference audio: {error_msg}")

    sample_id = str(uuid.uuid4())
    profile_dir = config.get_profiles_dir() / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    dest_path = profile_dir / f"{sample_id}.wav"
    await asyncio.to_thread(save_audio, audio, str(dest_path), sr)

    db_sample = DBProfileSample(
        id=sample_id,
        profile_id=profile_id,
        audio_path=config.to_storage_path(dest_path),
        reference_text=reference_text,
    )
    db.add(db_sample)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_sample)

    clear_profile_cache(profile_id)
    return ProfileSampleResponse.model_validate(db_sample)


async def get_profile(profile_id: str, db: Session) -> VoiceProfileResponse | None:
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        return None
    return _profile_to_response(profile)


def get_profile_orm_by_name_or_id(name_or_id: str, db: Session) -> DBVoiceProfile | None:
    if not name_or_id:
        return None
    row = db.query(DBVoiceProfile).filter(DBVoiceProfile.id == name_or_id).first()
    if row is not None:
        return row
    return db.query(DBVoiceProfile).filter(func.lower(DBVoiceProfile.name) == name_or_id.lower()).first()


async def get_profile_samples(profile_id: str, db: Session) -> list[ProfileSampleResponse]:
    samples = db.query(DBProfileSample).filter_by(profile_id=profile_id).all()
    return [ProfileSampleResponse.model_validate(s) for s in samples]


async def list_profiles(db: Session) -> list[VoiceProfileResponse]:
    profiles = db.query(DBVoiceProfile).order_by(DBVoiceProfile.created_at.desc()).all()
    if not profiles:
        return []

    gen_counts = dict(db.query(DBGeneration.profile_id, func.count(DBGeneration.id)).group_by(DBGeneration.profile_id).all())
    sample_counts = dict(db.query(DBProfileSample.profile_id, func.count(DBProfileSample.id)).group_by(DBProfileSample.profile_id).all())
    return [
        _profile_to_response(
            p,
            generation_count=gen_counts.get(p.id, 0),
            sample_count=sample_counts.get(p.id, 0),
        )
        for p in profiles
    ]


async def update_profile(profile_id: str, data: VoiceProfileCreate, db: Session) -> VoiceProfileResponse | None:
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        return None

    if profile.name != data.name and db.query(DBVoiceProfile).filter_by(name=data.name).first():
        raise ValueError(f"A profile with the name '{data.name}' already exists. Please choose a different name.")

    profile.name = data.name
    profile.description = data.description
    profile.language = data.language
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


async def delete_profile(profile_id: str, db: Session) -> bool:
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        return False

    db.query(DBProfileSample).filter_by(profile_id=profile_id).delete()
    db.delete(profile)
    db.commit()

    profile_dir = config.get_profiles_dir() / profile_id
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    clear_profile_cache(profile_id)
    return True


async def delete_profile_sample(sample_id: str, db: Session) -> bool:
    sample = db.query(DBProfileSample).filter_by(id=sample_id).first()
    if not sample:
        return False

    profile_id = sample.profile_id
    audio_path = config.resolve_storage_path(sample.audio_path)
    if audio_path is not None and audio_path.exists():
        audio_path.unlink()

    db.delete(sample)
    db.commit()
    clear_profile_cache(profile_id)
    return True


async def update_profile_sample(sample_id: str, reference_text: str, db: Session) -> ProfileSampleResponse | None:
    sample = db.query(DBProfileSample).filter_by(id=sample_id).first()
    if not sample:
        return None

    profile_id = sample.profile_id
    sample.reference_text = reference_text
    db.commit()
    db.refresh(sample)
    clear_profile_cache(profile_id)
    return ProfileSampleResponse.model_validate(sample)


async def create_voice_prompt_for_profile(
    profile_id: str,
    db: Session,
    use_cache: bool = True,
    engine: str = "indextts2",
) -> dict:
    from ..backends import get_tts_backend_for_engine

    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        raise ValueError(f"Profile not found: {profile_id}")
    validate_profile_engine(profile, engine)

    samples = db.query(DBProfileSample).filter_by(profile_id=profile_id).all()
    if not samples:
        raise ValueError(f"No samples found for profile {profile_id}")

    tts_model = get_tts_backend_for_engine(engine)
    if len(samples) == 1:
        sample = samples[0]
        sample_audio_path = config.resolve_storage_path(sample.audio_path)
        if sample_audio_path is None:
            raise ValueError(f"Sample audio not found for profile {profile_id}")
        voice_prompt, _ = await tts_model.create_voice_prompt(
            str(sample_audio_path),
            sample.reference_text,
            use_cache=use_cache,
        )
        return voice_prompt

    audio_paths = []
    for sample in samples:
        sample_audio_path = config.resolve_storage_path(sample.audio_path)
        if sample_audio_path is None:
            raise ValueError(f"Sample audio not found for profile {profile_id}")
        audio_paths.append(str(sample_audio_path))

    combined_audio, combined_text = await tts_model.combine_voice_prompts(audio_paths, [s.reference_text for s in samples])
    sample_ids_str = "-".join(sorted(s.id for s in samples))
    combination_hash = hashlib.md5(sample_ids_str.encode()).hexdigest()[:12]
    cache_dir = _get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    combined_path = cache_dir / f"combined_{profile_id}_{combination_hash}.wav"
    save_audio(combined_audio, str(combined_path), 24000)

    voice_prompt, _ = await tts_model.create_voice_prompt(str(combined_path), combined_text, use_cache=use_cache)
    return voice_prompt


async def upload_avatar(profile_id: str, image_path: str, db: Session) -> VoiceProfileResponse:
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")

    is_valid, error_msg = validate_image(image_path)
    if not is_valid:
        raise ValueError(error_msg)

    if profile.avatar_path:
        old_avatar = config.resolve_storage_path(profile.avatar_path)
        if old_avatar is not None and old_avatar.exists():
            old_avatar.unlink()

    from PIL import Image

    with Image.open(image_path) as img:
        img_format = "JPEG" if img.format in ("MPO", "JPG") else img.format
        ext = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}.get(img_format, ".png")

    profile_dir = config.get_profiles_dir() / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    output_path = profile_dir / f"avatar{ext}"
    process_avatar(image_path, str(output_path))

    profile.avatar_path = config.to_storage_path(output_path)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


async def delete_avatar(profile_id: str, db: Session) -> bool:
    profile = db.query(DBVoiceProfile).filter_by(id=profile_id).first()
    if not profile or not profile.avatar_path:
        return False

    avatar_path = config.resolve_storage_path(profile.avatar_path)
    if avatar_path is not None and avatar_path.exists():
        avatar_path.unlink()

    profile.avatar_path = None
    profile.updated_at = datetime.utcnow()
    db.commit()
    return True
