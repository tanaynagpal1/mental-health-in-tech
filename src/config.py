"""Project configuration: paths and every constant fixed by the Phase 2 decisions.

Each constant below maps to a decision in docs/cleaning_decision_log.md.
Nothing in this file computes anything - it is the single place where the
project's rules are written down, so clean.py, validate.py, the notebook and
the dashboard all use the same definitions.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths (DQ-09: no path is ever built by string concatenation)
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "survey.csv"
DATA_CLEAN = PROJECT_ROOT / "data" / "processed" / "survey_clean.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

# --------------------------------------------------------------------------
# Loading (DQ-09)
# --------------------------------------------------------------------------
NA_VALUES = ["NA", "-", ""]          # blanks stored as text; "-" is one typed "nothing"
ENCODING = "utf-8"                   # always explicit: Windows defaults to cp1252

# --------------------------------------------------------------------------
# Row filters (DQ-01, DQ-16)
# --------------------------------------------------------------------------
AGE_MIN, AGE_MAX = 18, 75            # DQ-01: 8 rows fall outside and are dropped
EXPECTED_ROWS_RAW = 1259
EXPECTED_ROWS_CLEAN = 1247           # after 8 invalid ages + 4 resubmissions

# --------------------------------------------------------------------------
# Gender mapping (DQ-02, DQ-03, DQ-04)
# Matching happens on the stripped, lowercased value.
# --------------------------------------------------------------------------
GENDER_FEMALE = {
    "female", "f", "woman", "cis female", "female (cis)", "femake", "femail",
    "cis-female/femme", "femme",
}
GENDER_DIVERSE = {
    "non-binary", "enby", "genderqueer", "agender", "androgyne", "fluid",
    "queer", "queer/she/they", "neuter",
    # DQ-02: trans respondents are grouped here
    "female (trans)", "trans-female", "trans woman",
}
# Everything else resolves to Male: spelling variants, typos, cis-prefixed forms,
# and the 6 hedged answers ("male-ish", "guy (-ish) ^_^", "nah", ...).
GENDER_DEFAULT = "Male"

# --------------------------------------------------------------------------
# Category orders (DQ-20). The last entry of leave/work_interfere sits
# OUTSIDE the scale - it is not a point on the axis.
# --------------------------------------------------------------------------
SIZE_ORDER = ["1-5", "6-25", "26-100", "100-500", "500-1000", "More than 1000"]
LEAVE_ORDER = ["Very difficult", "Somewhat difficult", "Somewhat easy", "Very easy", "Don't know"]
INTERFERE_ORDER = ["Never", "Rarely", "Sometimes", "Often", "No condition"]

LEAVE_SCALE = {"Very difficult": 1, "Somewhat difficult": 2, "Somewhat easy": 3, "Very easy": 4}
INTERFERE_SCALE = {"Never": 1, "Rarely": 2, "Sometimes": 3, "Often": 4}

NO_CONDITION = "No condition"        # DQ-05: label for a blank work_interfere

# --------------------------------------------------------------------------
# Uncertainty (DQ-21, DQ-22)
# "Maybe" is deliberately NOT here: it is a judgement about risk, not a gap
# in knowledge.
# --------------------------------------------------------------------------
UNCERTAIN = ["Don't know", "Not sure"]
SUPPORT_QUESTIONS = [
    "benefits", "care_options", "wellness_program", "seek_help", "anonymity", "leave",
]
UNCERTAINTY_QUESTIONS = SUPPORT_QUESTIONS + ["mental_vs_physical"]   # 7 columns, score 0-7

# --------------------------------------------------------------------------
# Geography (DQ-24)
# --------------------------------------------------------------------------
MIN_N_COUNTRY = 20                   # no country figure is reported below this
MIN_N_STATE = 10

REGION_MAP = {
    "United States": "United States",
    "United Kingdom": "UK & Ireland",
    "Ireland": "UK & Ireland",
    "Canada": "Canada, Australia & NZ",
    "Australia": "Canada, Australia & NZ",
    "New Zealand": "Canada, Australia & NZ",
}
EUROPE_OTHER = {
    "Germany", "Netherlands", "France", "Switzerland", "Poland", "Sweden", "Belgium",
    "Austria", "Denmark", "Finland", "Italy", "Spain", "Norway", "Portugal", "Greece",
    "Czech Republic", "Slovenia", "Croatia", "Hungary", "Bulgaria", "Romania", "Latvia",
    "Moldova", "Bosnia and Herzegovina", "Russia", "Georgia", "Israel",
}
REGION_FALLBACK = "Rest of world"

STATE_NOT_APPLICABLE = "Not applicable"   # DQ-06: respondent is not in the US
STATE_NOT_SPECIFIED = "Not specified"     # DQ-11: US respondent who skipped the question

# --------------------------------------------------------------------------
# Age bands (DQ-28) - the top band is open-ended because only 6 respondents are 60+
# --------------------------------------------------------------------------
AGE_BINS = [17, 24, 34, 44, 75]
AGE_LABELS = ["18-24", "25-34", "35-44", "45+"]

# --------------------------------------------------------------------------
# Survey waves (DQ-18)
# --------------------------------------------------------------------------
WAVE_CUTOFF = "2014-09-30"           # responses after this date are the "Late" wave

# --------------------------------------------------------------------------
# Modelling (DQ-25, DQ-26)
# --------------------------------------------------------------------------
TARGET = "treatment"
LEAKY_FEATURES = ["work_interfere", "has_condition", "interfere_score"]

# --------------------------------------------------------------------------
# Expected results - validate.py asserts these exactly (see the log)
# --------------------------------------------------------------------------
EXPECTED = {
    "rows": 1247,
    "gender_clean": {"Male": 987, "Female": 247, "Gender-diverse": 13},
    "employment_type": {"Employee": 1088, "Self-employed": 141, "Unknown": 18},
    "has_condition_no": 261,
    "state_not_applicable": 501,
    "state_not_specified": 11,
    "knows_leave_policy_no": 560,
    "has_comment": 160,
    "survey_wave_late": 76,
    "employees": 1088,
}
