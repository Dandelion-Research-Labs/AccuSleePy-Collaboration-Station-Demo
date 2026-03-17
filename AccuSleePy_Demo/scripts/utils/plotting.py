"""Shared plotting utilities for the AccuSleePy Demo pipeline.

Provides project-wide constants (stage colors, labels) and helper functions
used by 06_figures.py so that styling logic is defined once and applied
consistently across all figures.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend safe for scripts
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ---------------------------------------------------------------------------
# Project-wide constants
# ---------------------------------------------------------------------------

#: Consistent stage colors used in all figures
STAGE_COLORS = {
    "wake": "#2ca02c",   # green
    "nrem": "#1f77b4",   # blue
    "rem":  "#d62728",   # red
}

#: Human-readable stage labels for axes and legends
STAGE_LABELS = {
    "wake": "Wake",
    "nrem": "NREM",
    "rem":  "REM",
}

#: Mapping from integer label value to stage key
LABEL_TO_STAGE = {1: "rem", 2: "wake", 3: "nrem"}

#: Ordered list of stage keys for consistent axis/legend order
STAGE_ORDER = ["wake", "nrem", "rem"]

#: Seconds per epoch (2.5 s at 512 Hz)
EPOCH_DURATION_S = 2.5


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def stage_color(stage_key: str) -> str:
    """Return the hex color string for a stage key.

    :param stage_key: one of ``"wake"``, ``"nrem"``, ``"rem"``
    :return: hex color string
    :raises KeyError: if stage_key is not recognized
    """
    return STAGE_COLORS[stage_key]


def stage_legend_handles() -> list:
    """Return a list of Patch handles for Wake, NREM, REM suitable for plt.legend.

    :return: list of three matplotlib.patches.Patch objects in STAGE_ORDER
    """
    return [
        mpatches.Patch(color=STAGE_COLORS[s], label=STAGE_LABELS[s])
        for s in STAGE_ORDER
    ]


def save_figure(fig: plt.Figure, output_path: str, dpi: int = 300) -> None:
    """Save a matplotlib figure to disk as PNG.

    Creates parent directories as needed.

    :param fig: the matplotlib Figure to save
    :param output_path: destination path (will be saved as PNG regardless of extension)
    :param dpi: resolution in dots per inch (default: 300)
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def apply_spine_style(ax: plt.Axes) -> None:
    """Remove top and right spines for a cleaner publication style.

    :param ax: matplotlib Axes object to style
    """
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
