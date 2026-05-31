"""Idempotent SQLite migrations for the desktop database."""

import logging
import sqlite3

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)


def run_migrations(engine) -> None:
    """Run all schema migrations. Safe to call on every startup."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    _drop_removed_tables(engine, tables)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    _migrate_story_items(engine, inspector, tables)
    _migrate_profiles(engine, inspector, tables)
    _migrate_generations(engine, inspector, tables)
    _migrate_effect_presets(engine, inspector, tables)
    _migrate_generation_versions(engine, inspector, tables)
    _create_audio_library_items(engine, tables)
    _normalize_storage_paths(engine, tables)


def _get_columns(inspector, table: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table)}


def _add_column(engine, table: str, column_sql: str, label: str) -> None:
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))
        conn.commit()
    logger.info("Added %s column to %s", label, table)


def _drop_removed_tables(engine, tables: set[str]) -> None:
    removed = {"captures", "capture_settings", "mcp_client_bindings"}
    existing = removed.intersection(tables)
    if not existing:
        return
    with engine.connect() as conn:
        for table in sorted(existing):
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            logger.info("Dropped removed table %s", table)
        conn.commit()


def _drop_columns(engine, table: str, columns: set[str]) -> None:
    if not columns:
        return
    if not _supports_drop_column(engine):
        logger.warning(
            "SQLite %s too old to drop columns from %s; leaving legacy columns in place",
            sqlite3.sqlite_version,
            table,
        )
        return
    with engine.connect() as conn:
        for column in sorted(columns):
            conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))
            logger.info("Dropped legacy %s.%s", table, column)
        conn.commit()


def _migrate_story_items(engine, inspector, tables: set[str]) -> None:
    if "story_items" not in tables:
        return
    columns = _get_columns(inspector, "story_items")
    if "track" not in columns:
        _add_column(engine, "story_items", "track INTEGER NOT NULL DEFAULT 0", "track")
    columns = _get_columns(inspector, "story_items")
    if "trim_start_ms" not in columns:
        _add_column(engine, "story_items", "trim_start_ms INTEGER NOT NULL DEFAULT 0", "trim_start_ms")
    if "trim_end_ms" not in columns:
        _add_column(engine, "story_items", "trim_end_ms INTEGER NOT NULL DEFAULT 0", "trim_end_ms")
    if "version_id" not in columns:
        _add_column(engine, "story_items", "version_id VARCHAR", "version_id")
    if "volume" not in columns:
        _add_column(engine, "story_items", "volume FLOAT NOT NULL DEFAULT 1.0", "volume")


def _migrate_profiles(engine, inspector, tables: set[str]) -> None:
    if "profiles" not in tables:
        return
    columns = _get_columns(inspector, "profiles")
    if "avatar_path" not in columns:
        _add_column(engine, "profiles", "avatar_path VARCHAR", "avatar_path")
    if "effects_chain" not in columns:
        _add_column(engine, "profiles", "effects_chain TEXT", "effects_chain")
    legacy = {
        "voice_type",
        "preset_engine",
        "preset_voice_id",
        "design_prompt",
        "default_engine",
        "personality",
    }.intersection(columns)
    _drop_columns(engine, "profiles", legacy)


def _migrate_generations(engine, inspector, tables: set[str]) -> None:
    if "generations" not in tables:
        return
    columns = _get_columns(inspector, "generations")
    if "status" not in columns:
        _add_column(engine, "generations", "status VARCHAR DEFAULT 'completed'", "status")
    if "error" not in columns:
        _add_column(engine, "generations", "error TEXT", "error")
    if "model_size" not in columns:
        _add_column(engine, "generations", "model_size VARCHAR", "model_size")
    if "is_favorited" not in columns:
        _add_column(engine, "generations", "is_favorited BOOLEAN DEFAULT 0", "is_favorited")
    if "source" not in columns:
        _add_column(engine, "generations", "source VARCHAR NOT NULL DEFAULT 'manual'", "source")
    columns = _get_columns(inspector, "generations")
    _drop_columns(engine, "generations", {"engine"}.intersection(columns))


def _migrate_effect_presets(engine, inspector, tables: set[str]) -> None:
    if "effect_presets" not in tables:
        return
    if "sort_order" not in _get_columns(inspector, "effect_presets"):
        _add_column(engine, "effect_presets", "sort_order INTEGER DEFAULT 100", "sort_order")


def _migrate_generation_versions(engine, inspector, tables: set[str]) -> None:
    if "generation_versions" not in tables:
        return
    if "source_version_id" not in _get_columns(inspector, "generation_versions"):
        _add_column(engine, "generation_versions", "source_version_id VARCHAR", "source_version_id")


def _create_audio_library_items(engine, tables: set[str]) -> None:
    if "audio_library_items" in tables:
        return
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE audio_library_items (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                language VARCHAR,
                gender VARCHAR,
                style VARCHAR,
                tags TEXT,
                audio_path VARCHAR NOT NULL,
                duration FLOAT,
                source VARCHAR NOT NULL DEFAULT 'user',
                created_at DATETIME
            )
        """))
        conn.commit()
    logger.info("Created audio_library_items table")


def _supports_drop_column(engine) -> bool:
    if engine.dialect.name != "sqlite":
        return True
    return tuple(int(p) for p in sqlite3.sqlite_version.split(".")[:3]) >= (3, 35, 0)


def _normalize_storage_paths(engine, tables: set[str]) -> None:
    from pathlib import Path

    from ..config import resolve_storage_path, to_storage_path

    path_columns = [
        ("generations", "audio_path"),
        ("generation_versions", "audio_path"),
        ("profile_samples", "audio_path"),
        ("profiles", "avatar_path"),
        ("audio_library_items", "audio_path"),
    ]

    total_fixed = 0
    with engine.connect() as conn:
        for table, column in path_columns:
            if table not in tables:
                continue
            rows = conn.execute(text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")).fetchall()
            for row_id, path_val in rows:
                if not path_val:
                    continue
                resolved = resolve_storage_path(Path(path_val))
                if resolved is None:
                    continue
                normalized = to_storage_path(resolved)
                if normalized != path_val:
                    conn.execute(text(f"UPDATE {table} SET {column} = :path WHERE id = :id"), {"path": normalized, "id": row_id})
                    total_fixed += 1
        if total_fixed:
            conn.commit()
            logger.info("Normalized %d stored file paths", total_fixed)
