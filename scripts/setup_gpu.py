from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import setup_indextts2


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str]) -> None:
    print(f"[gpu] {' '.join(command)}", flush=True)
    subprocess.check_call(command, cwd=str(ROOT), env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install GPU acceleration packages into the IndexTTS2 worker runtime.")
    parser.add_argument("--cuda", default="cu124", choices=["cu121", "cu124", "cu126"], help="PyTorch CUDA wheel channel.")
    args = parser.parse_args()

    try:
        env = setup_indextts2.setup_env()
        python = setup_indextts2.worker_python()
        if not python.exists():
            raise RuntimeError("IndexTTS2 worker runtime is missing. Run `just setup-indextts2` first.")

        uv = shutil.which("uv")
        if not uv:
            uv = setup_indextts2.ensure_uv()

        index_url = f"https://download.pytorch.org/whl/{args.cuda}"
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--reinstall",
                "torch",
                "torchvision",
                "torchaudio",
                "--index-url",
                index_url,
            ],
            env=env,
        )
        run(
            [
                str(python),
                "-c",
                "import torch; print('torch', torch.__version__); print('cuda', torch.version.cuda); print('available', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')",
            ],
            env=env,
        )
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"[gpu] Command failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    except RuntimeError as exc:
        print(f"[gpu] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
