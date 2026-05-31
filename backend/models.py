"""Pydantic request and response models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


LANGUAGE_PATTERN = "^(zh|en|ja|ko|de|fr|ru|pt|es|it|he|ar|da|el|fi|hi|ms|nl|no|pl|sv|sw|tr)$"


class EffectConfig(BaseModel):
    """A single effect in an effects chain."""

    type: str
    enabled: bool = True
    params: dict = Field(default_factory=dict)


class VoiceProfileCreate(BaseModel):
    """Request model for creating or updating a cloned voice profile."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    language: str = Field(default="en", pattern=LANGUAGE_PATTERN)


class VoiceProfileResponse(BaseModel):
    """Response model for a cloned voice profile."""

    id: str
    name: str
    description: Optional[str]
    language: str
    avatar_path: Optional[str] = None
    effects_chain: Optional[list[EffectConfig]] = None
    generation_count: int = 0
    sample_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileSampleCreate(BaseModel):
    reference_text: str = Field(..., min_length=1, max_length=1000)


class ProfileSampleUpdate(BaseModel):
    reference_text: str = Field(..., min_length=1, max_length=1000)


class ProfileSampleResponse(BaseModel):
    id: str
    profile_id: str
    audio_path: str
    reference_text: str

    class Config:
        from_attributes = True


class GenerationRequest(BaseModel):
    """Request model for IndexTTS2 generation."""

    profile_id: str
    text: str = Field(..., min_length=1, max_length=50000)
    language: str = Field(default="en", pattern=LANGUAGE_PATTERN)
    seed: Optional[int] = Field(None, ge=0)
    model_size: Optional[str] = Field(default=None, pattern="^(1\\.7B|0\\.6B|1B|3B)$")
    instruct: Optional[str] = Field(None, max_length=500)
    engine: Optional[str] = Field(default="indextts2", pattern="^indextts2$")
    emo_audio_prompt: Optional[str] = Field(None, max_length=1000)
    emo_alpha: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    emo_vector: Optional[list[float]] = Field(default=None, min_length=8, max_length=8)
    use_emo_text: bool = False
    emo_text: Optional[str] = Field(None, max_length=1000)
    use_random: bool = False
    interval_silence: Optional[int] = Field(default=200, ge=0, le=5000)
    max_text_tokens_per_segment: Optional[int] = Field(default=120, ge=20, le=500)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1, le=200)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    length_penalty: Optional[float] = Field(default=None, ge=-10.0, le=10.0)
    num_beams: Optional[int] = Field(default=None, ge=1, le=10)
    repetition_penalty: Optional[float] = Field(default=None, ge=0.0, le=30.0)
    max_mel_tokens: Optional[int] = Field(default=None, ge=100, le=10000)
    max_chunk_chars: int = Field(default=800, ge=100, le=5000)
    crossfade_ms: int = Field(default=50, ge=0, le=500)
    normalize: bool = True
    effects_chain: Optional[list[EffectConfig]] = None


class GenerationVersionResponse(BaseModel):
    id: str
    generation_id: str
    label: str
    audio_path: str
    effects_chain: Optional[list[EffectConfig]] = None
    source_version_id: Optional[str] = None
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GenerationResponse(BaseModel):
    id: str
    profile_id: str
    text: str
    language: str
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    seed: Optional[int] = None
    instruct: Optional[str] = None
    engine: Optional[str] = "indextts2"
    model_size: Optional[str] = None
    status: str = "completed"
    error: Optional[str] = None
    is_favorited: bool = False
    source: str = "manual"
    created_at: datetime
    versions: Optional[list[GenerationVersionResponse]] = None
    active_version_id: Optional[str] = None

    class Config:
        from_attributes = True


class HistoryQuery(BaseModel):
    profile_id: Optional[str] = None
    search: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class HistoryResponse(GenerationResponse):
    profile_name: str


class HistoryListResponse(BaseModel):
    items: list[HistoryResponse]
    total: int


class GenerationSettingsResponse(BaseModel):
    max_chunk_chars: int = Field(default=800, ge=100, le=5000)
    crossfade_ms: int = Field(default=50, ge=0, le=500)
    normalize_audio: bool = True
    autoplay_on_generate: bool = True

    class Config:
        from_attributes = True


class GenerationSettingsUpdate(BaseModel):
    max_chunk_chars: Optional[int] = Field(default=None, ge=100, le=5000)
    crossfade_ms: Optional[int] = Field(default=None, ge=0, le=500)
    normalize_audio: Optional[bool] = None
    autoplay_on_generate: Optional[bool] = None


class DownloadSettingsResponse(BaseModel):
    model_source: Literal["huggingface", "modelscope"] = "modelscope"
    github_mirror_enabled: bool = False

    class Config:
        from_attributes = True


class DownloadSettingsUpdate(BaseModel):
    model_source: Optional[Literal["huggingface", "modelscope"]] = None
    github_mirror_enabled: Optional[bool] = None


class AudioLibraryItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    style: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    audio_path: str
    duration: Optional[float] = None
    source: Literal["default", "user"] = "user"
    created_at: datetime

    class Config:
        from_attributes = True


class AudioLibraryUseAsSampleRequest(BaseModel):
    reference_text: str = Field(..., min_length=1, max_length=1000)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_downloaded: Optional[bool] = None
    model_size: Optional[str] = None
    gpu_available: bool
    gpu_type: Optional[str] = None
    vram_used_mb: Optional[float] = None
    backend_type: Optional[str] = None
    backend_variant: Optional[str] = None
    gpu_compatibility_warning: Optional[str] = None


class DirectoryCheck(BaseModel):
    path: str
    exists: bool
    writable: bool
    error: Optional[str] = None


class FilesystemHealthResponse(BaseModel):
    healthy: bool
    disk_free_mb: Optional[float] = None
    disk_total_mb: Optional[float] = None
    directories: list[DirectoryCheck]


class ModelStatus(BaseModel):
    model_name: str
    display_name: str
    hf_repo_id: Optional[str] = None
    downloaded: bool
    downloading: bool = False
    size_mb: Optional[float] = None
    loaded: bool = False


class ModelStatusListResponse(BaseModel):
    models: list[ModelStatus]


class ModelDownloadRequest(BaseModel):
    model_name: str


class ModelMigrateRequest(BaseModel):
    destination: str


class ActiveDownloadTask(BaseModel):
    model_name: str
    status: str
    started_at: datetime
    error: Optional[str] = None
    progress: Optional[float] = None
    current: Optional[int] = None
    total: Optional[int] = None
    filename: Optional[str] = None


class ActiveGenerationTask(BaseModel):
    task_id: str
    profile_id: str
    text_preview: str
    started_at: datetime


class ActiveTasksResponse(BaseModel):
    downloads: list[ActiveDownloadTask]
    generations: list[ActiveGenerationTask]


class AudioChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    device_ids: list[str] = Field(default_factory=list)


class AudioChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_ids: Optional[list[str]] = None


class AudioChannelResponse(BaseModel):
    id: str
    name: str
    is_default: bool
    device_ids: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChannelVoiceAssignment(BaseModel):
    profile_ids: list[str]


class ProfileChannelAssignment(BaseModel):
    channel_ids: list[str]


class StoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class StoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    item_count: int = 0

    class Config:
        from_attributes = True


class StoryItemDetail(BaseModel):
    id: str
    story_id: str
    generation_id: str
    version_id: Optional[str] = None
    start_time_ms: int
    track: int = 0
    trim_start_ms: int = 0
    trim_end_ms: int = 0
    created_at: datetime
    profile_id: str
    profile_name: str
    text: str
    language: str
    audio_path: str
    duration: float
    seed: Optional[int]
    instruct: Optional[str]
    engine: Optional[str] = "indextts2"
    volume: float = 1.0
    generation_created_at: datetime
    versions: Optional[list[GenerationVersionResponse]] = None
    active_version_id: Optional[str] = None

    class Config:
        from_attributes = True


class StoryDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[StoryItemDetail] = []

    class Config:
        from_attributes = True


class StoryItemCreate(BaseModel):
    generation_id: str
    start_time_ms: Optional[int] = None
    track: Optional[int] = 0


class StoryItemUpdateTime(BaseModel):
    generation_id: str
    start_time_ms: int = Field(..., ge=0)


class StoryItemBatchUpdate(BaseModel):
    updates: list[StoryItemUpdateTime]


class StoryItemReorder(BaseModel):
    generation_ids: list[str] = Field(..., min_length=1)


class StoryItemMove(BaseModel):
    start_time_ms: int = Field(..., ge=0)
    track: int = 0


class StoryItemTrim(BaseModel):
    trim_start_ms: int = Field(..., ge=0)
    trim_end_ms: int = Field(..., ge=0)


class StoryItemSplit(BaseModel):
    split_time_ms: int = Field(..., ge=0)


class StoryItemVersionUpdate(BaseModel):
    version_id: Optional[str] = None


class StoryItemVolumeUpdate(BaseModel):
    volume: float = Field(..., ge=0.0, le=2.0)


class EffectsChain(BaseModel):
    effects: list[EffectConfig] = Field(default_factory=list)


class EffectPresetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    effects_chain: list[EffectConfig]


class EffectPresetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    effects_chain: Optional[list[EffectConfig]] = None


class EffectPresetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    effects_chain: list[EffectConfig]
    is_builtin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ApplyEffectsRequest(BaseModel):
    effects_chain: list[EffectConfig]
    source_version_id: Optional[str] = None
    label: Optional[str] = Field(None, max_length=100)
    set_as_default: bool = True


class ProfileEffectsUpdate(BaseModel):
    effects_chain: Optional[list[EffectConfig]] = None


class AvailableEffectParam(BaseModel):
    default: float
    min: float
    max: float
    step: float
    description: str


class AvailableEffect(BaseModel):
    type: str
    label: str
    description: str
    params: dict


class AvailableEffectsResponse(BaseModel):
    effects: list[AvailableEffect]
