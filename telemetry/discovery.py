from __future__ import annotations

import os
from pathlib import Path


def default_export_path() -> Path:
    home = Path.home()
    candidates = [
        home / "Documents" / "Assetto Corsa" / "apps" / "telemetrick" / "exported",
        home / "OneDrive" / "Documents" / "Assetto Corsa" / "apps" / "telemetrick" / "exported",
    ]
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        profile = Path(user_profile)
        candidates.insert(0, profile / "Documents" / "Assetto Corsa" / "apps" / "telemetrick" / "exported")
        candidates.append(profile / "OneDrive" / "Documents" / "Assetto Corsa" / "apps" / "telemetrick" / "exported")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def discover_exports(root: str | Path, limit: int = 100) -> list[Path]:
    path = Path(root).expanduser()
    if not path.is_dir():
        return []
    files = [item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".csv", ".zip"}]
    files.sort(key=lambda item: item.stat().st_mtime_ns, reverse=True)
    return files[:limit]
