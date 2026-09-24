"""Cleaning pipeline for the Mental Health in Tech Survey.

Turns data/raw/survey.csv (1,259 rows x 27 columns) into
data/processed/survey_clean.csv (1,247 rows x 40 columns).

Every step below implements a decision recorded in docs/cleaning_decision_log.md
and is tagged with its issue id (DQ-xx). The rules themselves live in config.py,
so this file contains only the mechanics.

Run:  python -m src.clean
"""

import pandas as pd

from src import config as cfg


# ---------------------------------------------------------------------------
# Step 1 - load (DQ-09, DQ-23)
# ---------------------------------------------------------------------------
def load_raw() -> pd.DataFrame:
    """Read the raw file with every assumption stated explicitly."""
    df = pd.read_csv(
        cfg.DATA_RAW,
        na_values=cfg.NA_VALUES,   # "NA" and "-" are blanks, not answers
        keep_default_na=True,
        encoding=cfg.ENCODING,
    )
    df.columns = df.columns.str.lower()
    return df


# ---------------------------------------------------------------------------
# Step 2 - whitespace (DQ-03)
# ---------------------------------------------------------------------------
def strip_text(df: pd.DataFrame) -> pd.DataFrame:
    """Remove leading/trailing spaces from every text column."""
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].str.strip()
    return df


# ---------------------------------------------------------------------------
# Step 3 - timestamp (DQ-19)
# ---------------------------------------------------------------------------
def parse_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")
    return df


# ---------------------------------------------------------------------------
# Step 4 - invalid ages (DQ-01, DQ-29)
# ---------------------------------------------------------------------------
def drop_invalid_ages(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the 8 rows whose age is outside 18-75 (includes 2 test submissions)."""
    keep = df["age"].between(cfg.AGE_MIN, cfg.AGE_MAX)
    print(f"  DQ-01  dropping {(~keep).sum()} rows with an impossible age")
    return df.loc[keep].copy()


# ---------------------------------------------------------------------------
# Step 5 - duplicate submissions (DQ-16, DQ-17)
# ---------------------------------------------------------------------------
def drop_resubmissions(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the later row of each pair identical in all 26 answer columns.

    Rows are compared in timestamp order, so keep="first" keeps the earliest
    submission even when the file is not sorted by time.
    """
    answer_cols = [c for c in df.columns if c != "timestamp"]
    later = df.sort_values("timestamp").duplicated(subset=answer_cols, keep="first")
    drop_idx = later[later].index
    print(f"  DQ-16  dropping {len(drop_idx)} accidental resubmissions")
    return df.drop(index=drop_idx).copy()


# ---------------------------------------------------------------------------
# Step 6 - gender (DQ-02, DQ-04)
# ---------------------------------------------------------------------------
def clean_gender(df: pd.DataFrame) -> pd.DataFrame:
    """Map 44 free-text answers to Male / Female / Gender-diverse.

    Matching is done on the lowercased value; the original text is kept so any
    grouping can be audited later.
    """
    key = df["gender"].str.lower()

    def bucket(value: str) -> str:
        if value in cfg.GENDER_FEMALE:
            return "Female"
        if value in cfg.GENDER_DIVERSE:
            return "Gender-diverse"
        return cfg.GENDER_DEFAULT

    df["gender_clean"] = key.map(bucket)
    return df


# ---------------------------------------------------------------------------
# Step 7 - country / state (DQ-06, DQ-10, DQ-11)
# ---------------------------------------------------------------------------
def clean_state(df: pd.DataFrame) -> pd.DataFrame:
    """Only US respondents may hold a state; everyone else is 'Not applicable'."""
    is_us = df["country"] == "United States"
    df.loc[~is_us, "state"] = cfg.STATE_NOT_APPLICABLE          # DQ-10: clears 3 stray values
    df.loc[is_us & df["state"].isna(), "state"] = cfg.STATE_NOT_SPECIFIED  # DQ-11
    return df


# ---------------------------------------------------------------------------
# Step 8 - region (DQ-24)
# ---------------------------------------------------------------------------
def add_region(df: pd.DataFrame) -> pd.DataFrame:
    def to_region(country: str) -> str:
        if country in cfg.REGION_MAP:
            return cfg.REGION_MAP[country]
        if country in cfg.EUROPE_OTHER:
            return "Europe (other)"
        return cfg.REGION_FALLBACK

    df["region"] = df["country"].map(to_region)
    return df


# ---------------------------------------------------------------------------
# Step 9 - work interference (DQ-05)
# ---------------------------------------------------------------------------
def clean_work_interfere(df: pd.DataFrame) -> pd.DataFrame:
    """A blank means 'the question did not apply', i.e. no condition."""
    df["has_condition"] = df["work_interfere"].notna().map({True: "Yes", False: "No"})
    df["work_interfere"] = df["work_interfere"].fillna(cfg.NO_CONDITION)
    return df


# ---------------------------------------------------------------------------
# Step 10 - employment type (DQ-14)
# ---------------------------------------------------------------------------
def add_employment_type(df: pd.DataFrame) -> pd.DataFrame:
    """Employee / Self-employed / Unknown - the filter for employer questions."""
    df["employment_type"] = (
        df["self_employed"].map({"No": "Employee", "Yes": "Self-employed"}).fillna("Unknown")
    )
    return df


# ---------------------------------------------------------------------------
# Step 11 - ordered categories and their numeric scores (DQ-20)
# ---------------------------------------------------------------------------
def add_ordered_categories(df: pd.DataFrame) -> pd.DataFrame:
    df["no_employees"] = pd.Categorical(df["no_employees"], categories=cfg.SIZE_ORDER, ordered=True)
    df["leave"] = pd.Categorical(df["leave"], categories=cfg.LEAVE_ORDER, ordered=True)
    df["work_interfere"] = pd.Categorical(
        df["work_interfere"], categories=cfg.INTERFERE_ORDER, ordered=True
    )

    df["size_rank"] = df["no_employees"].cat.codes + 1                    # 1-6
    df["leave_score"] = df["leave"].astype(str).map(cfg.LEAVE_SCALE)      # blank for "Don't know"
    df["interfere_score"] = df["work_interfere"].astype(str).map(cfg.INTERFERE_SCALE)
    df["knows_leave_policy"] = (
        df["leave"].astype(str).ne("Don't know").map({True: "Yes", False: "No"})
    )
    return df


# ---------------------------------------------------------------------------
# Step 12 - age bands (DQ-28)
# ---------------------------------------------------------------------------
def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
    df["age_group"] = pd.cut(df["age"], bins=cfg.AGE_BINS, labels=cfg.AGE_LABELS)
    return df


# ---------------------------------------------------------------------------
# Step 13 - comments (DQ-08)
# ---------------------------------------------------------------------------
def add_comment_flag(df: pd.DataFrame) -> pd.DataFrame:
    df["has_comment"] = df["comments"].notna().map({True: "Yes", False: "No"})
    return df


# ---------------------------------------------------------------------------
# Step 14 - survey wave (DQ-18)
# ---------------------------------------------------------------------------
def add_survey_wave(df: pd.DataFrame) -> pd.DataFrame:
    late = df["timestamp"] > pd.Timestamp(cfg.WAVE_CUTOFF) + pd.Timedelta(days=1)
    df["survey_wave"] = late.map({True: "Late", False: "Main"})
    return df


# ---------------------------------------------------------------------------
# Step 15 - the two summary scores (DQ-21, DQ-14)
# ---------------------------------------------------------------------------
def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    """uncertainty_score: how much the respondent does NOT know (0-7).
    support_score:     how much the employer provides (0-6), employees only.
    "Maybe" is deliberately not counted as uncertainty - it is a risk judgement.
    """
    uncertain = df[cfg.UNCERTAINTY_QUESTIONS].astype(str).isin(cfg.UNCERTAIN)
    df["uncertainty_score"] = uncertain.sum(axis=1)

    support = df[cfg.SUPPORT_YES_QUESTIONS].astype(str).eq("Yes").sum(axis=1)
    support = support + df["leave"].astype(str).isin(cfg.LEAVE_POSITIVE).astype(int)
    df["support_score"] = support.where(df["employment_type"] == "Employee")
    return df


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def build_clean_dataset() -> pd.DataFrame:
    df = load_raw()
    print(f"Loaded {len(df)} rows x {df.shape[1]} columns")

    df = strip_text(df)
    df = parse_timestamp(df)
    df = drop_invalid_ages(df)
    df = drop_resubmissions(df)

    df = clean_gender(df)
    df = clean_state(df)
    df = add_region(df)
    df = clean_work_interfere(df)
    df = add_employment_type(df)
    df = add_ordered_categories(df)
    df = add_age_group(df)
    df = add_comment_flag(df)
    df = add_survey_wave(df)
    df = add_scores(df)

    print(f"Clean  {len(df)} rows x {df.shape[1]} columns")
    return df


def main() -> None:
    df = build_clean_dataset()
    cfg.DATA_CLEAN.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.DATA_CLEAN, index=False, encoding=cfg.ENCODING)
    print(f"Saved  {cfg.DATA_CLEAN}")


if __name__ == "__main__":
    main()
