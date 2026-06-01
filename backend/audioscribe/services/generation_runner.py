from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from ..config import RuntimePaths
from ..database import connect


class GenerationError(RuntimeError):
    pass


_worker_process: subprocess.Popen | None = None
_worker_lock = threading.Lock()


def _inside(base: Path, candidate: Path) -> bool:
    base = base.resolve()
    candidate = candidate.resolve()
    return candidate == base or base in candidate.parents


def _load_preset_audio(paths: RuntimePaths, preset_voice_id: str) -> Path:
    manifest_path = paths.preset_voice_dir / "manifest.json"
    if not manifest_path.exists():
        raise GenerationError("Preset voice manifest is empty. Add preset voices first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    item = next((row for row in manifest.get("items", []) if row.get("id") == preset_voice_id), None)
    if not item:
        raise GenerationError("Preset voice not found.")
    audio_path = (paths.preset_voice_dir / item["file"]).resolve()
    if not _inside(paths.preset_voice_dir, audio_path) or not audio_path.exists():
        raise GenerationError("Preset voice audio file is missing or outside the preset directory.")
    return audio_path


def _load_audio_library_item(paths: RuntimePaths, item_id: str) -> Path:
    with connect(paths.database_path) as conn:
        row = conn.execute("SELECT * FROM audio_library_items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        raise GenerationError("Uploaded reference audio not found.")
    audio_path = Path(row["audio_path"]).resolve()
    if not _inside(paths.install_dir, audio_path) or not audio_path.exists():
        raise GenerationError("Uploaded reference audio is missing or outside the install directory.")
    return audio_path


def resolve_reference_audio(paths: RuntimePaths, payload: Any) -> Path:
    if payload.audio_source == "preset":
        if not payload.preset_voice_id:
            raise GenerationError("Select a preset voice before generating.")
        return _load_preset_audio(paths, payload.preset_voice_id)

    if payload.audio_source == "upload":
        if not payload.uploaded_audio_id:
            raise GenerationError("Upload a reference audio file before generating.")
        return _load_audio_library_item(paths, payload.uploaded_audio_id)

    if payload.audio_source == "record":
        if not payload.recorded_audio_id:
            raise GenerationError("Record a reference audio file before generating.")
        return _load_audio_library_item(paths, payload.recorded_audio_id)

    if payload.audio_source == "role":
        if not payload.role_id:
            raise GenerationError("Select a role before generating.")
        with connect(paths.database_path) as conn:
            row = conn.execute(
                "SELECT audio_path FROM role_samples WHERE role_id = ? ORDER BY created_at DESC LIMIT 1",
                (payload.role_id,),
            ).fetchone()
        if not row:
            raise GenerationError("Selected role has no reference audio sample.")
        audio_path = Path(row["audio_path"]).resolve()
        if not _inside(paths.install_dir, audio_path) or not audio_path.exists():
            raise GenerationError("Role reference audio is missing or outside the install directory.")
        return audio_path

    raise GenerationError("Unsupported audio source.")


def _model_snapshot_dir(paths: RuntimePaths) -> Path:
    return paths.model_dir / "IndexTeam" / "IndexTTS-2"


def _worker_python(paths: RuntimePaths) -> Path:
    explicit = os.environ.get("AUDIOSCRIBE_INDEXTTS2_PYTHON")
    if explicit:
        return Path(explicit)

    worker_venv = _worker_root(paths) / ".venv"
    if os.name == "nt":
        return worker_venv / "Scripts" / "python.exe"
    return worker_venv / "bin" / "python"


def _worker_root(paths: RuntimePaths) -> Path:
    candidates = [
        paths.install_dir / "backend" / "indextts2_worker",
        paths.install_dir / "resources" / "backend" / "indextts2_worker",
    ]
    for candidate in candidates:
        if (candidate / "worker.py").exists() or (candidate / "requirements.txt").exists():
            return candidate
    return candidates[0]


def _job_env(paths: RuntimePaths) -> dict[str, str]:
    env = os.environ.copy()
    env["AUDIOSCRIBE_INSTALL_DIR"] = str(paths.install_dir)
    env["AUDIOSCRIBE_WORKER_CACHE"] = str(paths.worker_cache_dir)
    env["MODELSCOPE_CACHE"] = str(paths.modelscope_model_dir)
    env["HF_HOME"] = str(paths.huggingface_cache_dir)
    env["HF_HUB_CACHE"] = str(paths.huggingface_cache_dir / "hub")
    env["TRANSFORMERS_CACHE"] = str(paths.cache_dir / "transformers")
    env["TORCH_HOME"] = str(paths.cache_dir / "torch")
    env["TEMP"] = str(paths.cache_dir / "tmp")
    env["TMP"] = str(paths.cache_dir / "tmp")
    return env


def _creation_flags() -> int:
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _worker_port() -> int:
    return int(os.environ.get("AUDIOSCRIBE_INDEXTTS2_PORT", "17495"))


def _worker_base_url() -> str:
    return f"http://127.0.0.1:{_worker_port()}"


def _http_json(method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{_worker_base_url()}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GenerationError(detail or f"IndexTTS2 worker HTTP {exc.code}") from exc


def _worker_healthy() -> bool:
    try:
        data = _http_json("GET", "/health", timeout=1.0)
        return data.get("status") == "healthy" and data.get("worker_protocol") == 2
    except Exception:
        return False


def _ensure_worker_server(paths: RuntimePaths, worker_python: Path, worker_script: Path) -> None:
    global _worker_process

    if _worker_healthy():
        return

    with _worker_lock:
        if _worker_healthy():
            return
        if _worker_process is not None and _worker_process.poll() is None:
            _worker_process.terminate()

        paths.logs_dir.mkdir(parents=True, exist_ok=True)
        stdout = (paths.logs_dir / "indextts2-worker.out.log").open("a", encoding="utf-8")
        stderr = (paths.logs_dir / "indextts2-worker.err.log").open("a", encoding="utf-8")
        env = _job_env(paths)
        env["AUDIOSCRIBE_INDEXTTS2_PORT"] = str(_worker_port())
        _worker_process = subprocess.Popen(
            [str(worker_python), str(worker_script)],
            cwd=str(paths.install_dir),
            env=env,
            stdout=stdout,
            stderr=stderr,
            text=True,
            creationflags=_creation_flags(),
        )

    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if _worker_process is not None and _worker_process.poll() is not None:
            raise GenerationError(
                f"IndexTTS2 worker exited during startup with code {_worker_process.returncode}. "
                f"See {paths.logs_dir / 'indextts2-worker.err.log'}"
            )
        if _worker_healthy():
            return
        time.sleep(0.5)
    raise GenerationError(f"IndexTTS2 worker did not become ready within 90 seconds. See {paths.logs_dir}")


def _run_worker_generation(paths: RuntimePaths, worker_python: Path, worker_script: Path, job_payload: dict[str, Any]) -> None:
    _ensure_worker_server(paths, worker_python, worker_script)
    _http_json("POST", "/generate", job_payload, timeout=60 * 60)


def run_generation_task(paths: RuntimePaths, generation_id: str) -> None:
    with connect(paths.database_path) as conn:
        row = conn.execute("SELECT * FROM generations WHERE id = ?", (generation_id,)).fetchone()
    if not row:
        return

    output_path = paths.generated_audio_dir / f"{generation_id}.wav"
    snapshot_dir = _model_snapshot_dir(paths)
    cfg_path = snapshot_dir / "config.yaml"
    worker_python = _worker_python(paths)
    worker_script = _worker_root(paths) / "worker.py"

    try:
        if not worker_python.exists():
            raise GenerationError(
                f"IndexTTS2 worker runtime is not installed: {worker_python}. "
                "Create backend/indextts2_worker/.venv with uv sync before generating."
            )
        if not worker_script.exists():
            raise GenerationError(f"IndexTTS2 worker script is missing: {worker_script}")
        if not cfg_path.exists():
            raise GenerationError(
                f"IndexTTS2 ModelScope model is missing: {snapshot_dir}. Download IndexTeam/IndexTTS-2 first."
            )

        params = json.loads(row["parameters_snapshot"] or "{}")
        speaker_audio = Path(params["speaker_audio"]).resolve()
        if not _inside(paths.install_dir, speaker_audio) or not speaker_audio.exists():
            raise GenerationError("Reference audio is missing or outside the install directory.")

        with connect(paths.database_path) as conn:
            conn.execute(
                "UPDATE generations SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (generation_id,),
            )

        paths.worker_cache_dir.mkdir(parents=True, exist_ok=True)
        paths.generated_audio_dir.mkdir(parents=True, exist_ok=True)
        (paths.cache_dir / "tmp").mkdir(parents=True, exist_ok=True)
        job_payload = {
            "install_dir": str(paths.install_dir),
            "cache_dir": str(paths.cache_dir),
            "model_dir": str(snapshot_dir),
            "cfg_path": str(cfg_path),
            "speaker_audio": str(speaker_audio),
            "text": row["text"],
            "output_path": str(output_path),
            "emo_audio_prompt": params.get("emo_audio_prompt"),
            "emo_alpha": params.get("emo_alpha", 1.0),
            "emo_vector": params.get("emo_vector"),
            "use_emo_text": params.get("use_emo_text", False),
            "emo_text": params.get("emo_text"),
            "use_random": params.get("use_random", False),
            "interval_silence": params.get("interval_silence", 200),
            "max_text_tokens_per_segment": params.get("max_text_tokens_per_segment", 120),
            "settings": params.get("settings", {}),
        }
        job_path = paths.worker_cache_dir / f"{generation_id}.json"
        job_path.write_text(json.dumps(job_payload, ensure_ascii=False), encoding="utf-8")

        _run_worker_generation(paths, worker_python, worker_script, job_payload)
        if not output_path.exists():
            raise GenerationError("IndexTTS2 worker completed without creating an audio file.")

        version_id = str(uuid.uuid4())
        with connect(paths.database_path) as conn:
            conn.execute(
                """
                UPDATE generations
                SET status = 'completed', audio_path = ?, error = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(output_path), generation_id),
            )
            conn.execute(
                """
                INSERT INTO generation_versions (id, generation_id, audio_path, label, is_active)
                VALUES (?, ?, ?, 'Initial', 1)
                """,
                (version_id, generation_id, str(output_path)),
            )
    except Exception as exc:
        with connect(paths.database_path) as conn:
            conn.execute(
                """
                UPDATE generations
                SET status = 'failed', error = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(exc), generation_id),
            )
