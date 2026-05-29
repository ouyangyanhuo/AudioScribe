# Voicebox Agent Notes

## Project Overview

Voicebox is a local-first AI voice studio. The desktop app is built with Tauri
and React, the backend is a FastAPI Python service, and production desktop
builds run the backend as a PyInstaller sidecar.

Main workspaces:

- `backend/`: FastAPI app, model registry, TTS/STT/LLM services, SQLite models.
- `app/`: Shared React UI used by the desktop frontend.
- `tauri/`: Tauri desktop shell, Rust commands, sidecar lifecycle, OS integration.
- `web/`: Browser-only Vite entrypoint using the shared app code.
- `landing/`: Marketing/download site.
- `docs/`: Documentation site and developer docs.
- `scripts/`: Build/release helper scripts.
- `data/`: Default development data directory.

## Development Commands

Use the `justfile` as the source of truth.

- `just setup`: create `backend/venv`, install Python dependencies, install JS deps.
- `just dev`: start the backend on port `17493` and run the Tauri app.
- `just dev-backend`: backend only.
- `just dev-frontend`: Tauri frontend only; backend must already be running.
- `just dev-web`: backend plus browser Vite app.
- `just check`: JS/TS checks plus Python ruff checks.
- `just test`: run backend pytest suite.
- `just build`: build CPU server sidecar plus Tauri installer.
- `just build-local`: Windows local build with CPU sidecar, CUDA backend, and Tauri installer.

On Windows, these commands run through PowerShell. No WSL or Git Bash is
required for the normal workflow.

## Runtime Data Storage

The backend data directory is configured in `backend/config.py`.

Default development path:

- `F:/Project/voicebox/data` when launched from the repository without
  `--data-dir`.

Production desktop path:

- Tauri passes its `app_data_dir()` to the sidecar with `--data-dir`.
- With app identifier `sh.voicebox.app`, this is typically:
  `%APPDATA%/sh.voicebox.app`

Data directory contents:

- `voicebox.db`: SQLite database.
- `profiles/<profile_id>/`: reference voice samples and avatars.
- `generations/`: generated TTS WAV files and generation versions.
- `captures/`: dictation/recording/upload audio used for STT.
- `cache/`: voice prompt cache files such as `*.prompt` and combined sample WAVs.
- `backends/cuda/`: downloaded CUDA backend onedir bundle.
- `logs/`: runtime logs in packaged/server paths that create logs.

Database paths are stored through `config.to_storage_path()` and resolved with
`config.resolve_storage_path()`, so new persisted files should generally be
stored relative to the configured data directory.

## Model Storage

HuggingFace model downloads use the HuggingFace Hub cache, not `data/models`,
unless explicitly overridden.

Default model cache:

- Windows: `%USERPROFILE%/.cache/huggingface/hub`
- macOS/Linux: `~/.cache/huggingface/hub`
- Docker: `/home/voicebox/.cache/huggingface/hub`

Override:

- Set `VOICEBOX_MODELS_DIR` to an absolute path before server startup.
- `backend/config.py` maps this to `HF_HUB_CACHE`.
- Tauri can pass a custom models directory when starting/restarting the server.

Relevant APIs:

- `GET /models/cache-dir`: returns current HuggingFace cache path.
- `GET /models/status`: scans registered model repos and loaded state.
- `POST /models/download`: triggers background model download.
- `GET /models/progress/{model_name}`: SSE progress stream.
- `DELETE /models/{model_name}`: deletes the corresponding HF repo cache.
- `POST /models/migrate`: moves cached HF model repo directories to a new path.

Model metadata is centralized in `backend/backends/__init__.py` as
`ModelConfig` entries. New engines should follow the local backend registry
pattern instead of adding route-level branching.

## CUDA Backend Storage and Switching

CUDA support is intentionally not bundled into the main installer because the
NVIDIA runtime libraries are large.

The CUDA backend is downloaded on demand from GitHub Releases by
`backend/services/cuda.py` as two archives:

- `voicebox-server-cuda.tar.gz`: server core, versioned with the app.
- `cuda-libs-cu128-v1.tar.gz`: NVIDIA CUDA/cuDNN runtime libraries, versioned
  independently.

Both are extracted into:

- `{data_dir}/backends/cuda/`
- On installed Windows builds, typically:
  `%APPDATA%/sh.voicebox.app/backends/cuda/`

Expected Windows executable:

- `{data_dir}/backends/cuda/voicebox-server-cuda.exe`

The Tauri launcher checks this directory on startup. If the CUDA binary exists
and `voicebox-server-cuda.exe --version` matches the app version, Tauri launches
it with the CUDA directory as the current working directory. Otherwise it falls
back to the bundled CPU sidecar.

Relevant APIs:

- `GET /backend/cuda-status`
- `POST /backend/download-cuda`
- `GET /backend/cuda-progress`
- `DELETE /backend/cuda`

For local Windows testing, `just build-server-cuda` builds the CUDA onedir
bundle and copies it to `%APPDATA%/sh.voicebox.app/backends/cuda`.

## Windows Development Notes

Prerequisites:

- Python 3.11+ or 3.12 preferred for ML dependency compatibility.
- Bun.
- Rust toolchain and Tauri prerequisites.
- `just` command runner.
- Visual Studio Build Tools may be needed for native Python/Rust dependencies.

Setup:

```powershell
just setup
```

On Windows, `just setup` detects GPUs:

- NVIDIA: installs CUDA PyTorch from `https://download.pytorch.org/whl/cu128`.
- Intel Arc: installs XPU PyTorch and `intel-extension-for-pytorch`.
- Otherwise: uses CPU PyTorch.

Run desktop development:

```powershell
just dev
```

Run backend only:

```powershell
just dev-backend
```

Run web-only development:

```powershell
just dev-web
```

Backend URL:

- `http://127.0.0.1:17493`
- API docs: `http://127.0.0.1:17493/docs`

Useful validation:

```powershell
just check
just test
```

Build paths:

- CPU sidecar build output starts in `backend/dist/voicebox-server.exe`.
- Tauri sidecar copy target is `tauri/src-tauri/binaries/voicebox-server-<triple>.exe`.
- Tauri installer output is under `tauri/src-tauri/target/release/bundle/`.
- CUDA local test output is copied to `%APPDATA%/sh.voicebox.app/backends/cuda/`.

## Implementation Guidelines for Future Agents

- Prefer existing service/backend registry patterns over adding special cases
  in routes.
- Keep persisted user data under `config.get_data_dir()` helpers.
- Store database file paths with `config.to_storage_path()`.
- Resolve database paths with `config.resolve_storage_path()`.
- Use HuggingFace APIs and the existing progress tracker for model downloads.
- Avoid deleting user data, model caches, or CUDA backends unless the request
  explicitly asks for it.
- Use `apply_patch` for manual file edits.
- Run focused tests for backend behavior changes and `just check` when scope is
  broad enough to affect both Python and TypeScript.
