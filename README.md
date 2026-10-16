# Shark Tank: Deal or No Deal?

A small Python foundation for a confidence-based pitch prediction game. Users will
predict whether a pitch received a deal, then compare their confidence with the
recorded outcome. This first milestone validates real source data and scores a
prediction. It has no web app, trained model, accounts or deployment yet.

The implementation and learning guide were prepared with Codex assistance. User
understanding and independent contributions are tracked separately from generated code.

## Try the scoring function

Python 3.11 or 3.12; no third-party packages required. Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -c 'from sharktank.scoring import brier_score; print(brier_score(0.75, 1))'
```

The second command returns `0.0625`. This is a synthetic example: a 75% prediction
of a deal when the recorded outcome is a deal. Brier loss is `(probability - outcome)^2`;
lower is better. Use probabilities from 0 to 1, not percentages from 0 to 100.

## Real data, with a reproducible audit

Source: [thirumani's Shark Tank US dataset on Kaggle](https://www.kaggle.com/datasets/thirumani/shark-tank-us-dataset).
Its API metadata reported **CC0: Public Domain**, version **34**, when accessed on
October 16, 2026. That snapshot contains **1,485 records and 53 columns**, covering
seasons 1-17, with only 44 season-17 records. It is a partial season snapshot.

The validator accepts **1,481 rows**. Four rows lack the outcome, original ask and
offered equity; they are quarantined, never interpreted as “no deal.” Accepted rows
contain 914 recorded deals and 567 recorded no-deals. These are dataset counts,
not model accuracy, real user activity or independent factual validation.

Raw files stay outside Git. To reproduce the local audit:

```sh
mkdir -p data/raw
curl -fL 'https://www.kaggle.com/api/v1/datasets/download/thirumani/shark-tank-us-dataset?datasetVersionNumber=34' -o data/raw/shark-tank-v34.zip
python3 -m sharktank.audit data/raw/shark-tank-v34.zip
```

The audit stops if either the archive or CSV checksum differs from the pinned
[manifest](data/manifest.json). It reads the CSV inside the ZIP without extracting
files. [Recorded audit](reports/dataset-audit-2026-10-16.json).

The dataset creator deserves source credit. Kaggle's licence label does not grant
rights to TV videos, trademarks or logos; none are included. Recorded on-show deal
labels do not establish that funding closed after filming. No row-by-row independent
label review has been completed.

## What the code does

```text
Pinned ZIP -> checksum/schema checks -> valid rows + quarantine reasons
                                       |
                                       +-> public pitch fields (before reveal)
                                       +-> separate outcome (after reveal)
Probability + recorded outcome -> Brier loss
```

- `sharktank/data.py`: typed pitch data, explicit pre-reveal fields and validation.
- `sharktank/scoring.py`: one binary Brier-loss calculation with strict inputs.
- `sharktank/audit.py`: checksums, column checks and a dataset summary.
- `tests/`: scoring boundaries, missing labels, invalid data, duplicate IDs,
  outcome leakage and altered archives. Fixtures are labelled synthetic.

Only pitch ID, season, episode, startup, industry, original ask and offered equity
enter the pre-reveal representation. Final deal amounts, investing sharks, guest
names, deal equity and every unknown source column are excluded. This is a Python
data boundary tested here, not a claim about a web API that does not yet exist.

Before any future model: split by season, fit preprocessing on training data only,
compare with a constant-probability baseline and evaluate on untouched later
seasons. Startup IDs/names also require review for memorization and repeat-company
leakage; being visible before a reveal does not automatically make a field suitable
as a model feature. No model or held-out evaluation is part of this milestone.

Start with the [15-minute learning guide](docs/LEARN_FIRST_SLICE.md). The next
subsystem waits until this slice has been reviewed and a small exercise attempted.
