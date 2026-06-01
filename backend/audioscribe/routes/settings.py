from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Request

from ..config import RuntimePaths
from ..database import connect
from ..schemas import InstallStatus, RuntimeInstallRequest, RuntimePathSummary, SettingsResponse, SettingsUpdate

router = APIRouter()

_install_lock = threading.Lock()
_install_state: dict[str, object] = {
    "installing": False,
    "package": None,
    "message": None,
    "log": None,
    "error": None,
    "done": False,
}


def _worker_env(paths: RuntimePaths) -> dict[str, str]:
    env = os.environ.copy()
    env["AUDIOSCRIBE_INSTALL_DIR"] = str(paths.install_dir)
    env["AUDIOSCRIBE_WORKER_CACHE"] = str(paths.worker_cache_dir)
    env["MODELSCOPE_CACHE"] = str(paths.modelscope_model_dir)
    env["HF_HOME"] = str(paths.huggingface_cache_dir)
    env["HF_HUB_CACHE"] = str(paths.huggingface_cache_dir / "hub")
    env["HUGGINGFACE_HUB_CACHE"] = str(paths.huggingface_cache_dir / "hub")
    env["TRANSFORMERS_CACHE"] = str(paths.cache_dir / "transformers")
    env["TORCH_HOME"] = str(paths.cache_dir / "torch")
    env["UV_CACHE_DIR"] = str(paths.cache_dir / "uv")
    env["PIP_CACHE_DIR"] = str(paths.cache_dir / "pip")
    env["TEMP"] = str(paths.temp_dir)
    env["TMP"] = str(paths.temp_dir)
    for key in ("AUDIOSCRIBE_WORKER_CACHE", "MODELSCOPE_CACHE", "HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "TORCH_HOME", "UV_CACHE_DIR", "PIP_CACHE_DIR", "TEMP"):
        from pathlib import Path

        Path(env[key]).mkdir(parents=True, exist_ok=True)
    return env


def _creation_flags() -> int:
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _worker_probe(paths: RuntimePaths) -> dict[str, object]:
    python = _worker_python(paths)
    if not os.path.exists(python):
        return {
            "cuda_available": False,
            "deepspeed_available": False,
            "worker_runtime_installed": False,
            "worker_python": python,
            "gpu_message": f"IndexTTS2 worker runtime is not installed: {python}",
        }

    code = (
        "import json\n"
        "result={'cuda_available':False,'deepspeed_available':False,'cuda_device_name':None,'cuda_torch_version':None,'cuda_version':None,'worker_runtime_installed':True,'worker_python':None,'worker_numpy_version':None,'gpu_message':None}\n"
        "import sys\n"
        "result['worker_python']=sys.executable\n"
        "try:\n"
        " import numpy\n"
        " result['worker_numpy_version']=getattr(numpy,'__version__',None)\n"
        " if int(result['worker_numpy_version'].split('.',1)[0]) >= 2:\n"
        "  result['gpu_message']=f'IndexTTS2 worker requires numpy<2, current version is {result[\"worker_numpy_version\"]}. Reinstall the CPU or CUDA runtime.'\n"
        "except Exception as exc:\n"
        " result['gpu_message']=f'numpy check failed: {exc}'\n"
        "try:\n"
        " import torch\n"
        " result['cuda_torch_version']=getattr(torch,'__version__',None)\n"
        " result['cuda_version']=getattr(getattr(torch,'version',None),'cuda',None)\n"
        " result['cuda_available']=bool(torch.cuda.is_available())\n"
        " if result['cuda_available']:\n"
        "  result['cuda_device_name']=torch.cuda.get_device_name(0)\n"
        "except Exception as exc:\n"
        " result['gpu_message']=f'torch check failed: {exc}'\n"
        "try:\n"
        " import deepspeed\n"
        " result['deepspeed_available']=True\n"
        "except Exception:\n"
        " pass\n"
        "print(json.dumps(result, ensure_ascii=False))\n"
    )
    try:
        completed = subprocess.run(
            [python, "-c", code],
            cwd=str(paths.install_dir),
            env=_worker_env(paths),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
            creationflags=_creation_flags(),
        )
        if completed.returncode != 0:
            return {
                "cuda_available": False,
                "deepspeed_available": False,
                "gpu_message": (completed.stderr or completed.stdout or "worker probe failed").strip()[-1000:],
            }
        return json.loads(completed.stdout.strip() or "{}")
    except Exception as exc:
        return {"cuda_available": False, "deepspeed_available": False, "gpu_message": str(exc)}


def _worker_python(paths: RuntimePaths) -> str:
    explicit = os.environ.get("AUDIOSCRIBE_INDEXTTS2_PYTHON")
    if explicit:
        return explicit
    venv = _worker_root(paths) / ".venv"
    if os.name == "nt":
        return str(venv / "Scripts" / "python.exe")
    return str(venv / "bin" / "python")


def _worker_root(paths: RuntimePaths) -> Path:
    candidates = [
        paths.install_dir / "backend" / "indextts2_worker",
        paths.install_dir / "resources" / "backend" / "indextts2_worker",
    ]
    for candidate in candidates:
        if (candidate / "worker.py").exists() or (candidate / "requirements.txt").exists():
            return candidate
    return candidates[0]


def _bootstrap_python(paths: RuntimePaths) -> str:
    explicit = os.environ.get("AUDIOSCRIBE_RUNTIME_PYTHON")
    if explicit:
        return explicit
    bundled = paths.install_dir / "runtime" / "python"
    if os.name == "nt":
        candidate = bundled / "python.exe"
    else:
        candidate = bundled / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    if not getattr(sys, "frozen", False):
        return sys.executable
    raise RuntimeError(
        f"Bundled Python runtime is missing: {candidate}. "
        "Packaged builds must include install-local runtime/python before client-side worker installation can run."
    )


def _uv_executable(paths: RuntimePaths) -> str:
    explicit = os.environ.get("AUDIOSCRIBE_UV_BIN")
    if explicit:
        return explicit
    bundled = paths.install_dir / "runtime" / "uv" / ("uv.exe" if os.name == "nt" else "uv")
    if bundled.exists():
        return str(bundled)
    uv = shutil.which("uv")
    if uv:
        return uv
    raise RuntimeError("uv was not found. Packaged builds must include install-local runtime/uv/uv.exe.")


def _ensure_worker_venv(paths: RuntimePaths) -> None:
    python = _worker_python(paths)
    if os.path.exists(python):
        return
    bootstrap = _bootstrap_python(paths)
    worker_root = _worker_root(paths)
    worker_root.mkdir(parents=True, exist_ok=True)
    venv_dir = worker_root / ".venv"
    subprocess.run(
        [bootstrap, "-m", "venv", str(venv_dir)],
        cwd=str(paths.install_dir),
        env=_worker_env(paths),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60 * 10,
        check=True,
        creationflags=_creation_flags(),
    )
    if not os.path.exists(python):
        raise RuntimeError(f"Worker venv was created with {bootstrap}, but Python is missing: {python}")


def _worker_requirements(paths: RuntimePaths) -> Path:
    path = _worker_root(paths) / "requirements.txt"
    if path.exists():
        return path
    dev_path = Path(__file__).resolve().parents[2] / "indextts2_worker" / "requirements.txt"
    if dev_path.exists():
        return dev_path
    raise RuntimeError(f"IndexTTS2 worker requirements file is missing: {path}")


def _set_install_state(**kwargs) -> None:
    with _install_lock:
        for k, v in kwargs.items():
            _install_state[k] = v


def _run_install(pip_args: list[str], package_label: str, paths: RuntimePaths, extra_env: dict[str, str] | None = None) -> None:
    python = _worker_python(paths)
    env = _worker_env(paths)
    if extra_env:
        env.update(extra_env)
    _set_install_state(
        installing=True, package=package_label, message=f"Installing {package_label}...",
        log="", error=None, done=False,
    )
    try:
        if not os.path.exists(python):
            raise RuntimeError(
                f"IndexTTS2 worker runtime is not installed: {python}. Run `just setup-indextts2` first."
            )
        uv = _uv_executable(paths)
        proc = subprocess.run(
            [uv, "pip", "install", "--python", python, *pip_args],
            cwd=str(paths.install_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60 * 30,
            check=False,
            creationflags=_creation_flags(),
        )
        output = (proc.stdout or "")[-4000:]
        if proc.returncode != 0:
            _set_install_state(
                installing=False, package=package_label, message=f"{package_label} installation failed.",
                log=output, error=f"pip exited with code {proc.returncode}", done=True,
            )
        else:
            _set_install_state(
                installing=False, package=package_label, message=f"{package_label} installed successfully.",
                log=output, error=None, done=True,
            )
    except subprocess.TimeoutExpired:
        _set_install_state(
            installing=False, package=package_label, message=f"{package_label} installation timed out.",
            log=None, error="Timeout after 30 minutes", done=True,
        )
    except Exception as exc:
        _set_install_state(
            installing=False, package=package_label, message=f"{package_label} installation failed.",
            log=None, error=str(exc), done=True,
        )


def _run_runtime_install(variant: str, cuda_channel: str, paths: RuntimePaths) -> None:
    label = "IndexTTS2 CUDA runtime" if variant == "cuda" else "IndexTTS2 CPU runtime"
    _set_install_state(
        installing=True, package=label, message=f"Installing {label}...",
        log="", error=None, done=False,
    )
    try:
        _ensure_worker_venv(paths)
        python = _worker_python(paths)
        uv = _uv_executable(paths)

        requirements = _worker_requirements(paths)
        commands = [
            [uv, "pip", "install", "--python", python, "-r", str(requirements)],
        ]
        if variant == "cuda":
            commands.append([
                uv,
                "pip",
                "install",
                "--python",
                python,
                "--reinstall",
                "torch",
                "torchvision",
                "torchaudio",
                "--index-url",
                f"https://download.pytorch.org/whl/{cuda_channel}",
            ])
        else:
            commands.append([
                uv,
                "pip",
                "install",
                "--python",
                python,
                "--reinstall",
                "torch",
                "torchvision",
                "torchaudio",
                "--index-url",
                "https://download.pytorch.org/whl/cpu",
            ])

        logs: list[str] = []
        for command in commands:
            proc = subprocess.run(
                command,
                cwd=str(paths.install_dir),
                env=_worker_env(paths),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60 * 45,
                check=False,
                creationflags=_creation_flags(),
            )
            logs.append(proc.stdout or "")
            _set_install_state(log="\n".join(logs)[-5000:])
            if proc.returncode != 0:
                raise RuntimeError(f"{Path(command[0]).name} exited with code {proc.returncode}")

        probe = _worker_probe(paths)
        if variant == "cuda" and not probe.get("cuda_available"):
            raise RuntimeError(probe.get("gpu_message") or "CUDA runtime installed, but torch.cuda.is_available() is false.")
        with connect(paths.database_path) as conn:
            if variant == "cuda":
                conn.execute(
                    """
                    UPDATE settings
                    SET gpu_mode = 'cuda', use_fp16 = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                    """
                )
            else:
                conn.execute(
                    """
                    UPDATE settings
                    SET gpu_mode = 'cpu', use_fp16 = 0, use_cuda_kernel = 0, use_deepspeed = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                    """
                )
        _set_install_state(
            installing=False, package=label, message=f"{label} installed successfully.",
            log="\n".join(logs)[-5000:], error=None, done=True,
        )
    except subprocess.TimeoutExpired:
        _set_install_state(
            installing=False, package=label, message=f"{label} installation timed out.",
            log=None, error="Timeout during runtime installation", done=True,
        )
    except Exception as exc:
        _set_install_state(
            installing=False, package=label, message=f"{label} installation failed.",
            log=_install_state.get("log"), error=str(exc), done=True,
        )


def _path_summary(request: Request) -> RuntimePathSummary:
    paths = request.app.state.paths
    return RuntimePathSummary(
        install_dir=str(paths.install_dir),
        data_dir=str(paths.data_dir),
        cache_dir=str(paths.cache_dir),
        model_dir=str(paths.model_dir),
        logs_dir=str(paths.logs_dir),
        database_path=str(paths.database_path),
        generated_audio_dir=str(paths.generated_audio_dir),
        role_samples_dir=str(paths.role_samples_dir),
        preset_voice_dir=str(paths.preset_voice_dir),
        temp_dir=str(paths.temp_dir),
    )


def _get_install_status() -> InstallStatus | None:
    with _install_lock:
        if not _install_state["installing"] and not _install_state["done"]:
            return None
        return InstallStatus(**_install_state)


def _row_to_settings(request: Request, row) -> SettingsResponse:
    paths = request.app.state.paths
    probe = _worker_probe(paths)
    deepspeed_supported = os.name != "nt"
    gpu_message = probe.get("gpu_message")
    if os.name == "nt" and row["use_deepspeed"]:
        gpu_message = "DeepSpeed is not supported on native Windows. Use CUDA PyTorch acceleration instead."
    return SettingsResponse(
        model_source="modelscope",
        github_mirror_enabled=bool(row["github_mirror_enabled"]),
        gpu_mode=row["gpu_mode"],
        use_fp16=bool(row["use_fp16"]),
        use_cuda_kernel=bool(row["use_cuda_kernel"]),
        use_deepspeed=bool(row["use_deepspeed"]) and deepspeed_supported,
        paths=_path_summary(request),
        cuda_available=bool(probe.get("cuda_available", False)),
        cuda_runtime_installed=bool(probe.get("cuda_version")),
        cuda_device_name=probe.get("cuda_device_name"),
        cuda_torch_version=probe.get("cuda_torch_version"),
        cuda_version=probe.get("cuda_version"),
        deepspeed_available=bool(probe.get("deepspeed_available", False)),
        deepspeed_supported=deepspeed_supported,
        worker_runtime_installed=bool(probe.get("worker_runtime_installed", False)),
        worker_python=probe.get("worker_python") or str(_worker_python(paths)),
        worker_numpy_version=probe.get("worker_numpy_version"),
        gpu_message=gpu_message,
        install_status=_get_install_status(),
    )


@router.get("", response_model=SettingsResponse)
def get_settings(request: Request) -> SettingsResponse:
    with connect(request.app.state.paths.database_path) as conn:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return _row_to_settings(request, row)


@router.put("", response_model=SettingsResponse)
def update_settings(request: Request, patch: SettingsUpdate = Body(...)) -> SettingsResponse:
    fields = patch.model_dump(exclude_unset=True)
    if fields.get("gpu_mode") == "cuda":
        probe = _worker_probe(request.app.state.paths)
        if not probe.get("cuda_available"):
            raise HTTPException(
                status_code=400,
                detail=probe.get("gpu_message") or "CUDA is not available in the IndexTTS2 worker runtime.",
            )
    if fields.get("use_deepspeed") and os.name == "nt":
        raise HTTPException(
            status_code=400,
            detail="DeepSpeed is not supported on native Windows. Use CUDA PyTorch acceleration instead.",
        )
    if fields:
        values = {
            key: int(value) if isinstance(value, bool) else value
            for key, value in fields.items()
        }
        assignments = ", ".join(f"{key} = :{key}" for key in values)
        with connect(request.app.state.paths.database_path) as conn:
            conn.execute(
                f"UPDATE settings SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
                values,
            )
    return get_settings(request)


@router.post("/uninstall-cuda", response_model=SettingsResponse)
def uninstall_cuda_runtime(request: Request, background_tasks: BackgroundTasks) -> SettingsResponse:
    with _install_lock:
        if _install_state["installing"]:
            raise HTTPException(status_code=409, detail="Another installation is in progress.")
    _set_install_state(done=False)
    background_tasks.add_task(
        _run_runtime_install,
        "cpu",
        "cu124",
        request.app.state.paths,
    )
    return get_settings(request)


@router.post("/install-cuda-torch", response_model=SettingsResponse)
def install_cuda_torch(request: Request, background_tasks: BackgroundTasks) -> SettingsResponse:
    with _install_lock:
        if _install_state["installing"]:
            raise HTTPException(status_code=409, detail="Another installation is in progress.")
    _set_install_state(done=False)
    background_tasks.add_task(
        _run_runtime_install,
        "cuda",
        "cu124",
        request.app.state.paths,
    )
    return get_settings(request)


@router.post("/install-runtime", response_model=SettingsResponse)
def install_runtime(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: RuntimeInstallRequest = Body(...),
) -> SettingsResponse:
    with _install_lock:
        if _install_state["installing"]:
            raise HTTPException(status_code=409, detail="Another installation is in progress.")
    _set_install_state(done=False)
    background_tasks.add_task(
        _run_runtime_install,
        payload.variant,
        payload.cuda_channel,
        request.app.state.paths,
    )
    return get_settings(request)


@router.post("/install-runtime/{variant}", response_model=SettingsResponse)
def install_runtime_variant(
    request: Request,
    background_tasks: BackgroundTasks,
    variant: str,
    cuda_channel: str = "cu124",
) -> SettingsResponse:
    if variant not in {"cpu", "cuda"}:
        raise HTTPException(status_code=400, detail="Runtime variant must be cpu or cuda.")
    if cuda_channel not in {"cu121", "cu124", "cu126"}:
        raise HTTPException(status_code=400, detail="CUDA channel must be cu121, cu124, or cu126.")
    with _install_lock:
        if _install_state["installing"]:
            raise HTTPException(status_code=409, detail="Another installation is in progress.")
    _set_install_state(done=False)
    background_tasks.add_task(
        _run_runtime_install,
        variant,
        cuda_channel,
        request.app.state.paths,
    )
    return get_settings(request)


@router.post("/install-deepspeed", response_model=SettingsResponse)
def install_deepspeed(request: Request, background_tasks: BackgroundTasks) -> SettingsResponse:
    if os.name == "nt":
        raise HTTPException(
            status_code=400,
            detail="DeepSpeed is not supported on native Windows. Use CUDA PyTorch acceleration instead.",
        )
    with _install_lock:
        if _install_state["installing"]:
            raise HTTPException(status_code=409, detail="Another installation is in progress.")
    _set_install_state(done=False)
    background_tasks.add_task(
        _run_install,
        ["--reinstall", "deepspeed"],
        "DeepSpeed",
        request.app.state.paths,
        {"DS_BUILD_OPS": "0"},
    )
    return get_settings(request)
