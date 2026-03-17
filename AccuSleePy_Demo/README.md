# AccuSleePy Demo

Automated sleep staging of a publicly available rodent EEG/EMG dataset using
[AccuSleePy](https://github.com/zekebarger/AccuSleePy). This package contains
all scripts, outputs, figures, and a written report needed to understand and
reproduce the full analysis.

---

## Dataset

**Source:** Barger, Z., Frye, C. G., Liu, D., Dan, Y., & Bouchard, K. E. (2019).
Robust, automated sleep scoring by a compact neural network with distributional
shift correction. *PLOS ONE*, 14(12), 1–18.
<https://doi.org/10.1371/journal.pone.0224642>

**OSF repository:** <https://osf.io/py5eb/>

**Local data path (not distributed with this package):**
`C:\Datasets\AccuSleePy_Data`

10 C57BL/6 mice × 5 four-hour daytime recordings = 50 recordings, 288,000
epochs total. EEG and EMG sampled at 512 Hz; epoch length 2.5 s.

---

## Pre-trained Model

**Model file (not distributed with this package):**
`C:\Datasets\models\ssann_2(5)s.pth`

This is AccuSleePy's 2.5-second epoch model, matching the epoch length used in
the dataset.

---

## Environment Setup

A Python 3.11 virtual environment is required. From the **project root** (one
level above this folder):

```bash
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r AccuSleePy_Demo/requirements.txt
```

All subsequent commands assume the virtual environment is activated.

---

## Running the Pipeline

Run the scripts in order. Each script writes its outputs to the paths shown
below and prints progress to stdout.

### Step 1 — Data Inspection

```bash
python AccuSleePy_Demo/scripts/01_data_inspection.py \
  --data_dir C:\Datasets\AccuSleePy_Data
```

**Expected output:**
- Console summary of all 50 recordings (file sizes, shapes, label distribution)
- `AccuSleePy_Demo/outputs/data_info.txt` — full inspection report mirroring stdout

---

### Step 2 — AccuSleePy Scoring

```bash
python AccuSleePy_Demo/scripts/02_accusleepy_scoring.py \
  --data_dir C:\Datasets\AccuSleePy_Data \
  --model_path C:\Datasets\models\ssann_2(5)s.pth \
  --output_dir AccuSleePy_Demo/outputs/predicted_labels
```

**Expected output (100 files):**
- `AccuSleePy_Demo/outputs/predicted_labels/<recording_id>.csv` — predicted
  label (brain_state) and confidence score per epoch (5,760 rows each)
- `AccuSleePy_Demo/outputs/predicted_labels/<recording_id>_calibration_indices.csv`
  — 360 calibration epoch indices (120 per stage, distributed) per recording

Runtime: approximately 10–20 minutes for all 50 recordings.

---

### Step 3 — Quality Control

```bash
python AccuSleePy_Demo/scripts/03_quality_control.py \
  --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \
  --output_dir AccuSleePy_Demo
```

**Expected output:**
- `AccuSleePy_Demo/QC_report.md` — flags for recordings with unusual stage
  proportions or long unbroken runs; low-confidence epoch summary
- `AccuSleePy_Demo/low_confidence_epochs/<recording_id>_low_confidence.csv`
  (50 files) — per-recording list of epochs with confidence score ≤ 0.8

---

### Step 4 — Validation Against Expert Labels

```bash
python AccuSleePy_Demo/scripts/04_validation.py \
  --data_dir C:\Datasets\AccuSleePy_Data \
  --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \
  --output_dir AccuSleePy_Demo/outputs
```

**Expected output:**
- `AccuSleePy_Demo/outputs/validation_summary.csv` — per-recording Cohen's
  kappa, accuracy, per-class precision/recall/F1, and confusion matrix counts
- Console: aggregate mean ± SD kappa and accuracy across all 50 recordings

Calibration epochs (360 per recording) are excluded from this comparison.

---

### Step 5 — Descriptive Sleep Metrics

```bash
python AccuSleePy_Demo/scripts/05_sleep_metrics.py \
  --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \
  --output_path AccuSleePy_Demo/outputs/sleep_metrics.csv
```

**Expected output:**
- `AccuSleePy_Demo/outputs/sleep_metrics.csv` — 50 rows × 26 columns: stage
  proportions, bout statistics (mean/max duration, count) per stage, state
  transition probability matrix, low-confidence epoch counts

---

### Step 6 — Figure Generation

```bash
python AccuSleePy_Demo/scripts/06_figures.py \
  --sleep_metrics_csv AccuSleePy_Demo/outputs/sleep_metrics.csv \
  --validation_csv AccuSleePy_Demo/outputs/validation_summary.csv \
  --predicted_labels_dir AccuSleePy_Demo/outputs/predicted_labels \
  --output_dir AccuSleePy_Demo/figures
```

**Expected output (11 PNG files at 300 DPI):**

| File | Description |
|------|-------------|
| `figures/hypnograms/Mouse01_Day1_hypnogram.png` | Hypnogram for Mouse01, Day1 |
| `figures/hypnograms/Mouse02_Day1_hypnogram.png` | Hypnogram for Mouse02, Day1 |
| `figures/hypnograms/Mouse03_Day1_hypnogram.png` | Hypnogram for Mouse03, Day1 |
| `figures/hypnograms/Mouse04_Day1_hypnogram.png` | Hypnogram for Mouse04, Day1 |
| `figures/hypnograms/Mouse05_Day1_hypnogram.png` | Hypnogram for Mouse05, Day1 |
| `figures/hypnograms/Mouse06_Day1_hypnogram.png` | Hypnogram for Mouse06, Day1 |
| `figures/stage_percentages/stage_percentages.png` | Group-level % Wake / NREM / REM |
| `figures/bout_analysis/bout_duration.png` | Mean bout duration by stage |
| `figures/validation/confusion_matrix.png` | Aggregate 3×3 confusion matrix |
| `figures/validation/kappa_distribution.png` | Per-recording kappa distribution |
| `figures/transitions/transition_matrix.png` | Mean state transition heatmap |

---

## Folder Structure

```
AccuSleePy_Demo/
├── README.md                         ← This file
├── requirements.txt                  ← Pinned Python dependencies
├── .gitignore                        ← Excludes __pycache__, *.pyc, .DS_Store
├── data_guide.md                     ← Authoritative dataset reference
├── QC_report.md                      ← Quality control flags
├── scripts/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_loading.py           ← EEG/EMG/label loading functions
│   │   ├── metrics.py                ← Cohen's kappa, F1, accuracy, confusion matrix
│   │   └── plotting.py               ← Shared figure utilities and stage colors
│   ├── 01_data_inspection.py         ← Dataset summary and verification
│   ├── 02_accusleepy_scoring.py      ← AccuSleePy scoring for all 50 recordings
│   ├── 03_quality_control.py         ← Stage proportion and confidence QC
│   ├── 04_validation.py              ← Validation against expert labels
│   ├── 05_sleep_metrics.py           ← Descriptive sleep architecture metrics
│   └── 06_figures.py                 ← Publication-quality figure generation
├── outputs/
│   ├── data_info.txt                 ← Dataset inspection report
│   ├── predicted_labels/             ← 50 scoring CSVs + 50 calibration index CSVs
│   ├── sleep_metrics.csv             ← Per-recording sleep architecture metrics
│   └── validation_summary.csv        ← Per-recording validation metrics
├── figures/
│   ├── hypnograms/                   ← 6 hypnogram PNGs
│   ├── stage_percentages/            ← Stage proportion summary figure
│   ├── bout_analysis/                ← Bout duration figure
│   ├── validation/                   ← Confusion matrix and kappa distribution
│   └── transitions/                  ← Transition matrix heatmap
├── low_confidence_epochs/            ← 50 per-recording low-confidence CSVs
└── report/
    ├── report.tex                    ← LaTeX source
    └── report.pdf                    ← Compiled final report
```

---

## Key Results

| Metric | Value |
|--------|-------|
| Mean Cohen's kappa | 0.9490 ± 0.0148 |
| Mean accuracy | 97.25 ± 0.72% |
| Wake F1 | 0.9623 |
| NREM F1 | 0.9763 |
| REM F1 | 0.9754 |
| Mean % Wake | 34.53 ± 7.76% |
| Mean % NREM | 54.64 ± 6.16% |
| Mean % REM | 10.83 ± 2.18% |
| Recordings flagged in QC | 0 / 50 |
| Total low-confidence epochs | 481 / 288,000 (0.167%) |

---

## Citation

If you use this analysis or the dataset, please cite:

> Barger, Z., Frye, C. G., Liu, D., Dan, Y., & Bouchard, K. E. (2019).
> Robust, automated sleep scoring by a compact neural network with distributional
> shift correction. *PLOS ONE*, 14(12), 1–18.
> <https://doi.org/10.1371/journal.pone.0224642>

> Barger, Z., & Frye, C. (2025, June 6). AccuSleep. <https://doi.org/10.17605/OSF.IO/PY5EB>
