from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd


MAX_MEMBER_BYTES = 600 * 1024 * 1024

SUPPORTED_COLUMNS = [
    "time",
    "Ground Speed",
    "Lap Time",
    "Lap Distance",
    "Lap Number",
    "Lap Invalidated",
    "Num Tires Off Track",
    "Throttle Pos",
    "Throttle Pedal",
    "Brake Pos",
    "Gear",
    "Engine RPM",
    "Fuel Level",
    "Air Temp",
    "Road Temp",
    "Surface Grip",
    "Tyres Compound",
    "Brake Bias",
    "Brake Bias Base",
    "Brake Bias Live",
    "PU Mode",
    "Deployment Strat",
    "Deployment Split",
    "KERS Charge",
    "KERS Charge ESOC",
    "KERS Deployed Energy",
    "KERS Deploy MJ",
    "KERS Regen MJ",
    "KERS Regen Limit MJ",
    "MGU-K Rear Power",
    "MGU-K Rear Torque",
    "MGU-K Max Power",
    "KERS Input",
    "ERS Is Charging",
    "KERS Charge Active",
    "Power Limited",
    "Power Limited Pending",
    "MGU-K Max Power Reduction",
    "MGU-K Max Power Limit",
    "Overtake Active",
    "KERS Boost Active",
    "DRS Active",
    "Aero Drag",
    "Aero Downforce F",
    "Aero Downforce R",
    "Ride Height Front",
    "Ride Height Rear",
    "Tire Rubber Grip FL",
    "Tire Rubber Grip FR",
    "Tire Rubber Grip RL",
    "Tire Rubber Grip RR",
    "Tire Temp Core FL",
    "Tire Temp Core FR",
    "Tire Temp Core RL",
    "Tire Temp Core RR",
]


class TelemetryFormatError(ValueError):
    """Arquivo incompatível ou incompleto."""


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_header(raw: bytes) -> tuple[int, dict[str, str], dict[str, str]]:
    prefix = raw[:262_144].decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(prefix)))
    header_index: int | None = None
    metadata: dict[str, str] = {}
    static: dict[str, str] = {}

    for index, row in enumerate(rows):
        if not row:
            continue
        first = row[0].strip()
        if first == "time":
            header_index = index
            break
        if first == "data" and index + 2 < len(rows):
            names = row[1:]
            values = rows[index + 2][1:]
            static.update({name: values[pos] for pos, name in enumerate(names) if pos < len(values)})
        elif len(row) >= 2 and first:
            metadata[first] = row[1].strip()

    if header_index is None:
        raise TelemetryFormatError("Cabeçalho 'time' não encontrado no CSV do Telemetrick.")
    return header_index, metadata, static


def parse_csv_bytes(raw: bytes, source_name: str) -> dict[str, Any]:
    header_index, metadata, static = _read_header(raw)
    header = pd.read_csv(io.BytesIO(raw), skiprows=header_index, nrows=0).columns.tolist()
    columns = [column for column in SUPPORTED_COLUMNS if column in header]
    required = {"time", "Lap Time", "Lap Distance", "Ground Speed"}
    missing = required.difference(columns)
    if missing:
        raise TelemetryFormatError(f"Canais obrigatórios ausentes: {', '.join(sorted(missing))}.")

    frame = pd.read_csv(
        io.BytesIO(raw),
        skiprows=header_index,
        usecols=columns,
        low_memory=False,
    )
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame[frame["time"].notna()].copy()
    frame[columns] = frame[columns].ffill()
    frame.reset_index(drop=True, inplace=True)

    lap_times = []
    for token in metadata.get("lapTimes", "").split(","):
        value = _to_float(token.strip())
        if value is not None:
            lap_times.append(value)

    venue_length = _to_float(static.get("Venue Length"))
    return {
        "source_name": source_name,
        "metadata": metadata,
        "static": static,
        "venue_length_m": venue_length,
        "recorded_lap_times": lap_times,
        "advanced_channels": "MGU-K Rear Power" in frame.columns,
        "data": frame,
    }


def parse_upload(file_name: str, raw: bytes) -> list[dict[str, Any]]:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        return [parse_csv_bytes(raw, Path(file_name).name)]
    if suffix != ".zip":
        raise TelemetryFormatError("Envie um arquivo .csv ou .zip do Telemetrick.")

    sessions: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            if info.is_dir() or member.suffix.lower() != ".csv":
                continue
            if member.is_absolute() or ".." in member.parts:
                raise TelemetryFormatError("ZIP contém um caminho inseguro.")
            if info.file_size > MAX_MEMBER_BYTES:
                raise TelemetryFormatError(f"CSV excede o limite de {MAX_MEMBER_BYTES // 1024 // 1024} MB.")
            sessions.append(parse_csv_bytes(archive.read(info), member.name))

    if not sessions:
        raise TelemetryFormatError("Nenhum CSV foi encontrado dentro do ZIP.")
    return sessions
