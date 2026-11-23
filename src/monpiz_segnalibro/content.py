"""Loading and validation of the bookmark content."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .errors import ContentError
from .models import Bookmark
from .vector import load_svg


def _read_yaml(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ContentError(f"File di contenuto non trovato: {path}") from exc
    except yaml.YAMLError as exc:
        raise ContentError(f"YAML non valido in {path}:\n{exc}") from exc


def load_bookmark(content_file: Path, assets_dir: Path) -> Bookmark:
    """Load and validate ``content_file``, checking that every image exists."""
    raw = _read_yaml(content_file)
    if not isinstance(raw, dict):
        raise ContentError(f"{content_file} deve contenere una mappa YAML al livello radice")
    try:
        bookmark = Bookmark.model_validate(raw)
    except ValidationError as exc:
        lines = [f"Contenuto non valido in {content_file}:"]
        for issue in exc.errors():
            location = ".".join(str(part) for part in issue["loc"]) or "(radice)"
            lines.append(f"  - {location}: {issue['msg']}")
        raise ContentError("\n".join(lines)) from exc

    missing = sorted({str(p) for p in bookmark.asset_paths() if not (assets_dir / p).is_file()})
    if missing:
        listing = "\n".join(f"  - {name}" for name in missing)
        raise ContentError(f"Immagini mancanti in {assets_dir}:\n{listing}")
    load_svg(assets_dir / bookmark.front.logo)  # fails here, at check time, if the SVG is unusable
    return bookmark
