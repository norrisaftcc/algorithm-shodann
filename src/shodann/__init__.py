"""SHODANN: measures learning velocity (dy/dx) rather than absolute skill.

The public surface intentionally mirrors the JavaScript engine it replaces, so
that references to it in the design documents still resolve to something.
"""

from .config import DEFAULT_CONFIG, ORACLE_CONFIG, VelocityConfig
from .leaderboard import generate_leaderboard
from .prompt_section import generate_prompt_section
from .state import CitizenRecord, load_citizen_history, save_citizen_history
from .velocity import CodeMetrics, MetricDeltas, VelocityResult, calculate_velocity

__all__ = [
    "DEFAULT_CONFIG",
    "ORACLE_CONFIG",
    "CitizenRecord",
    "CodeMetrics",
    "MetricDeltas",
    "VelocityConfig",
    "VelocityResult",
    "calculate_velocity",
    "generate_leaderboard",
    "generate_prompt_section",
    "load_citizen_history",
    "save_citizen_history",
]

__version__ = "0.1.0"
