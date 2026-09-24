"""Verification of the cleaning pipeline.

Every check below is the "Verification check" line of a decision in
docs/cleaning_decision_log.md. If the cleaning code is ever changed and a
number moves, this fails loudly instead of quietly shipping wrong figures.

Run:  python -m src.validate
"""

import pandas as pd

from src import config as cfg

E = cfg.EXPECTED


def load_clean() -> pd.DataFrame:
    return pd.read_csv(cfg.DATA_CLEAN, encoding=cfg.ENCODING)


def check(name: str, condition: bool, detail: str = "") -> bool:
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}{('  -> ' + detail) if detail and not condition else ''}")
    return condition


def run_checks(df: pd.DataFrame) -> bool:
    results = []

    # DQ-01, DQ-16 - row count
    results.append(check("DQ-01/16  1,247 rows", len(df) == E["rows"], f"got {len(df)}"))
    results.append(check(
        "DQ-01     every age within 18-75",
        df["age"].between(cfg.AGE_MIN, cfg.AGE_MAX).all(),
    ))
    answer_cols = [c for c in df.columns if c != "timestamp"]
    results.append(check(
        "DQ-16     no duplicate answer rows remain",
        df.duplicated(subset=answer_cols).sum() == 0,
    ))

    # DQ-02 - gender
    got = df["gender_clean"].value_counts().to_dict()
    results.append(check("DQ-02     gender groups 987/247/13", got == E["gender_clean"], str(got)))

    # DQ-03 - whitespace
    text_cols = df.select_dtypes(include=["object", "str"]).columns
    stripped = all(df[c].dropna().astype(str).str.strip().eq(df[c].dropna().astype(str)).all()
                   for c in text_cols)
    results.append(check("DQ-03     no leading/trailing whitespace", stripped))

    # DQ-05 - work interference
    results.append(check(
        "DQ-05     work_interfere has no blanks",
        df["work_interfere"].isna().sum() == 0,
    ))
    results.append(check(
        "DQ-05     has_condition = No for 261",
        (df["has_condition"] == "No").sum() == E["has_condition_no"],
        str((df["has_condition"] == "No").sum()),
    ))

    # DQ-06, DQ-10, DQ-11 - state
    results.append(check(
        "DQ-06     state never blank",
        df["state"].isna().sum() == 0,
    ))
    results.append(check(
        "DQ-10     no non-US row holds a real state",
        (df.loc[df["country"] != "United States", "state"] == cfg.STATE_NOT_APPLICABLE).all(),
    ))
    results.append(check(
        "DQ-11     11 US rows 'Not specified'",
        (df["state"] == cfg.STATE_NOT_SPECIFIED).sum() == E["state_not_specified"],
        str((df["state"] == cfg.STATE_NOT_SPECIFIED).sum()),
    ))

    # DQ-07, DQ-14 - employment
    got = df["employment_type"].value_counts().to_dict()
    results.append(check("DQ-14     employment types 1088/141/18",
                         got == E["employment_type"], str(got)))

    # DQ-08 - comments
    results.append(check(
        "DQ-08     160 comments kept",
        (df["has_comment"] == "Yes").sum() == E["has_comment"],
        str((df["has_comment"] == "Yes").sum()),
    ))

    # DQ-18 - survey wave
    results.append(check(
        "DQ-18     76 late-wave responses",
        (df["survey_wave"] == "Late").sum() == E["survey_wave_late"],
        str((df["survey_wave"] == "Late").sum()),
    ))

    # DQ-20 - ordered columns and scores
    results.append(check(
        "DQ-20     knows_leave_policy = No for 560",
        (df["knows_leave_policy"] == "No").sum() == E["knows_leave_policy_no"],
        str((df["knows_leave_policy"] == "No").sum()),
    ))
    results.append(check(
        "DQ-20     interfere_score set for the 986 with a condition",
        df["interfere_score"].notna().sum() == (df["has_condition"] == "Yes").sum(),
    ))
    results.append(check(
        "DQ-20     size_rank spans 1-6",
        df["size_rank"].min() == 1 and df["size_rank"].max() == 6,
    ))

    # DQ-21 - uncertainty score
    results.append(check(
        "DQ-21     uncertainty_score within 0-7",
        df["uncertainty_score"].between(0, 7).all(),
    ))

    # DQ-14 - support score is employees only
    results.append(check(
        "DQ-14     support_score only for employees",
        df["support_score"].notna().sum() == E["employees"],
        str(df["support_score"].notna().sum()),
    ))

    # DQ-28 - age bands
    results.append(check(
        "DQ-28     every row has an age band",
        df["age_group"].isna().sum() == 0,
    ))

    return all(results)


def main() -> None:
    df = load_clean()
    print(f"Validating {cfg.DATA_CLEAN.name}: {len(df)} rows x {df.shape[1]} columns\n")
    ok = run_checks(df)
    print("\nAll checks passed." if ok else "\nSOME CHECKS FAILED - do not use this file.")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
