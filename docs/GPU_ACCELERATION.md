# AudioScribe GPU Acceleration Strategy

## Windows policy

AudioScribe does not use DeepSpeed on native Windows. DeepSpeed is treated as unsupported because its build path is unstable on Windows and can break the isolated IndexTTS2 runtime.

The supported Windows acceleration path is:

1. NVIDIA driver installed by the user.
2. IndexTTS2 worker runtime installed from the client settings page.
3. CUDA-enabled PyTorch installed into the worker runtime from the client settings page.
3. AudioScribe setting `gpu_mode = "cuda"`.
4. Optional `use_fp16` after CUDA is confirmed working.

`use_cuda_kernel` is exposed as an advanced switch and should stay off unless the local IndexTTS2 runtime supports it.

## Install-local storage

All GPU package caches and temporary files must stay under the install directory:

- `<install>/cache/uv`
- `<install>/cache/pip`
- `<install>/cache/tmp`
- `<install>/backend/indextts2_worker/.venv`

No CUDA, PyTorch, uv, pip, model, or worker runtime cache may be written to user profile directories.

## Setup commands

Development command-line setup is still available:

```powershell
just setup-indextts2
```

Install CUDA-enabled PyTorch into the worker runtime:

```powershell
just setup-gpu
```

Packaged client setup is done in Settings:

1. Click `Install CPU Runtime` for CPU-only generation.
2. Click `Install CUDA Runtime` for GPU generation.
3. `Install CUDA Runtime` automatically switches `gpu_mode` to `CUDA` after `torch.cuda.is_available()` succeeds.
4. Click `Uninstall CUDA` to reinstall CPU PyTorch and switch generation back to CPU.

For packaged builds, the installer must include install-local bootstrap tools:

- `<install>/runtime/python/python.exe`
- `<install>/runtime/uv/uv.exe`
- `<install>/resources/backend/indextts2_worker/worker.py`
- `<install>/resources/backend/indextts2_worker/requirements.txt`

`just build` copies the worker files into Tauri resources. If `runtime/python` or `runtime/uv` exists in the project root, it is also copied into the bundle resources. Without those runtime bootstrap files, the client can show the install buttons but cannot create the worker environment after installation.

Alternative CUDA wheel channels:

```powershell
python scripts/setup_gpu.py --cuda cu121
python scripts/setup_gpu.py --cuda cu124
python scripts/setup_gpu.py --cuda cu126
```

## Runtime behavior

The backend checks CUDA from the worker Python, not from the main FastAPI environment. This avoids false negatives when the main backend is CPU-only but the IndexTTS2 worker has CUDA-enabled PyTorch.

The worker runtime pins `numpy<2` because IndexTTS2 imports matplotlib/bigvgan modules that can crash when NumPy 2.x is paired with extensions compiled against NumPy 1.x.

Generation uses a persistent local IndexTTS2 worker server on `127.0.0.1:17495`. The first generation still has to load the model, but later generations reuse the loaded `IndexTTS2` instance as long as the model path and GPU settings do not change. Changing `gpu_mode`, `use_fp16`, `use_cuda_kernel`, or `use_deepspeed` reloads the model once.

On native Windows:

- `/settings/install-deepspeed` returns a clear error.
- `use_deepspeed=true` is rejected.
- The worker fails fast if DeepSpeed is somehow enabled.
- CUDA mode fails with a clear error if worker PyTorch cannot access CUDA.

## Future Linux/WSL path

DeepSpeed can be reconsidered only for a Linux or WSL worker runtime. It should remain isolated from the main backend and must still obey install-local storage rules.
