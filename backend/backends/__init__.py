"""Backend registry for the single IndexTTS2 TTS engine."""

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Tuple
from typing_extensions import runtime_checkable

import numpy as np

from ..utils import hf_offline_patch  # noqa: F401


@dataclass
class ModelConfig:
    model_name: str
    display_name: str
    engine: str
    hf_repo_id: str
    model_size: str = "default"
    size_mb: int = 0
    needs_trim: bool = False
    supports_instruct: bool = False
    languages: list[str] = field(default_factory=lambda: ["zh", "en"])


@runtime_checkable
class TTSBackend(Protocol):
    async def load_model(self, model_size: str = "default") -> None:
        ...

    async def create_voice_prompt(
        self,
        audio_path: str,
        reference_text: str,
        use_cache: bool = True,
    ) -> Tuple[dict, bool]:
        ...

    async def combine_voice_prompts(
        self,
        audio_paths: List[str],
        reference_texts: List[str],
    ) -> Tuple[np.ndarray, str]:
        ...

    async def generate(
        self,
        text: str,
        voice_prompt: dict,
        language: str = "en",
        seed: Optional[int] = None,
        instruct: Optional[str] = None,
    ) -> Tuple[np.ndarray, int]:
        ...

    def unload_model(self) -> None:
        ...

    def is_loaded(self) -> bool:
        ...

    def _get_model_path(self, model_size: str = "default") -> str:
        ...


TTS_ENGINES = {"indextts2": "IndexTTS2"}
INDEXTTS2_REPO_ID = "IndexTeam/IndexTTS-2"

_tts_backends: dict[str, TTSBackend] = {}
_tts_backends_lock = threading.Lock()


def _get_indextts2_configs() -> list[ModelConfig]:
    return [
        ModelConfig(
            model_name="indextts2",
            display_name="IndexTTS2",
            engine="indextts2",
            hf_repo_id=INDEXTTS2_REPO_ID,
            size_mb=7000,
            languages=["zh", "en"],
        )
    ]


def get_all_model_configs() -> list[ModelConfig]:
    return _get_indextts2_configs()


def get_tts_model_configs() -> list[ModelConfig]:
    return _get_indextts2_configs()


def get_llm_model_configs() -> list[ModelConfig]:
    return []


def get_stt_model_configs() -> list[ModelConfig]:
    return []


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    for cfg in get_all_model_configs():
        if cfg.model_name == model_name:
            return cfg
    return None


def engine_needs_trim(engine: str) -> bool:
    return False


def engine_has_model_sizes(engine: str) -> bool:
    return False


async def load_engine_model(engine: str = "indextts2", model_size: str = "default") -> None:
    if engine != "indextts2":
        raise ValueError("IndexTTS2 is the only supported TTS engine")
    await get_tts_backend().load_model(model_size)


async def ensure_model_cached_or_raise(engine: str = "indextts2", model_size: str = "default") -> None:
    from fastapi import HTTPException

    if engine != "indextts2":
        raise HTTPException(status_code=400, detail="IndexTTS2 is the only supported TTS engine")
    backend = get_tts_backend()
    if not backend._is_model_cached(model_size):  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail="IndexTTS2 model is not downloaded yet. Use /models/download first.")


def unload_model_by_config(config: ModelConfig) -> bool:
    if config.model_name != "indextts2":
        return False
    backend = get_tts_backend()
    was_loaded = backend.is_loaded()
    backend.unload_model()
    return was_loaded


def check_model_loaded(config: ModelConfig) -> bool:
    if config.model_name != "indextts2":
        return False
    return get_tts_backend().is_loaded()


def get_model_load_func(config: ModelConfig):
    if config.model_name != "indextts2":
        raise ValueError("IndexTTS2 is the only supported model")
    return lambda: get_tts_backend().load_model()


def get_tts_backend() -> TTSBackend:
    return get_tts_backend_for_engine("indextts2")


def get_tts_backend_for_engine(engine: str) -> TTSBackend:
    if engine != "indextts2":
        raise ValueError("IndexTTS2 is the only supported TTS engine")

    if engine in _tts_backends:
        return _tts_backends[engine]

    with _tts_backends_lock:
        if engine in _tts_backends:
            return _tts_backends[engine]
        from .indextts2_backend import IndexTTS2Backend

        backend = IndexTTS2Backend()
        _tts_backends[engine] = backend
        return backend


def reset_backends() -> None:
    _tts_backends.clear()
