from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from telemetry import __version__, analyze_session, build_comparison_summary, build_insights, lap_trace, parse_upload
from telemetry.analysis import format_lap_time
from telemetry.discovery import default_export_path, discover_exports
from telemetry.parser import TelemetryFormatError


st.set_page_config(page_title="FA26 Telemetry Engineer", page_icon="🏎️", layout="wide")
st.title("FA26 Telemetry Engineer")
st.caption(f"v{__version__} · Análise local de exports do Telemetrick para o VRC Formula Alpha 2026")


@st.cache_data(show_spinner=False)
def cached_parse(name: str, digest: str, raw: bytes):
    del digest
    return parse_upload(name, raw)


parsed_sessions = []
errors = []
source_mode = st.radio(
    "Fonte da telemetria",
    ["Pasta automática do Telemetrick", "Upload manual"],
    horizontal=True,
)

if source_mode == "Pasta automática do Telemetrick":
    export_root = st.text_input("Pasta de exports", value=str(default_export_path()))
    discovered = discover_exports(export_root)
    if discovered:
        display_to_path = {
            f"{datetime.fromtimestamp(path.stat().st_mtime):%d/%m %H:%M} · {path.relative_to(Path(export_root))}": path
            for path in discovered
        }
        defaults = list(display_to_path)[: min(3, len(display_to_path))]
        selected = st.multiselect("Sessões para analisar", list(display_to_path), default=defaults)
        with st.spinner("Lendo telemetria..."):
            for display_name in selected:
                path = display_to_path[display_name]
                try:
                    raw = path.read_bytes()
                    digest = hashlib.sha256(raw).hexdigest()
                    parsed_sessions.extend(cached_parse(path.name, digest, raw))
                except (OSError, TelemetryFormatError, ValueError) as exc:
                    errors.append(f"{path.name}: {exc}")
    else:
        st.info("A pasta ainda não foi encontrada. Confirme o caminho acima ou use o upload manual.")
else:
    uploads = st.file_uploader(
        "Envie um ou mais CSVs ou ZIPs do Telemetrick",
        type=["csv", "zip"],
        accept_multiple_files=True,
        help="Os arquivos são processados localmente pela aplicação.",
    )
    with st.spinner("Lendo telemetria..."):
        for upload in uploads or []:
            raw = upload.getvalue()
            digest = hashlib.sha256(raw).hexdigest()
            try:
                parsed_sessions.extend(cached_parse(upload.name, digest, raw))
            except (TelemetryFormatError, ValueError) as exc:
                errors.append(f"{upload.name}: {exc}")

for error in errors:
    st.error(error)
if not parsed_sessions:
    st.markdown(
        """
        **Esta versão já faz:** detecção de voltas válidas, comparação de ritmo, SoC, deploy,
        regeneração, clipping, super-clipping e delta por distância. O upload manual continua
        disponível como alternativa.
        """
    )
    st.stop()

st.sidebar.header("Identificação das sessões")
analyses = []
for index, session in enumerate(parsed_sessions, start=1):
    default = f"Sessão {index} · {session['metadata'].get('Log Time', '')}".strip()
    label = st.sidebar.text_input(
        f"Sessão {index}",
        value=default,
        key=f"label_{index}_{session['source_name']}",
    )
    analyses.append(analyze_session(session, label=label))

summary = build_comparison_summary(analyses)
total_clean = sum(len(analysis["clean_laps"]) for analysis in analyses)
best_candidates = [analysis for analysis in analyses if analysis["best_lap_s"] is not None]
best = min(best_candidates, key=lambda item: item["best_lap_s"]) if best_candidates else None

card1, card2, card3, card4 = st.columns(4)
card1.metric("Sessões", len(analyses))
card2.metric("Voltas válidas", total_clean)
card3.metric("Melhor volta", format_lap_time(best["best_lap_s"]) if best else "—")
card4.metric("Melhor sessão", best["label"] if best else "—")

tabs = st.tabs(["Resumo", "Voltas", "Energia", "Delta", "Diagnóstico"])

with tabs[0]:
    st.subheader("Comparação das sessões")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar resumo CSV",
        summary.to_csv(index=False).encode("utf-8-sig"),
        file_name="fa26_telemetry_resumo.csv",
        mime="text/csv",
    )

with tabs[1]:
    lap_frames = []
    for analysis in analyses:
        laps = analysis["laps"].copy()
        laps = laps[laps["complete"]]
        lap_frames.append(laps)
    lap_data = pd.concat(lap_frames, ignore_index=True) if lap_frames else pd.DataFrame()
    if lap_data.empty:
        st.warning("Nenhuma volta completa foi detectada.")
    else:
        chart = px.line(
            lap_data,
            x="lap",
            y="lap_time_s",
            color="session",
            markers=True,
            symbol="valid",
            labels={"lap": "Volta detectada", "lap_time_s": "Tempo (s)", "session": "Sessão", "valid": "Válida"},
            title="Tempo por volta",
        )
        st.plotly_chart(chart, use_container_width=True)
        shown = lap_data[
            ["session", "lap", "lap_time", "valid", "fuel_start_l", "max_speed_kmh", "soc_start_pct", "soc_end_pct"]
        ].rename(
            columns={
                "session": "Sessão",
                "lap": "Volta",
                "lap_time": "Tempo",
                "valid": "Válida",
                "fuel_start_l": "Combustível inicial (L)",
                "max_speed_kmh": "Vmax (km/h)",
                "soc_start_pct": "SoC inicial (%)",
                "soc_end_pct": "SoC final (%)",
            }
        )
        st.dataframe(shown, use_container_width=True, hide_index=True)

with tabs[2]:
    energy_frames = []
    for analysis in analyses:
        clean = analysis["clean_laps"].copy()
        if not clean.empty:
            energy_frames.append(clean)
    energy = pd.concat(energy_frames, ignore_index=True) if energy_frames else pd.DataFrame()
    if energy.empty or energy[["deploy_mj", "regen_mj"]].dropna(how="all").empty:
        st.warning("Os arquivos não possuem energia suficiente para este gráfico.")
    else:
        melted = energy.melt(
            id_vars=["session", "lap"],
            value_vars=["deploy_mj", "regen_mj"],
            var_name="tipo",
            value_name="energia_mj",
        )
        melted["tipo"] = melted["tipo"].map({"deploy_mj": "Deploy", "regen_mj": "Regeneração"})
        melted["volta"] = melted["session"] + " · V" + melted["lap"].astype(str)
        chart = px.bar(
            melted,
            x="volta",
            y="energia_mj",
            color="tipo",
            barmode="group",
            labels={"volta": "Sessão e volta", "energia_mj": "Energia (MJ)", "tipo": "Fluxo"},
            title="Deploy e regeneração nas voltas válidas",
        )
        st.plotly_chart(chart, use_container_width=True)

        phases = energy[["session", "lap", "deploy_s", "clip_s", "superclip_s", "soc_delta_pp"]].rename(
            columns={
                "session": "Sessão",
                "lap": "Volta",
                "deploy_s": "Deploy pleno (s)",
                "clip_s": "Clipping (s)",
                "superclip_s": "Super-clipping (s)",
                "soc_delta_pp": "ΔSoC (pp)",
            }
        )
        st.dataframe(phases, use_container_width=True, hide_index=True)

with tabs[3]:
    choices = []
    lookup = {}
    for analysis_index, analysis in enumerate(analyses):
        for row in analysis["clean_laps"].itertuples(index=False):
            key = f"{analysis['label']} · V{row.lap} · {row.lap_time}"
            choices.append(key)
            lookup[key] = (analysis_index, int(row.segment))

    if len(choices) < 2:
        st.warning("São necessárias pelo menos duas voltas válidas para calcular o delta.")
    else:
        left, right = st.columns(2)
        reference_key = left.selectbox("Volta de referência", choices, index=0)
        comparison_key = right.selectbox("Volta comparada", choices, index=1)
        ref_analysis, ref_segment = lookup[reference_key]
        cmp_analysis, cmp_segment = lookup[comparison_key]
        ref = lap_trace(analyses[ref_analysis], ref_segment)
        cmp = lap_trace(analyses[cmp_analysis], cmp_segment)
        if ref.empty or cmp.empty:
            st.warning("Não foi possível alinhar essas voltas por distância.")
        else:
            max_distance = min(ref["distance_m"].max(), cmp["distance_m"].max())
            ref = ref[ref["distance_m"] <= max_distance]
            cmp = cmp[cmp["distance_m"] <= max_distance]
            count = min(len(ref), len(cmp))
            delta = pd.DataFrame(
                {
                    "Distância (m)": ref["distance_m"].iloc[:count].to_numpy(),
                    "Delta (s)": cmp["elapsed_s"].iloc[:count].to_numpy() - ref["elapsed_s"].iloc[:count].to_numpy(),
                }
            )
            delta_chart = px.line(
                delta,
                x="Distância (m)",
                y="Delta (s)",
                title="Delta acumulado — negativo significa que a volta comparada está à frente",
            )
            delta_chart.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(delta_chart, use_container_width=True)

            if "speed_kmh" in ref and "speed_kmh" in cmp:
                speed_chart = go.Figure()
                speed_chart.add_trace(go.Scatter(x=ref["distance_m"], y=ref["speed_kmh"], name=reference_key))
                speed_chart.add_trace(go.Scatter(x=cmp["distance_m"], y=cmp["speed_kmh"], name=comparison_key))
                speed_chart.update_layout(title="Velocidade por distância", xaxis_title="Distância (m)", yaxis_title="Velocidade (km/h)")
                st.plotly_chart(speed_chart, use_container_width=True)

with tabs[4]:
    insights = build_insights(analyses)
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info("Ainda não há voltas válidas suficientes para gerar diagnóstico.")

    missing_advanced = [analysis["label"] for analysis in analyses if not analysis["advanced_channels"]]
    if missing_advanced:
        st.warning(
            "Canais avançados ausentes em: " + ", ".join(missing_advanced) + ". "
            "O aplicativo continua analisando ritmo, velocidade, combustível e SoC disponíveis."
        )
