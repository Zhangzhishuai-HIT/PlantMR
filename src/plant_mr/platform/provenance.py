"""Input byte receipts for reproducible PlantMR runs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .project import ProjectManifest


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path("external") / path.name


def input_receipts(manifest: ProjectManifest) -> list[dict[str, Any]]:
    root = manifest.manifest_path.parent
    receipts = []
    for role, raw_path in sorted(manifest.inputs.items()):
        if not raw_path:
            continue
        path = manifest.resolve_input(role)
        if not path.exists() or not path.is_file():
            continue
        receipts.append(
            {
                "role": role,
                "path": str(_relative(path, root)),
                "size_bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    return receipts
