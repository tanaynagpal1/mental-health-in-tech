# All 29 Data Issues — Problem and Decided Fix

Mental Health in Tech Survey (OSMI 2014) · `survey.csv` · Phase 2 complete
**1,259 rows → 1,247 rows · 27 columns → 40 columns**

---

## A. Invalid values

| ID | The problem | The fix we decided |
|---|---|---|
| **DQ-01** | 8 impossible ages: -1726, -29, -1, 5, 8, 11, 329, 99999999999. Raw mean age came out as 79 million. | **Drop all 8 rows** (age outside 18–75). One simple rule; an invalid age casts doubt on the rest of that response. Headline figures unchanged (treatment 50.6% → 50.5%). |
| **DQ-02** | `Gender` was a free-text box: 44 different spellings, from "M" and "maile" to "Genderqueer" and "Nah". | New **`gender_clean`**: Male 987 · Female 247 · **Gender-diverse** 13. Typos merged; 6 hedged answers ("Male-ish", "Guy (-ish) ^_^") read as Male; the 4 trans respondents grouped as Gender-diverse. Original text kept for audit. |
| **DQ-03** | Trailing spaces: "Male " counted as a separate value from "Male". | **Strip whitespace** from every text column before any matching. |
| **DQ-04** | Mixed capitalisation split the same answer ("Male" / "male"). | **Lowercase before matching** in the cleaning code. |
| **DQ-29** | 2 rows answered "Yes" to all 17 Yes/No questions — the only two in the dataset. One comment read "password: testered". | **No separate action**: both are removed by the DQ-01 age rule. Recorded as evidence of straight-lining. |

## B. Missing values — each blank has a different cause

| ID | The problem | The fix we decided |
|---|---|---|
| **DQ-05** | `work_interfere` blank for 262 people. The question only applies "*if you have a condition*", so the blank is an answer, not lost data — 98.5% of them never sought treatment. | Label the blanks **"No condition"** and derive **`has_condition`** (Yes 986 / No 261). Rejected merging into "Never" — those groups differ (2% vs 14% treatment). |
| **DQ-06** | `state` blank for 509: 498 non-US (question didn't apply) and 11 US respondents who skipped it. | **"Not applicable"** for non-US, **"Not specified"** for the 11. All state charts run on the **US subset (746)** and say so. |
| **DQ-07** | `self_employed` blank for 18 — exactly the first 18 responses, submitted before the question was added (11:34:53 cut-off). | **Leave blank**, exclude from self-employment charts (n = 1,229). A Naive Bayes imputation test scored *below* the majority baseline, so imputation was rejected on evidence. |
| **DQ-08** | `comments` blank for 1,090 (87%), and commenters are unrepresentative (64.6% treatment vs 48.4%). | **Leave blank**, add **`has_comment`**. Comments quoted illustratively only, never counted. |
| **DQ-09** | 1,892 blanks stored as the literal text "NA"; one comment is "-". | Load explicitly: `na_values=["NA", "-", ""]`, and **lowercase all column names**. |

## C. Contradictions

| ID | The problem | The fix we decided |
|---|---|---|
| **DQ-10** | 3 non-US respondents gave a US state (Latvia→NY, Israel→MD, Bulgaria→UT). | **Clear the state, keep the country.** Row 488's comment describes Israel's health system, confirming the country is right. |
| **DQ-11** | 11 US respondents gave no state. | **Label "Not specified"**; they stay in all US analysis. Enforced rule: only US rows may hold a state. |
| **DQ-12** | 4 people sought treatment but skipped the interference question. | **No override** — they follow the DQ-05 rule. Most likely a past condition now resolved. 0.3% of rows. |
| **DQ-13** | 9 self-employed people report a company of 100+ employees. | **Keep both answers.** Ambiguous, not wrong: a contractor may describe the client's size. |
| **DQ-14** | 141 self-employed people answered 6 questions about "your employer" — but they are the employer. Including them inflates "no benefits" by 4.5pp. | The 6 employer-support questions are analysed on **employees only (n = 1,088)**, via a derived **`employment_type`**. No data edited. |
| **DQ-15** | 141 said "no benefits" but "yes, I know the care options" — apparently contradictory. | **Valid, no change.** Different questions: you can know your employer offers nothing. Self-employed are 31% of this group; the mirror case (benefits yes, options unknown) exists for 91 people. |

## D. Duplicates

| ID | The problem | The fix we decided |
|---|---|---|
| **DQ-16** | 4 pairs identical across all 26 answer columns, submitted 12 seconds to 5 minutes apart. | **Keep the first submission, drop the later one** (rows 821, 859, 1134, 1218). Treatment rate identical either way. |
| **DQ-17** | 13 rows share a timestamp with another row. | **Keep all** — their answers differ (different countries, ages). Two people submitting in the same second. |

## E. Structure and encoding

| ID | The problem | The fix we decided |
|---|---|---|
| **DQ-18** | 76 responses arrived Oct 2014 – Feb 2015, and they differ: 63.2% treatment vs 49.7%. | **Keep all**, add **`survey_wave`** (Main 1,171 / Late 76). The difference is composition (38% US vs 61%), not time. Sensitivity check both ways. |
| **DQ-19** | `Timestamp` stored as text. | Parse with an **explicit format** so malformed values raise. Derive only `survey_wave` — a one-month survey has no seasonality. |
| **DQ-20** | 3 columns have a natural order but sort alphabetically, e.g. "1-5, 100-500, 26-100, 500-1000, 6-25". Benefits rise 9.7% → 65.6% across company size, and alphabetical order hides it completely. | **Ordered categoricals** for `no_employees`, `leave`, `work_interfere`, with "Don't know"/"No condition" parked outside the order, plus numeric **`size_rank`** (1–6), **`leave_score`** (1–4), **`interfere_score`** (1–4) and **`knows_leave_policy`**. |
| **DQ-21** | "Don't know" / "Not sure" / "Maybe" fill 11 columns — 813 in `anonymity` alone (65%). Treating them as missing would gut the data. | **Keep as real answers** and derive **`uncertainty_score`** (0–7). Treatment-seeking falls **61.8% → 26.9%** as uncertainty rises — a finding, not a caveat. |
| **DQ-22** | The same idea worded three ways across columns. | **Keep the survey's wording**; use one code constant `UNCERTAIN = ["Don't know", "Not sure"]`. **"Maybe" excluded** — it's a risk judgement, not a knowledge gap. |
| **DQ-23** | "Bahamas, The" contains a comma. | **No action** — that row was dropped by DQ-01, and the CSV is properly quoted. Standing rule: never parse by splitting on commas. |

## F. Analytical limits — documented, not fixed

| ID | The problem | The fix we decided |
|---|---|---|
| **DQ-24** | 46 countries but 17 have a single respondent; India's treatment rate carries a ±25pp margin. | **Three measures together:** countries with n ≥ 20 charted individually with error bars; 5 **`region`** groups so nobody is dropped; US states at n ≥ 10. Stated rule: no geographic figure below n = 20. |
| **DQ-25** | The survey never asks "do you have a condition?" — `treatment` is only a stand-in. | **Terminology rule:** `treatment` = treatment-seeking, `has_condition` = self-reported condition. Never "prevalence of mental illness". The gap — **361 people with a condition who never sought help** — gets its own section. |
| **DQ-26** | `work_interfere` almost *is* the target: a model using it scores ~90% and learns nothing. | **Banned-feature rule** in code: `work_interfere`, `has_condition`, `interfere_score` excluded from the model. Run honest vs leaky and report the gap. Second model on the 986 who have a condition. |
| **DQ-27** | 79% male, 82% tech, 60% US, all volunteers. | **Limitations paragraph** with those figures, and a wording rule: "X% of respondents", never "X% of tech workers". **No weighting** — no population benchmark exists. |
| **DQ-28** | Only 6 respondents aged 60+. | **`age_group`** with an open-ended top band: 18–24 · 25–34 · 35–44 · 45+ (68). Every band clears the n ≥ 20 threshold. |

---

## The 13 derived columns

`has_condition` · `gender_clean` · `employment_type` · `age_group` · `region` · `size_rank` · `leave_score` · `interfere_score` · `knows_leave_policy` · `has_comment` · `survey_wave` · `uncertainty_score` · `support_score`

The last two are the dashboard's backbone: **`support_score`** (0–6) says what the employer provides, **`uncertainty_score`** (0–7) says whether the employee knows about it.

---

## Three findings the cleaning itself produced

1. **361 respondents (29%) have a mental health condition but have never sought treatment.**
2. **Treatment-seeking falls from 61.8% to 26.9%** as uncertainty about employer support rises — uncertainty behaves like a barrier.
3. **Women sought treatment at 68.8% against 45.5% of men**, and it isn't explained by who has a condition (85.4% vs 77.2%).

## Principles applied throughout

- Every blank was investigated for its **cause** before any fix — the cause decides the treatment.
- **Nothing was invented.** Every fill is a label for a meaning the blank already carried.
- Imputation was **tested, not assumed** (DQ-07), and rejected when it failed.
- Rows were dropped only where **multiple independent signals** showed a non-genuine response.
- Two denominators are stated on every chart: **1,247** overall, **1,088** for employer-support questions.
