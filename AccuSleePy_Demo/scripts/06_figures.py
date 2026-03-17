"""Phase 6: Figure Generation

Generates all publication-quality figures for the AccuSleePy Demo analysis.

Figures produced
----------------
1. Hypnograms          (figures/hypnograms/)
   Predicted sleep-stage sequence over the 4-hour recording for 6
   representative animals (Mouse01–Mouse06, Day1 each).

2. Stage percentage plots  (figures/stage_percentages/)
   Bar chart of mean ± SEM % Wake, % NREM, and % REM across 10 animals,
   with individual mouse data points overlaid.  Within-mouse average is
   computed first (5 recordings per mouse → 1 value per mouse).

3. Bout duration plots     (figures/bout_analysis/)
   Grouped box plots of mean bout duration (s) per stage across 10 animals.
   Within-mouse average is computed first before plotting.

4. Aggregate confusion matrix  (figures/validation/)
   3×3 confusion matrix summed across all 50 recordings, normalized to
   row percentages.  Rows = expert label; columns = predicted label.

5. Kappa distribution      (figures/validation/)
   Box plot of per-recording Cohen's kappa values with individual points.

6. Transition matrix heatmap   (figures/transitions/)
   Mean stage transition probability matrix across all recordings (3×3).

All figures are saved as PNG at 300 DPI (or the value passed to --dpi).
Colors: Wake = green, NREM = blue, REM = red throughout.

Usage
-----
python scripts/06_figures.py \\
    --sleep_metrics_csv AccuSleePy_Demo/outputs/sleep_metrics.csv \\
    --validation_csv    AccuSleePy_Demo/outputs/validation_summary.csv \\
    --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \\
    --output_dir        AccuSleePy_Demo/figures \\
    [--dpi 300]
"""

import argparse
import sys
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------------
# Make utils importable from any working directory
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from utils.plotting import (       # noqa: E402
    STAGE_COLORS,
    STAGE_LABELS,
    STAGE_ORDER,
    LABEL_TO_STAGE,
    EPOCH_DURATION_S,
    stage_legend_handles,
    save_figure,
    apply_spine_style,
)
from utils.data_loading import load_predicted_labels  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Animals and recording selected for hypnograms (Day1 for Mouse01–Mouse06)
HYPNOGRAM_ANIMALS = [f"Mouse{i:02d}" for i in range(1, 7)]
HYPNOGRAM_DAY = "Day1"

#: Y-axis positions for stages in the hypnogram (Wake at top)
_STAGE_Y = {"wake": 2, "nrem": 1, "rem": 0}
_Y_LABELS = {2: "Wake", 1: "NREM", 0: "REM"}

#: Confusion matrix stage order (matches column naming in validation_summary.csv)
CM_STAGES = ["wake", "nrem", "rem"]
CM_LABELS = ["Wake", "NREM", "REM"]


# ---------------------------------------------------------------------------
# Figure 1: Hypnograms
# ---------------------------------------------------------------------------

def plot_hypnogram(labels: np.ndarray, recording_id: str,
                   output_path: str, dpi: int) -> None:
    """Plot a predicted-label hypnogram for one recording.

    Each sleep stage is shown as a colored horizontal bar on a discrete
    y-axis (Wake=2, NREM=1, REM=0).  The x-axis shows elapsed time in hours.

    :param labels: 1-D integer array of predicted labels {1, 2, 3}
    :param recording_id: title string for the figure (e.g. ``"Mouse01_Day1"``)
    :param output_path: destination PNG path
    :param dpi: output resolution
    """
    n = len(labels)
    # Time vector: start of each epoch in hours
    t = np.arange(n) * EPOCH_DURATION_S / 3600.0
    # One extra time point for the last epoch end
    t_edge = np.append(t, t[-1] + EPOCH_DURATION_S / 3600.0)

    fig, ax = plt.subplots(figsize=(12, 2.5))

    for stage_key in STAGE_ORDER:
        label_val = {v: k for k, v in LABEL_TO_STAGE.items()}[stage_key]
        y_pos = _STAGE_Y[stage_key]
        color = STAGE_COLORS[stage_key]
        mask = (labels == label_val)
        # fill_between with step='post': each fill extends from t[i] to t[i+1]
        ax.fill_between(
            t_edge[:-1], y_pos - 0.45, y_pos + 0.45,
            where=mask,
            step="post",
            color=color,
            alpha=0.85,
            linewidth=0,
        )

    # Axes formatting
    ax.set_xlim(0, 4)
    ax.set_ylim(-0.6, 2.6)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["REM", "NREM", "Wake"])
    ax.set_xlabel("Time (hours)", fontsize=11)
    ax.set_ylabel("Sleep Stage", fontsize=11)
    ax.set_title(f"Predicted Hypnogram: {recording_id}", fontsize=12, fontweight="bold")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.5))
    apply_spine_style(ax)

    ax.legend(handles=stage_legend_handles(), loc="upper right",
              fontsize=9, framealpha=0.7)

    fig.tight_layout()
    save_figure(fig, output_path, dpi=dpi)


def generate_hypnograms(predicted_labels_dir: str, output_dir: str, dpi: int) -> None:
    """Generate one hypnogram PNG per representative animal.

    Selection rule: Day1 recording for Mouse01–Mouse06.

    :param predicted_labels_dir: directory containing predicted-label CSV files
    :param output_dir: root figures directory; hypnograms saved to <output_dir>/hypnograms/
    :param dpi: output resolution
    """
    pred_dir = Path(predicted_labels_dir)
    hyp_dir = Path(output_dir) / "hypnograms"

    print("  Generating hypnograms ...")
    for mouse_id in HYPNOGRAM_ANIMALS:
        recording_id = f"{mouse_id}_{HYPNOGRAM_DAY}"
        label_file = pred_dir / f"{recording_id}.csv"
        if not label_file.exists():
            print(f"    WARNING: {label_file} not found — skipping", file=sys.stderr)
            continue
        labels, _ = load_predicted_labels(str(label_file))
        out_path = str(hyp_dir / f"{recording_id}_hypnogram.png")
        plot_hypnogram(labels, recording_id, out_path, dpi)
        print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# Figure 2: Stage percentage plots
# ---------------------------------------------------------------------------

def generate_stage_percentages(df_metrics: pd.DataFrame,
                                output_dir: str, dpi: int) -> None:
    """Generate a grouped bar chart of mean ± SEM % Wake, % NREM, % REM.

    Within-mouse average is computed first (5 recordings per mouse → 1 value
    per mouse), then mean and SEM are computed across the 10 animals.

    :param df_metrics: DataFrame loaded from sleep_metrics.csv
    :param output_dir: root figures directory; figure saved to
        <output_dir>/stage_percentages/
    :param dpi: output resolution
    """
    # Average within each mouse
    mouse_means = (
        df_metrics.groupby("mouse_id")[["pct_wake", "pct_nrem", "pct_rem"]]
        .mean()
    )

    stages_pct = ["pct_wake", "pct_nrem", "pct_rem"]
    stage_keys = ["wake", "nrem", "rem"]

    means = mouse_means[stages_pct].mean()
    sems  = mouse_means[stages_pct].sem()

    x = np.arange(3)
    bar_width = 0.5

    fig, ax = plt.subplots(figsize=(6, 5))

    bars = ax.bar(
        x, means.values, bar_width,
        color=[STAGE_COLORS[s] for s in stage_keys],
        yerr=sems.values,
        capsize=5,
        error_kw={"linewidth": 1.5, "ecolor": "black"},
        alpha=0.85,
        zorder=2,
    )

    # Overlay individual mouse data points
    rng = np.random.default_rng(42)
    for xi, col in enumerate(stages_pct):
        jitter = rng.uniform(-0.1, 0.1, size=len(mouse_means))
        ax.scatter(
            np.full(len(mouse_means), xi) + jitter,
            mouse_means[col].values,
            color="black",
            s=25,
            zorder=3,
            alpha=0.7,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([STAGE_LABELS[s] for s in stage_keys], fontsize=12)
    ax.set_ylabel("Percentage of Recording (%)", fontsize=11)
    ax.set_title("Sleep Stage Proportions\n(mean ± SEM across 10 mice)",
                 fontsize=12, fontweight="bold")
    ax.set_ylim(0, 80)
    apply_spine_style(ax)

    out_path = str(Path(output_dir) / "stage_percentages" / "stage_percentages.png")
    fig.tight_layout()
    save_figure(fig, out_path, dpi=dpi)
    print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# Figure 3: Bout duration plots
# ---------------------------------------------------------------------------

def generate_bout_duration_plots(df_metrics: pd.DataFrame,
                                  output_dir: str, dpi: int) -> None:
    """Generate grouped box plots of mean bout duration per stage.

    Within-mouse average is computed first, then individual mouse values
    are shown as box plots (one box per stage).

    :param df_metrics: DataFrame loaded from sleep_metrics.csv
    :param output_dir: root figures directory; figure saved to
        <output_dir>/bout_analysis/
    :param dpi: output resolution
    """
    bout_cols = ["wake_mean_bout_s", "nrem_mean_bout_s", "rem_mean_bout_s"]
    stage_keys = ["wake", "nrem", "rem"]

    # Average within each mouse
    mouse_means = (
        df_metrics.groupby("mouse_id")[bout_cols].mean()
    )

    fig, ax = plt.subplots(figsize=(6, 5))

    bp = ax.boxplot(
        [mouse_means[col].dropna().values for col in bout_cols],
        patch_artist=True,
        widths=0.5,
        medianprops={"color": "black", "linewidth": 2},
        whiskerprops={"linewidth": 1.5},
        capprops={"linewidth": 1.5},
        flierprops={"marker": "o", "markersize": 4, "alpha": 0.5},
    )

    for patch, stage_key in zip(bp["boxes"], stage_keys):
        patch.set_facecolor(STAGE_COLORS[stage_key])
        patch.set_alpha(0.75)

    # Overlay individual mouse data points
    rng = np.random.default_rng(42)
    for xi, (col, stage_key) in enumerate(zip(bout_cols, stage_keys), start=1):
        vals = mouse_means[col].dropna().values
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(
            np.full(len(vals), xi) + jitter,
            vals,
            color="black",
            s=25,
            zorder=3,
            alpha=0.7,
        )

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels([STAGE_LABELS[s] for s in stage_keys], fontsize=12)
    ax.set_ylabel("Mean Bout Duration (s)", fontsize=11)
    ax.set_title("Mean Bout Duration by Stage\n(per-mouse averages, n=10 mice)",
                 fontsize=12, fontweight="bold")
    apply_spine_style(ax)

    out_path = str(Path(output_dir) / "bout_analysis" / "bout_duration.png")
    fig.tight_layout()
    save_figure(fig, out_path, dpi=dpi)
    print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# Figure 4: Aggregate confusion matrix
# ---------------------------------------------------------------------------

def generate_confusion_matrix(df_val: pd.DataFrame,
                               output_dir: str, dpi: int) -> None:
    """Generate a 3×3 aggregate confusion matrix heatmap.

    Sums counts across all 50 recordings, then normalizes each row to
    row percentages.  Rows = expert label; columns = predicted label.
    Order: Wake, NREM, REM.

    :param df_val: DataFrame loaded from validation_summary.csv
    :param output_dir: root figures directory; figure saved to
        <output_dir>/validation/
    :param dpi: output resolution
    """
    # Build summed 3×3 matrix in order: Wake, NREM, REM
    # Column naming in CSV: cm_true_<from>_pred_<to> where from/to ∈ {wake, nrem, rem}
    cm = np.zeros((3, 3), dtype=np.int64)
    for i, true_stage in enumerate(CM_STAGES):
        for j, pred_stage in enumerate(CM_STAGES):
            col = f"cm_true_{true_stage}_pred_{pred_stage}"
            cm[i, j] = int(df_val[col].sum())

    # Row-normalize to percentages
    row_sums = cm.sum(axis=1, keepdims=True)
    cm_pct = np.where(row_sums > 0, cm / row_sums * 100, 0.0)

    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm_pct, cmap="Blues", vmin=0, vmax=100)

    # Annotate cells
    for i in range(3):
        for j in range(3):
            val = cm_pct[i, j]
            text_color = "white" if val > 55 else "black"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=12, color=text_color, fontweight="bold")

    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(CM_LABELS, fontsize=11)
    ax.set_yticklabels(CM_LABELS, fontsize=11)
    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.set_ylabel("Expert Label", fontsize=11)
    ax.set_title("Aggregate Confusion Matrix\n(% of expert-labeled epochs, n=50 recordings)",
                 fontsize=11, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Row %", fontsize=10)

    out_path = str(Path(output_dir) / "validation" / "confusion_matrix.png")
    fig.tight_layout()
    save_figure(fig, out_path, dpi=dpi)
    print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# Figure 5: Kappa distribution
# ---------------------------------------------------------------------------

def generate_kappa_distribution(df_val: pd.DataFrame,
                                  output_dir: str, dpi: int) -> None:
    """Generate a box plot of per-recording Cohen's kappa values.

    Individual recording data points are overlaid on the box.

    :param df_val: DataFrame loaded from validation_summary.csv
    :param output_dir: root figures directory; figure saved to
        <output_dir>/validation/
    :param dpi: output resolution
    """
    kappas = df_val["kappa"].values

    fig, ax = plt.subplots(figsize=(4, 5))

    bp = ax.boxplot(
        kappas,
        patch_artist=True,
        widths=0.4,
        medianprops={"color": "black", "linewidth": 2},
        whiskerprops={"linewidth": 1.5},
        capprops={"linewidth": 1.5},
        flierprops={"marker": "o", "markersize": 4, "alpha": 0.5},
    )
    bp["boxes"][0].set_facecolor("#aec6e8")
    bp["boxes"][0].set_alpha(0.85)

    # Overlay individual recording points
    rng = np.random.default_rng(42)
    jitter = rng.uniform(-0.08, 0.08, size=len(kappas))
    ax.scatter(
        np.ones(len(kappas)) + jitter,
        kappas,
        color="steelblue",
        s=20,
        zorder=3,
        alpha=0.7,
    )

    mean_k = kappas.mean()
    sd_k   = kappas.std()
    ax.set_xticks([1])
    ax.set_xticklabels([f"κ = {mean_k:.3f} ± {sd_k:.3f}"], fontsize=10)
    ax.set_ylabel("Cohen's Kappa", fontsize=11)
    ax.set_title("Per-Recording Kappa Distribution\n(n=50 recordings)",
                 fontsize=12, fontweight="bold")
    ax.set_ylim(0.85, 1.02)
    apply_spine_style(ax)

    out_path = str(Path(output_dir) / "validation" / "kappa_distribution.png")
    fig.tight_layout()
    save_figure(fig, out_path, dpi=dpi)
    print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# Figure 6: Transition matrix heatmap
# ---------------------------------------------------------------------------

def generate_transition_heatmap(df_metrics: pd.DataFrame,
                                  output_dir: str, dpi: int) -> None:
    """Generate a 3×3 heatmap of mean stage transition probabilities.

    The mean is computed across all 50 recordings.  Order: Wake, NREM, REM.

    :param df_metrics: DataFrame loaded from sleep_metrics.csv
    :param output_dir: root figures directory; figure saved to
        <output_dir>/transitions/
    :param dpi: output resolution
    """
    # Transition columns: trans_<from>_to_<to> where from/to ∈ {wake, nrem, rem}
    stage_keys = ["wake", "nrem", "rem"]

    mean_trans = np.zeros((3, 3))
    for i, from_s in enumerate(stage_keys):
        for j, to_s in enumerate(stage_keys):
            col = f"trans_{from_s}_to_{to_s}"
            mean_trans[i, j] = df_metrics[col].mean()

    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(mean_trans, cmap="YlOrRd", vmin=0, vmax=1)

    for i in range(3):
        for j in range(3):
            val = mean_trans[i, j]
            text_color = "white" if val > 0.6 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=12, color=text_color, fontweight="bold")

    stage_display = [STAGE_LABELS[s] for s in stage_keys]
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(stage_display, fontsize=11)
    ax.set_yticklabels(stage_display, fontsize=11)
    ax.set_xlabel("Next Stage", fontsize=11)
    ax.set_ylabel("Current Stage", fontsize=11)
    ax.set_title("Mean Stage Transition Probabilities\n(averaged across 50 recordings)",
                 fontsize=11, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Transition Probability", fontsize=10)

    out_path = str(Path(output_dir) / "transitions" / "transition_matrix.png")
    fig.tight_layout()
    save_figure(fig, out_path, dpi=dpi)
    print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(
    sleep_metrics_csv: str,
    validation_csv: str,
    predicted_labels_dir: str,
    output_dir: str,
    dpi: int,
) -> None:
    """Run the full Phase 6 figure generation pipeline.

    Loads the required CSV inputs, creates output subdirectories, and
    generates all six figure types.

    :param sleep_metrics_csv: path to ``outputs/sleep_metrics.csv``
    :param validation_csv: path to ``outputs/validation_summary.csv``
    :param predicted_labels_dir: path to ``outputs/predicted_labels/`` directory
    :param output_dir: root output directory for figures (``figures/``)
    :param dpi: output resolution in dots per inch
    :raises SystemExit: on missing input files or other errors
    """
    # Validate inputs
    for path_str, label in [
        (sleep_metrics_csv, "--sleep_metrics_csv"),
        (validation_csv, "--validation_csv"),
        (predicted_labels_dir, "--predicted_labels_dir"),
    ]:
        p = Path(path_str)
        if not p.exists():
            print(f"ERROR: {label} path not found: {p}", file=sys.stderr)
            sys.exit(1)

    # Load CSVs
    df_metrics = pd.read_csv(sleep_metrics_csv)
    df_val     = pd.read_csv(validation_csv)

    print(f"Loaded sleep_metrics.csv  : {len(df_metrics)} rows")
    print(f"Loaded validation_summary : {len(df_val)} rows")
    print(f"Output directory          : {output_dir}")
    print(f"DPI                       : {dpi}")
    print()

    # Create output subdirectories
    for subdir in ["hypnograms", "stage_percentages", "bout_analysis",
                   "validation", "transitions"]:
        (Path(output_dir) / subdir).mkdir(parents=True, exist_ok=True)

    # Figure 1: Hypnograms
    print("Figure 1: Hypnograms")
    generate_hypnograms(predicted_labels_dir, output_dir, dpi)

    # Figure 2: Stage percentage plots
    print("Figure 2: Stage percentage plots")
    generate_stage_percentages(df_metrics, output_dir, dpi)

    # Figure 3: Bout duration plots
    print("Figure 3: Bout duration plots")
    generate_bout_duration_plots(df_metrics, output_dir, dpi)

    # Figure 4: Aggregate confusion matrix
    print("Figure 4: Aggregate confusion matrix")
    generate_confusion_matrix(df_val, output_dir, dpi)

    # Figure 5: Kappa distribution
    print("Figure 5: Kappa distribution")
    generate_kappa_distribution(df_val, output_dir, dpi)

    # Figure 6: Transition matrix heatmap
    print("Figure 6: Transition matrix heatmap")
    generate_transition_heatmap(df_metrics, output_dir, dpi)

    print()
    print("=" * 60)
    print("Phase 6 complete — all figures saved.")
    print(f"Output directory: {Path(output_dir).resolve()}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse CLI arguments and run the figure generation pipeline."""
    parser = argparse.ArgumentParser(
        description=(
            "Phase 6 — Generate publication-quality figures from AccuSleePy "
            "analysis outputs. Produces hypnograms, stage proportion plots, "
            "bout duration plots, confusion matrix, kappa distribution, and "
            "transition matrix heatmap."
        )
    )
    parser.add_argument(
        "--sleep_metrics_csv",
        required=True,
        help="Path to sleep_metrics.csv from Phase 5 "
             "(e.g. AccuSleePy_Demo/outputs/sleep_metrics.csv)",
    )
    parser.add_argument(
        "--validation_csv",
        required=True,
        help="Path to validation_summary.csv from Phase 4 "
             "(e.g. AccuSleePy_Demo/outputs/validation_summary.csv)",
    )
    parser.add_argument(
        "--predicted_labels_dir",
        required=True,
        help="Path to the directory containing predicted-label CSV files from Phase 3 "
             "(e.g. AccuSleePy_Demo/outputs/predicted_labels)",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Root output directory for all figures "
             "(e.g. AccuSleePy_Demo/figures)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output resolution in dots per inch (default: 300)",
    )
    args = parser.parse_args()

    run(
        sleep_metrics_csv=args.sleep_metrics_csv,
        validation_csv=args.validation_csv,
        predicted_labels_dir=args.predicted_labels_dir,
        output_dir=args.output_dir,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
