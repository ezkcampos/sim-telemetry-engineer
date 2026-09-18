"""Core do FA26 Telemetry Engineer."""

from .analysis import analyze_session, build_comparison_summary, build_insights, lap_trace
from .parser import parse_upload
from .setup import SetupDocument, parse_setup, semantic_setup_diff
from .version import __version__

__all__ = [
    "analyze_session",
    "build_comparison_summary",
    "build_insights",
    "lap_trace",
    "parse_upload",
    "parse_setup",
    "semantic_setup_diff",
    "SetupDocument",
    "__version__",
]
