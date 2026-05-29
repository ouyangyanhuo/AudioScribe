"""Entry point for the voicebox backend.

Imports the configured FastAPI app and provides a ``python -m backend.main``
entry point for development.
"""

import argparse
import os
import sys

import uvicorn


def _preconfigure_install_dir_env() -> None:
    """Set VOICEBOX_INSTALL_DIR before importing modules that initialize caches."""
    args = sys.argv[1:]
    for idx, arg in enumerate(args):
        if arg == "--install-dir" and idx + 1 < len(args):
            os.environ["VOICEBOX_INSTALL_DIR"] = args[idx + 1]
            return
        if arg.startswith("--install-dir="):
            os.environ["VOICEBOX_INSTALL_DIR"] = arg.split("=", 1)[1]
            return


_preconfigure_install_dir_env()

from .app import app  # noqa: F401 -- re-export for uvicorn "backend.main:app"
from . import config, database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="voicebox backend server")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (use 0.0.0.0 for remote access)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )
    parser.add_argument(
        "--install-dir",
        type=str,
        default=None,
        help="Install directory that contains data, cache, and model folders",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Legacy data directory override for database, profiles, and generated audio",
    )
    args = parser.parse_args()

    if args.install_dir:
        config.set_install_dir(args.install_dir)
    elif args.data_dir:
        config.set_data_dir(args.data_dir)

    database.init_db()

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
