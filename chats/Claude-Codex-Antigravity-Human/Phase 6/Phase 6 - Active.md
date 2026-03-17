# Phase 6

**Date Started:** 2026-03-16


**Randy:**

Let's get started on Phase 6. Claude I will once again have you complete all the tasks for Phase 6. Codex and Antigravity will check the work to make sure all gates are passed and that it adheres to the standards of reproducibility and portability, scientific best practices and software engineering best practices set out in Project Details.md. Codex, Antigravity and I must explicitly approve the work before we move on to Phase 7.

---

**Claude (Session 8) — Phase 6 Plan:**

Understood, Randy. I also note that the Phase 5 chat has been concluded (renamed to `Phase 5 - Concluded.md` with a `Summary.md` created) as requested.

I will now complete Phase 6 (Figure Generation). Here is my plan:

**Files to create:**
- `AccuSleePy_Demo/scripts/utils/plotting.py` — shared constants and helpers (colors, save_figure)
- `AccuSleePy_Demo/scripts/06_figures.py` — all six figure types

**CLI for 06_figures.py:**
```
venv\Scripts\python.exe AccuSleePy_Demo/scripts/06_figures.py \
  --sleep_metrics_csv AccuSleePy_Demo/outputs/sleep_metrics.csv \
  --validation_csv AccuSleePy_Demo/outputs/validation_summary.csv \
  --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \
  --output_dir AccuSleePy_Demo/figures
```

**Six figure types:**
1. Hypnograms (`figures/hypnograms/`) — Day1 recording for Mouse01–Mouse06 (6 animals); x-axis = time in hours, y-axis = stage; colored segments (Wake=green, NREM=blue, REM=red)
2. Stage percentage plots (`figures/stage_percentages/`) — bar chart with SEM error bars + individual mouse data points; within-mouse average first
3. Bout duration plots (`figures/bout_analysis/`) — grouped box plots of mean bout duration per stage; within-mouse average first
4. Aggregate confusion matrix (`figures/validation/`) — summed 3×3 across all 50 recordings, row-normalized to percentages
5. Kappa distribution (`figures/validation/`) — box plot with individual recording data points overlaid
6. Transition matrix heatmap (`figures/transitions/`) — mean 3×3 transition probabilities across all recordings

**Standards:** PNG at 300 DPI, labeled axes, titles, Wake=green / NREM=blue / REM=red throughout.

Proceeding with implementation now.

---

**Claude (Session 8) — Phase 6 Complete:**

Phase 6 (Figure Generation) is complete. All six figure types have been generated and verified.

**Files written:**

- `AccuSleePy_Demo/scripts/utils/plotting.py` — shared constants (`STAGE_COLORS`, `STAGE_LABELS`, `STAGE_ORDER`, `LABEL_TO_STAGE`, `EPOCH_DURATION_S`) and helpers (`stage_color`, `stage_legend_handles`, `save_figure`, `apply_spine_style`)
- `AccuSleePy_Demo/scripts/06_figures.py` — all six figure generation functions with argparse CLI

**Figures produced (11 PNG files total):**

| Figure | Path | Description |
|--------|------|-------------|
| Hypnograms (×6) | `figures/hypnograms/MouseXX_Day1_hypnogram.png` | Mouse01–Mouse06, Day1; step-filled colored segments |
| Stage percentages | `figures/stage_percentages/stage_percentages.png` | Bar chart, mean ± SEM, individual mouse points |
| Bout duration | `figures/bout_analysis/bout_duration.png` | Grouped box plots, individual mouse points |
| Confusion matrix | `figures/validation/confusion_matrix.png` | 3×3 heatmap, row-normalized % |
| Kappa distribution | `figures/validation/kappa_distribution.png` | Box plot with individual recording points |
| Transition heatmap | `figures/transitions/transition_matrix.png` | Mean 3×3 probabilities |

**Run command:**
```
venv\Scripts\python.exe AccuSleePy_Demo/scripts/06_figures.py \
  --sleep_metrics_csv AccuSleePy_Demo/outputs/sleep_metrics.csv \
  --validation_csv AccuSleePy_Demo/outputs/validation_summary.csv \
  --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \
  --output_dir AccuSleePy_Demo/figures
```

**Implementation details:**

- **Hypnograms:** `fill_between` with `step='post'` for each stage; y-axis: Wake=2, NREM=1, REM=0 (top-to-bottom convention matching published hypnograms). Selection rule: Day1 for Mouse01–Mouse06.
- **Stage percentages:** Within-mouse average first (5 recordings → 1 per mouse); then mean ± SEM across 10 mice; individual mouse points overlaid with jitter.
- **Bout durations:** Same within-mouse aggregation strategy; box plots with individual mouse points overlaid.
- **Confusion matrix:** Columns `cm_true_<stage>_pred_<stage>` from `validation_summary.csv` summed across all 50 recordings; row-normalized; stage order: Wake, NREM, REM.
- **Kappa distribution:** Direct box plot from all 50 per-recording kappa values; mean ± SD shown on x-axis tick label.
- **Transition heatmap:** Mean of `trans_<from>_to_<to>` columns from `sleep_metrics.csv` across all 50 recordings.

**Phase 6 gate conditions:**
- ✅ All six figure types generated and saved in the correct subdirectories
- ✅ All figures are PNG at 300 DPI with labeled axes and clear titles
- ✅ Consistent stage colors: Wake=green, NREM=blue, REM=red throughout

Randy, Codex, Antigravity — I am done with Phase 6. Ending my session.