from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def format_lap_time(seconds: float | int | None) -> str:
    if seconds is None or pd.isna(seconds):
        return "—"
    minutes = int(float(seconds) // 60)
    remainder = float(seconds) - minutes * 60
    return f"{minutes}:{remainder:06.3f}"


def _track_length(session: dict[str, Any]) -> float:
    explicit = session.get("venue_length_m")
    if explicit and explicit > 500:
        return float(explicit)
    distance = session["data"]["Lap Distance"].dropna()
    plausible = distance[distance <= distance.quantile(0.99)]
    return float(plausible.quantile(0.995))


def _confirmed_finish_wrap(group: pd.DataFrame, track_length: float) -> int | None:
    distance = group["Lap Distance"].to_numpy(dtype=float)
    if len(distance) < 2:
        return None
    wraps = np.flatnonzero(
        (distance[:-1] > track_length * 0.80)
        & (distance[1:] < track_length * 0.20)
    )
    for wrap in wraps:
        cut = int(wrap + 1)
        if cut >= len(group) * 0.90:
            return cut
    return None


def _trim_finish_lag(group: pd.DataFrame, track_length: float) -> pd.DataFrame:
    cut = _confirmed_finish_wrap(group, track_length)
    return group.iloc[:cut].copy() if cut else group.copy()


def _integrated_energy(group: pd.DataFrame) -> tuple[float | None, float | None]:
    if "MGU-K Rear Power" not in group.columns:
        return None, None
    time = group["time"].to_numpy(dtype=float)
    power = group["MGU-K Rear Power"].to_numpy(dtype=float)
    dt = np.diff(time, prepend=time[0])
    dt[(dt < 0) | (dt > 0.1)] = 0
    deploy = float(np.sum(np.maximum(power, 0) * dt) / 1000)
    regen = float(np.sum(np.maximum(-power, 0) * dt) / 1000)
    return deploy, regen


def _phase_metrics(group: pd.DataFrame) -> dict[str, float | None]:
    if "MGU-K Rear Power" not in group.columns:
        return {"deploy_s": None, "clip_s": None, "superclip_s": None, "superclip_mj": None}
    throttle_column = "Throttle Pedal" if "Throttle Pedal" in group.columns else "Throttle Pos"
    if throttle_column not in group.columns or "Brake Pos" not in group.columns:
        return {"deploy_s": None, "clip_s": None, "superclip_s": None, "superclip_mj": None}

    time = group["time"].to_numpy(dtype=float)
    dt = np.diff(time, prepend=time[0])
    dt[(dt < 0) | (dt > 0.1)] = 0
    power = group["MGU-K Rear Power"].to_numpy(dtype=float)
    throttle = group[throttle_column].to_numpy(dtype=float)
    brake = group["Brake Pos"].to_numpy(dtype=float)
    full = (throttle >= 99) & (brake < 1)
    deploy = full & (power > 50)
    clip = full & (np.abs(power) <= 50)
    superclip = full & (power < -50)
    return {
        "deploy_s": float(dt[deploy].sum()),
        "clip_s": float(dt[clip].sum()),
        "superclip_s": float(dt[superclip].sum()),
        "superclip_mj": float(np.sum(np.maximum(-power[superclip], 0) * dt[superclip]) / 1000),
    }


def _value(group: pd.DataFrame, column: str, where: str = "first") -> float | None:
    if column not in group.columns:
        return None
    series = group[column].dropna()
    if series.empty:
        return None
    if where == "last":
        return float(series.iloc[-1])
    if where == "max":
        return float(series.max())
    if where == "min":
        return float(series.min())
    if where == "median":
        return float(series.median())
    return float(series.iloc[0])


def analyze_session(session: dict[str, Any], label: str | None = None) -> dict[str, Any]:
    frame = session["data"].copy()
    track_length = _track_length(session)
    frame["_segment"] = (frame["Lap Time"].diff() < -10).cumsum().astype(int)
    rows: list[dict[str, Any]] = []

    for segment, raw_group in frame.groupby("_segment", sort=True):
        group = _trim_finish_lag(raw_group, track_length)
        if group.empty:
            continue
        elapsed = float(group["time"].iloc[-1] - group["time"].iloc[0])
        start_lap_time = float(group["Lap Time"].iloc[0])
        distance = group["Lap Distance"].dropna()
        distance_p95 = float(distance.quantile(0.95)) if not distance.empty else 0
        distance_start = float(distance.iloc[0]) if not distance.empty else track_length
        complete = bool(
            elapsed >= 30
            and start_lap_time <= 2
            and distance_start <= track_length * 0.20
            and distance_p95 >= track_length * 0.80
        )
        duration = float(group["Lap Time"].max()) if complete else elapsed
        invalid = bool(_value(group, "Lap Invalidated", "max") or 0)
        deploy_integrated, regen_integrated = _integrated_energy(group)
        phases = _phase_metrics(group)

        deploy_counter = _value(group, "KERS Deploy MJ", "max")
        regen_counter = _value(group, "KERS Regen MJ", "max")
        if deploy_counter is None and "KERS Deployed Energy" in group.columns:
            deploy_counter = (_value(group, "KERS Deployed Energy", "max") or 0) / 1000

        soc_start = _value(group, "KERS Charge")
        soc_end = _value(group, "KERS Charge", "last")
        esoc_start = _value(group, "KERS Charge ESOC")
        esoc_end = _value(group, "KERS Charge ESOC", "last")
        rows.append(
            {
                "session": label or session["source_name"],
                "segment": int(segment),
                "lap": len(rows) + 1,
                "complete": complete,
                "valid": complete and not invalid,
                "lap_time_s": duration,
                "lap_time": format_lap_time(duration),
                "fuel_start_l": _value(group, "Fuel Level"),
                "fuel_end_l": _value(group, "Fuel Level", "last"),
                "max_speed_kmh": _value(group, "Ground Speed", "max"),
                "soc_start_pct": soc_start,
                "soc_end_pct": soc_end,
                "soc_delta_pp": None if soc_start is None or soc_end is None else soc_end - soc_start,
                "esoc_start_mj": esoc_start,
                "esoc_end_mj": esoc_end,
                "esoc_delta_mj": None if esoc_start is None or esoc_end is None else esoc_end - esoc_start,
                "deploy_mj": deploy_counter if deploy_counter is not None else deploy_integrated,
                "regen_mj": regen_counter if regen_counter is not None else regen_integrated,
                "deploy_integrated_mj": deploy_integrated,
                "regen_integrated_mj": regen_integrated,
                "pu_mode": _value(group, "PU Mode", "median"),
                "deployment_strat": _value(group, "Deployment Strat", "median"),
                "tyre_compound": _value(group, "Tyres Compound", "median"),
                **phases,
            }
        )

    lap_table = pd.DataFrame(rows)
    clean = lap_table[lap_table["valid"]] if not lap_table.empty else lap_table
    metadata = session["metadata"]
    return {
        **session,
        "label": label or session["source_name"],
        "track_length_m": track_length,
        "data": frame,
        "laps": lap_table,
        "clean_laps": clean,
        "best_lap_s": None if clean.empty else float(clean["lap_time_s"].min()),
        "median_lap_s": None if clean.empty else float(clean["lap_time_s"].median()),
        "track": metadata.get("Venue", "Pista desconhecida"),
        "vehicle": metadata.get("Vehicle", "Carro desconhecido"),
        "log_time": metadata.get("Log Time", ""),
    }


def build_comparison_summary(analyses: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for analysis in analyses:
        clean = analysis["clean_laps"]
        rows.append(
            {
                "Sessão": analysis["label"],
                "Pista": analysis["track"],
                "Voltas válidas": int(len(clean)),
                "Melhor volta": format_lap_time(analysis["best_lap_s"]),
                "Mediana": format_lap_time(analysis["median_lap_s"]),
                "Vmax média (km/h)": None if clean.empty else round(float(clean["max_speed_kmh"].mean()), 1),
                "Deploy médio (MJ)": None if clean.empty or clean["deploy_mj"].dropna().empty else round(float(clean["deploy_mj"].mean()), 2),
                "Regen média (MJ)": None if clean.empty or clean["regen_mj"].dropna().empty else round(float(clean["regen_mj"].mean()), 2),
                "ΔSoC médio (pp)": None if clean.empty or clean["soc_delta_pp"].dropna().empty else round(float(clean["soc_delta_pp"].mean()), 2),
                "Canais VRC": "Completos" if analysis["advanced_channels"] else "Básicos",
            }
        )
    return pd.DataFrame(rows)


def build_insights(analyses: list[dict[str, Any]]) -> list[str]:
    insights: list[str] = []
    eligible = [analysis for analysis in analyses if not analysis["clean_laps"].empty]
    if len(eligible) >= 2:
        fastest = min(eligible, key=lambda item: item["median_lap_s"])
        slowest = max(eligible, key=lambda item: item["median_lap_s"])
        delta = float(slowest["median_lap_s"] - fastest["median_lap_s"])
        insights.append(f"{fastest['label']} tem a melhor mediana, {delta:.3f} s à frente de {slowest['label']}.")

    for analysis in eligible:
        clean = analysis["clean_laps"]
        soc = clean["soc_delta_pp"].dropna()
        if not soc.empty:
            mean_soc = float(soc.mean())
            if mean_soc < -5:
                insights.append(f"{analysis['label']} descarrega a bateria: ΔSoC médio de {mean_soc:.1f} pp por volta válida.")
            elif abs(mean_soc) <= 2:
                insights.append(f"{analysis['label']} ficou próximo do equilíbrio energético: ΔSoC médio de {mean_soc:+.1f} pp.")

        if analysis["advanced_channels"]:
            superclip = clean["superclip_s"].dropna()
            if not superclip.empty and float(superclip.mean()) < 0.5:
                insights.append(f"{analysis['label']} registrou menos de 0,5 s de super-clipping efetivo por volta.")
        else:
            insights.append(f"{analysis['label']} não contém os canais avançados do VRC; o diagnóstico energético é parcial.")
    return insights


def lap_trace(analysis: dict[str, Any], segment: int, step_m: int = 25) -> pd.DataFrame:
    group = analysis["data"][analysis["data"]["_segment"] == int(segment)]
    group = _trim_finish_lag(group, analysis["track_length_m"])
    wanted = ["Lap Distance", "time", "Ground Speed", "KERS Charge", "MGU-K Rear Power"]
    columns = [column for column in wanted if column in group.columns]
    work = group[columns].dropna(subset=["Lap Distance", "time"]).copy()
    work = work[(work["Lap Distance"] >= 0) & (work["Lap Distance"] <= analysis["track_length_m"] * 1.03)]
    work = work.sort_values("Lap Distance").drop_duplicates("Lap Distance")
    if len(work) < 2:
        return pd.DataFrame()

    grid = np.arange(0, analysis["track_length_m"] + 1, step_m, dtype=float)
    distance = work["Lap Distance"].to_numpy(dtype=float)
    raw_time = work["time"].to_numpy(dtype=float)
    interpolated_time = np.interp(grid, distance, raw_time)
    result = pd.DataFrame({"distance_m": grid, "elapsed_s": interpolated_time - interpolated_time[0]})
    for source, target in [
        ("Ground Speed", "speed_kmh"),
        ("KERS Charge", "soc_pct"),
        ("MGU-K Rear Power", "mgu_k_kw"),
    ]:
        if source in work.columns:
            result[target] = np.interp(grid, distance, work[source].to_numpy(dtype=float))
    return result
