"""Lossless, read-only parsing for Assetto Corsa setup files.

The parser keeps the original byte stream untouched. Its structured view is intended for
inspection and semantic diffs; writing a modified setup will be implemented separately so
that unknown sections, comments, ordering and formatting cannot be lost accidentally.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


_SECTION_RE = re.compile(r"^\s*\[([^\]\r\n]+)\]\s*(?:[;#].*)?$")
_ENTRY_RE = re.compile(r"^\s*([^;#=][^=]*?)\s*=\s*(.*?)\s*$")


@dataclass(frozen=True)
class SetupEntry:
    section: str
    key: str
    value: str
    line_number: int


@dataclass(frozen=True)
class SetupChange:
    section: str
    key: str
    before: str | None
    after: str | None
    category: str


@dataclass(frozen=True)
class SetupDocument:
    """A lossless setup document plus a deterministic structured view."""

    raw_bytes: bytes
    text: str
    encoding: str
    entries: tuple[SetupEntry, ...]
    section_order: tuple[str, ...]

    def to_bytes(self) -> bytes:
        """Return the exact original payload, byte for byte."""

        return self.raw_bytes

    def get(self, section: str, key: str, default: str | None = None) -> str | None:
        """Return the last value for a key, matching INI override semantics."""

        section_key = section.casefold()
        entry_key = key.casefold()
        for entry in reversed(self.entries):
            if entry.section.casefold() == section_key and entry.key.casefold() == entry_key:
                return entry.value
        return default

    def as_mapping(self) -> dict[tuple[str, str], str]:
        """Build a case-insensitive semantic mapping while preserving display names."""

        result: dict[tuple[str, str], str] = {}
        names: dict[tuple[str, str], tuple[str, str]] = {}
        for entry in self.entries:
            normalized = (entry.section.casefold(), entry.key.casefold())
            names[normalized] = (entry.section, entry.key)
            result[normalized] = entry.value
        return {names[key]: value for key, value in result.items()}


def _decode_setup(payload: bytes) -> tuple[str, str]:
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        return payload.decode("utf-16"), "utf-16"
    if payload.startswith(b"\xef\xbb\xbf"):
        return payload.decode("utf-8-sig"), "utf-8-sig"
    try:
        return payload.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return payload.decode("cp1252"), "cp1252"


def parse_setup(payload: bytes) -> SetupDocument:
    """Parse an INI/SP payload without changing its original representation."""

    text, encoding = _decode_setup(payload)
    current_section = ""
    entries: list[SetupEntry] = []
    section_order: list[str] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        section_match = _SECTION_RE.match(raw_line)
        if section_match:
            current_section = section_match.group(1).strip()
            section_order.append(current_section)
            continue

        entry_match = _ENTRY_RE.match(raw_line)
        if entry_match:
            entries.append(
                SetupEntry(
                    section=current_section,
                    key=entry_match.group(1).strip(),
                    value=entry_match.group(2),
                    line_number=line_number,
                )
            )

    return SetupDocument(
        raw_bytes=payload,
        text=text,
        encoding=encoding,
        entries=tuple(entries),
        section_order=tuple(section_order),
    )


def categorize_setup_key(section: str, key: str) -> str:
    token = f"{section} {key}".upper()
    if re.search(r"ERS|MGU|KERS|DEPLOY|REGEN|STRAT|ENERGY|ELECTRIC", token):
        return "energy"
    if re.search(r"WING|AERO|FLAP|DRAG|DOWNFORCE", token):
        return "aero"
    if re.search(r"TYRE|TIRE|PRESSURE|CAMBER|TOE", token):
        return "tyres"
    if re.search(r"DAMP|BUMP|REBOUND|SPRING|ARB|SUSP", token):
        return "suspension"
    if re.search(r"GEAR|DIFF|BRAKE|FUEL", token):
        return "mechanical"
    return "other"


def semantic_setup_diff(before: SetupDocument, after: SetupDocument) -> list[SetupChange]:
    """Return stable, value-level changes without treating formatting as a change."""

    before_values = _normalized_values(before.entries)
    after_values = _normalized_values(after.entries)
    ordered_keys = _ordered_union(before.entries, after.entries)
    changes: list[SetupChange] = []

    for normalized, display in ordered_keys:
        old_value = before_values.get(normalized)
        new_value = after_values.get(normalized)
        if old_value == new_value:
            continue
        section, key = display
        changes.append(
            SetupChange(
                section=section,
                key=key,
                before=old_value,
                after=new_value,
                category=categorize_setup_key(section, key),
            )
        )
    return changes


def _normalized_values(entries: Iterable[SetupEntry]) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for entry in entries:
        result[(entry.section.casefold(), entry.key.casefold())] = entry.value
    return result


def _ordered_union(
    before: Iterable[SetupEntry], after: Iterable[SetupEntry]
) -> list[tuple[tuple[str, str], tuple[str, str]]]:
    result: list[tuple[tuple[str, str], tuple[str, str]]] = []
    positions: dict[tuple[str, str], int] = {}
    for entry in (*tuple(before), *tuple(after)):
        normalized = (entry.section.casefold(), entry.key.casefold())
        display = (entry.section, entry.key)
        if normalized in positions:
            result[positions[normalized]] = (normalized, display)
        else:
            positions[normalized] = len(result)
            result.append((normalized, display))
    return result
