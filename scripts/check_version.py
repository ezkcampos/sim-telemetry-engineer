"""Verifica se as fontes públicas de versão estão sincronizadas."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = metadata["project"]["version"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    errors: list[str] = []
    if not SEMVER.fullmatch(version):
        errors.append(f"VERSION não é SemVer válido: {version!r}")
    if project_version != version:
        errors.append(f"pyproject.toml={project_version!r}, VERSION={version!r}")
    if f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md não contém a seção [{version}]")

    if errors:
        for error in errors:
            print(f"ERRO: {error}", file=sys.stderr)
        return 1

    print(f"Versão {version} consistente em VERSION, pyproject.toml e CHANGELOG.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
