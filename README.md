# Mental Health in Tech Survey — Analysis & Dashboard

Analysis of the 2014 OSMI *Mental Health in Tech Survey* (1,259 responses, 27 questions):
how common mental health conditions are among tech workers, how workplaces support them,
and what predicts whether someone seeks treatment.

**Deliverables:** a reproducible cleaning pipeline, an EDA notebook, and a Streamlit dashboard.

## Project structure

```
.
├── data/
│   ├── raw/survey.csv              # original file, never modified
│   └── processed/survey_clean.csv  # output of the cleaning pipeline
├── src/
│   ├── config.py                   # paths, category orders, cleaning constants
│   ├── clean.py                    # the cleaning pipeline (29 logged decisions)
│   └── validate.py                 # assertions that prove the cleaning worked
├── notebooks/                      # EDA
├── reports/figures/                # exported charts
├── docs/                           # decision log, data dictionary
├── streamlit_app.py                # dashboard entry point
└── requirements.txt                # runtime dependencies
```

## Setup

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python -m src.clean          # raw -> data/processed/survey_clean.csv
python -m src.validate       # verify every cleaning rule held
streamlit run streamlit_app.py
```

## Data quality

Every cleaning decision is recorded in [`docs/cleaning_decision_log.md`](docs/cleaning_decision_log.md):
the evidence, the options considered, the decision, the reasoning and a verification check.
A one-page summary of all 29 issues is in [`docs/all_29_decisions.md`](docs/all_29_decisions.md),
and the column reference is in [`docs/data_dictionary.md`](docs/data_dictionary.md).

Headline effects of cleaning: **1,259 -> 1,247 rows** (8 invalid ages, 4 accidental resubmissions),
**27 -> 40 columns** (13 derived). No value is imputed; every fill is a label for a meaning the blank already carried.

Two denominators are stated on every chart: **1,247** overall, **1,088** for employer-support questions
(self-employed respondents have no employer).

## Source

Open Sourcing Mental Illness (OSMI), 2014 survey. Findings describe these 1,247 volunteer
respondents, not tech workers in general.
