from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class WorkerGenerateRequest:
    install_dir: str
    cache_dir: str
    model_dir: str
    cfg_path: str
    speaker_audio: str
    text: str
    output_path: str
    emo_audio_prompt: str | None = None
    emo_alpha: float = 1.0
    emo_vector: list[float] | None = None
    use_emo_text: bool = False
    emo_text: str | None = None
    use_random: bool = False
    interval_silence: int = 200
    max_text_tokens_per_segment: int = 120
    settings: dict = field(default_factory=dict)


_TTS = None
_TTS_KEY: tuple[str, str, str, bool, bool, bool] | None = None
_TTS_LOCK = threading.Lock()


def create_app():
    from fastapi import Body, FastAPI

    app = FastAPI(title="AudioScribe IndexTTS2 Worker")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "healthy",
            "engine": "indextts2",
            "worker_protocol": 2,
            "state": "ready",
            "model_loaded": _TTS is not None,
        }

    @app.post("/generate")
    def generate(payload: dict = Body(...)) -> dict[str, str]:
        request = WorkerGenerateRequest(**payload)
        run_generation(request)
        return {"status": "completed", "output_path": request.output_path}

    return app


def _force_install_local_env(install_dir: Path, cache_dir: Path, model_dir: Path) -> None:
    hf_cache = cache_dir / "huggingface"
    env = {
        "AUDIOSCRIBE_INSTALL_DIR": str(install_dir),
        "AUDIOSCRIBE_WORKER_CACHE": str(cache_dir / "indextts2"),
        "MODELSCOPE_CACHE": str(model_dir.parent),
        "HF_HOME": str(hf_cache),
        "HF_HUB_CACHE": str(hf_cache / "hub"),
        "HUGGINGFACE_HUB_CACHE": str(hf_cache / "hub"),
        "TRANSFORMERS_CACHE": str(cache_dir / "transformers"),
        "TORCH_HOME": str(cache_dir / "torch"),
        "TEMP": str(cache_dir / "tmp"),
        "TMP": str(cache_dir / "tmp"),
    }
    for key, value in env.items():
        if key in {"TEMP", "TMP"} or key.endswith("CACHE") or key.endswith("HOME") or key.endswith("DIR"):
            Path(value).mkdir(parents=True, exist_ok=True)
    os.environ.update(env)


def _patch_huggingface_cache(cache_dir: Path) -> None:
    try:
        import huggingface_hub.constants as constants

        hub_cache = str(cache_dir / "huggingface" / "hub")
        constants.HF_HUB_CACHE = hub_cache
        constants.HUGGINGFACE_HUB_CACHE = hub_cache
    except Exception:
        pass


def _get_tts(payload: WorkerGenerateRequest, cache_dir: Path):
    global _TTS, _TTS_KEY

    # Import after forcing env. infer_v2 currently sets HF_HUB_CACHE internally,
    # so patch huggingface constants again immediately after import.
    from indextts.infer_v2 import IndexTTS2

    _patch_huggingface_cache(cache_dir)

    settings = payload.settings or {}
    if settings.get("use_deepspeed", False) and os.name == "nt":
        raise RuntimeError("DeepSpeed is not supported on native Windows. Use CUDA PyTorch acceleration instead.")

    device = "cuda:0" if settings.get("gpu_mode") == "cuda" else "cpu"
    if settings.get("gpu_mode") == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA mode is enabled, but worker PyTorch cannot access CUDA.")

    key = (
        str(Path(payload.cfg_path).resolve()),
        str(Path(payload.model_dir).resolve()),
        device,
        bool(settings.get("use_fp16", False)),
        bool(settings.get("use_cuda_kernel", False)),
        bool(settings.get("use_deepspeed", False)),
    )
    with _TTS_LOCK:
        if _TTS is None or _TTS_KEY != key:
            _TTS = IndexTTS2(
                cfg_path=payload.cfg_path,
                model_dir=payload.model_dir,
                device=device,
                use_fp16=bool(settings.get("use_fp16", False)),
                use_cuda_kernel=bool(settings.get("use_cuda_kernel", False)),
                use_deepspeed=bool(settings.get("use_deepspeed", False)),
            )
            _TTS_KEY = key
        return _TTS


def run_generation(payload: WorkerGenerateRequest) -> None:
    install_dir = Path(payload.install_dir).resolve()
    cache_dir = Path(payload.cache_dir).resolve()
    model_dir = Path(payload.model_dir).resolve()
    _force_install_local_env(install_dir, cache_dir, model_dir)

    import numpy as np

    major = int(np.__version__.split(".", 1)[0])
    if major >= 2:
        raise RuntimeError(
            f"IndexTTS2 worker has NumPy {np.__version__}, but this runtime requires numpy<2. "
            "Open Settings and reinstall the IndexTTS2 CPU or CUDA runtime."
        )

    tts = _get_tts(payload, cache_dir)
    result = tts.infer(
        spk_audio_prompt=payload.speaker_audio,
        text=payload.text,
        output_path=payload.output_path,
        emo_audio_prompt=payload.emo_audio_prompt,
        emo_alpha=payload.emo_alpha,
        emo_vector=payload.emo_vector,
        use_emo_text=payload.use_emo_text,
        emo_text=payload.emo_text,
        use_random=payload.use_random,
        interval_silence=payload.interval_silence,
        max_text_tokens_per_segment=payload.max_text_tokens_per_segment,
        verbose=True,
    )
    if result is None or not Path(payload.output_path).exists():
        raise RuntimeError("IndexTTS2 did not produce an audio file.")


def _load_payload(path: Path) -> WorkerGenerateRequest:
    return WorkerGenerateRequest(**json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", type=Path)
    args = parser.parse_args()
    if not args.generate:
        import uvicorn

        uvicorn.run(
            create_app(),
            host="127.0.0.1",
            port=int(os.environ.get("AUDIOSCRIBE_INDEXTTS2_PORT", "17495")),
        )
        return 0

    try:
        payload = _load_payload(args.generate)
        run_generation(payload)
        print(json.dumps({"status": "completed", "output_path": payload.output_path}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
