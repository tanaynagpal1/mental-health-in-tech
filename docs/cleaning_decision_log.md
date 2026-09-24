# Data Cleaning Decision Log — Mental Health in Tech Survey

**Dataset:** `survey.csv` (OSMI Mental Health in Tech Survey 2014) — 1,259 rows × 27 columns
**Purpose:** One record per data issue. Each entry states what was found, the options considered, what we decided and why, and how many rows were affected. This log is the source for the "Data Preparation" section of the report and the video.

**Status key:** 🔲 Open · 💬 Under discussion · ✅ Decided · 🛠️ Implemented & verified

---

## Summary tracker

| ID | Category | Issue | Severity | Rows affected | Status |
|---|---|---|---|---|---|
| DQ-01 | Invalid values | Impossible ages | 🔴 High | 8 | ✅ Decided — drop 8 rows |
| DQ-02 | Invalid values | Gender is free text (44 values after drops) | 🔴 High | 1,247 (all) | ✅ Decided — `gender_clean`: Male / Female / Gender-diverse |
| DQ-03 | Invalid values | Leading/trailing whitespace | 🟠 Medium | 5 Gender, 18 comments | ✅ Decided — strip all text columns |
| DQ-04 | Invalid values | Inconsistent capitalisation | 🟠 Medium | Gender | ✅ Decided — lowercase before matching |
| DQ-05 | Missing values | `work_interfere` blank because of survey design | 🔴 High | 262 | ✅ Decided — label "No condition" + derive `has_condition` |
| DQ-06 | Missing values | `state` blank for non-US respondents | 🟢 Low | 513 | ✅ Decided — label + US-subset rule |
| DQ-07 | Missing values | `self_employed` blank in the first 18 rows | 🟢 Low | 18 | ✅ Decided — leave blank, exclude from that chart |
| DQ-08 | Missing values | `comments` 87% blank | 🟢 Low | 1,090 | ✅ Decided — leave blank + `has_comment` flag |
| DQ-09 | Missing values | Blanks stored as the text "NA" | 🟠 Medium | 1,892 cells | ✅ Decided — explicit `na_values` + lowercase names |
| DQ-10 | Contradictions | Non-US respondents with a US state | 🟢 Low | 3 | ✅ Decided — clear the state, keep the country |
| DQ-11 | Contradictions | US respondents with no state | 🟢 Low | 11 | ✅ Decided — label "Not specified" |
| DQ-12 | Contradictions | Treatment = Yes but `work_interfere` blank | 🟢 Low | 4 | ✅ Decided — no override |
| DQ-13 | Contradictions | Self-employed at a 100+ employee company | 🟠 Medium | 9 | ✅ Decided — keep as given |
| DQ-14 | Contradictions | Self-employed answering employer questions | 🟠 Medium | 141 | ✅ Decided — employer questions on employees only |
| DQ-15 | Contradictions | benefits = No but care_options = Yes | 🟢 Low | 141 | ✅ Decided — valid, no change |
| DQ-16 | Duplicates | Probable double submissions (identical except timestamp) | 🟠 Medium | 4 pairs → 4 rows dropped | ✅ Decided — keep first submission |
| DQ-17 | Duplicates | Same timestamp, different people | 🟢 Low | 13 | ✅ Decided — keep all, no action |
| DQ-18 | Structure/time | Mixed survey period (2014–2016) | 🟠 Medium | 76 | ✅ Decided — keep all + `survey_wave` flag |
| DQ-19 | Structure/time | Timestamp stored as text | 🟢 Low | 1,247 | ✅ Decided — parse with explicit format |
| DQ-20 | Structure/time | Ordered answers stored as plain text | 🟠 Medium | 3 columns | ✅ Decided — all three ordered + score columns |
| DQ-21 | Structure/time | "Don't know" / "Not sure" / "Maybe" are real answers | 🟠 Medium | 11 columns | ✅ Decided — keep + `uncertainty_score` |
| DQ-22 | Structure/time | Similar options worded differently across questions | 🟢 Low | — | ✅ Decided — keep wording, one code constant |
| DQ-23 | Structure/time | Country name with a comma ("Bahamas, The") | 🟢 Low | 0 (row removed) | ✅ Decided — no action |
| DQ-24 | Analytical limit | Most countries have very few responses | 🔴 High | 17 of 46 countries have 1 respondent | ✅ Decided — threshold + error bars + regions |
| DQ-25 | Analytical limit | No direct "have a condition?" question | 🔴 High | — | ✅ Decided — terminology rule |
| DQ-26 | Analytical limit | Leakage in modelling | 🔴 High | — | ✅ Decided — banned-feature rule |
| DQ-27 | Analytical limit | Skewed, self-selected sample | 🟠 Medium | — | ✅ Decided — limitations wording, no weighting |
| DQ-28 | Analytical limit | Few respondents aged 60+ | 🟢 Low | 6 | ✅ Decided — 4 age bands, 45+ open-ended |
| DQ-29 | Invalid rows | Test/junk submissions (all-"Yes" answers + junk fields) | 🟠 Medium | 2 | ✅ Decided — covered by DQ-01 |

**Row-count trail** (updated as fixes are implemented)

| Step | Rows | Change | Reason |
|---|---|---|---|
| Raw load | 1,259 | — | — |
| DQ-01: drop rows with Age outside 18–75 | 1,251 | −8 | 6 real people with invalid ages + 2 test/junk submissions |
| DQ-16: drop the later row of each duplicate pair | 1,247 | −4 | Accidental resubmissions (rows 821, 859, 1134, 1218) |

---

## Cleaning execution order (Phase 2 work queue)

The order matters: each step assumes the ones before it are done. Steps 1–3 are housekeeping that makes every later check reliable.

| Step | Issues | What we do | Status |
|---|---|---|---|
| 1 | DQ-09, DQ-23 | Load the file correctly: treat the text "NA" as missing, keep quoted commas intact | ✅ Decided |
| 2 | DQ-03, DQ-04 | Trim spaces and fix capitalisation in every text column | ✅ Decided |
| 3 | DQ-19 | Convert `Timestamp` to a real date | ✅ Decided |
| 4 | DQ-01, DQ-29 | Drop the 8 rows with an age outside 18–75 | ✅ Decided (drop) |
| 5 | DQ-16, DQ-17 | Decide on the 4 probable double submissions; keep the same-second pairs | ✅ Decided |
| 6 | DQ-02 | Standardise `Gender` into a small set of groups | ✅ Decided |
| 7 | DQ-10, DQ-11 | Fix country/state contradictions | ✅ Decided |
| 8 | DQ-24 | Create a grouped geography column so small countries can be analysed | ✅ Decided |
| 9 | DQ-05 | Decide what a blank `work_interfere` means | ✅ Decided |
| 10 | DQ-06, DQ-07, DQ-08 | Decide how to record the other blanks | ✅ All decided |
| 11 | DQ-13, DQ-14 | Decide how to treat self-employed respondents in the employer questions | ✅ Decided |
| 12 | DQ-12, DQ-15 | Decide on the remaining contradictions (keep, flag or fix) | ✅ Decided |
| 13 | DQ-20 | Give the three ordered columns a proper order | ✅ Decided |
| 14 | DQ-21, DQ-22 | Decide how "Don't know" / "Not sure" / "Maybe" are handled and labelled | ✅ Decided |
| 15 | DQ-18 | Decide whether to keep the 2015–16 responses | ✅ Decided |
| 16 | — | Build derived columns (13 columns — see the Derived columns section) | ✅ Decided |
| 17 | DQ-25, DQ-26 | Fix the target variable and the leakage rule for modelling | ✅ Decided |
| 18 | DQ-27, DQ-28 | Write the limitations section; no code changes | ✅ Decided |

**Documentation-only items** (nothing to clean, but they must appear in the report): DQ-24 partly, DQ-25, DQ-26, DQ-27, DQ-28.

---

## Detailed entries

### DQ-01 — Impossible ages
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Column:** `Age`
- **Evidence:** 8 values outside any plausible working age: -1726, -29, -1, 5, 8, 11, 329, 99999999999. The valid values run from 18 to 72 (median 31). Because of these outliers, the raw mean age comes out as ~79 million.
- **Investigation (7 checks):**
  1. *Row-by-row review.* The 8 rows fall into three groups:
     - **Likely test/junk submissions (2):** row 989 (Age 8, Gender "A little about you", Country Bahamas but state IL) and row 1127 (Age -1, Gender "p", comment "password: testered").
     - **Suspicious (1):** row 390 (Age 99999999999, Gender "All"). Its other answers vary normally.
     - **Plausible real people with a mistyped age (5):** row 143 (-29, probably a sign typo), 364 (329), 715 (-1726), 734 (5; left a long, detailed comment), 1090 (11).
  2. *All-"Yes" answering.* Rows 989 and 1127 answered "Yes" to all 17 Yes/No questions. They are the **only 2 respondents out of 1,259** who did this. The next highest is 13 of 17. They also answer "Yes" to pairs that contradict each other (e.g. "discussing would have negative consequences" and "willing to discuss with coworkers").
  3. *Missing values in these rows.* Nothing unusual: state 2 (both non-US), work_interfere 2, comments 5.
  4. *"Don't know" answers.* 0–4 per row, against an overall average of 3.8. No sign of careless answering.
  5. *Outlier-detection methods.* The IQR rule (fences 13.5–49.5) would also flag 32 valid respondents aged 50 and over. A z-score above 3 catches only 1 value, because the 99999999999 inflates the standard deviation and hides the other bad values (the *masking* effect). **A range rule based on what the question means is the right tool here.**
  6. *Effect on results.* Treatment rate is 50.6% with these rows and 50.5% without. The median age is 31 either way; the mean is 79 million with them and 32.1 without.
  7. *Is age related to treatment?* Yes: the treatment rate rises with age (18–24: 45%, 25–34: 49%, 35–44: 55%, 45+: 60%). Filling in a made-up age would therefore slightly distort a real pattern.
- **Options considered:**
  - A. Drop all 8 rows. Also loses 5–6 real people's answers.
  - B. Set Age to missing for all 8 and keep the rows. This keeps the 2 test rows in the attitude analysis.
  - C. **Mixed approach:** drop the clear junk rows and set Age to missing for the rest.
  - D. Reconstruct the intended age (-29 → 29). This is guessing; only one value can be reasoned about at all.
  - E. Fill with the median (31). This makes up data and slightly weakens the age–treatment pattern.
  - F. Cap extreme values. Doesn't fit here, because these are typos, not real extremes.
- **Recommended:** C. Drop rows 989 and 1127. Set Age to missing for the other 6. Treat row 390 as a judgement call. Use a valid range of 18–75 and add an `age_group` column.
- **Links:** Also resolves 3 junk answers under DQ-02 (gender) and 1 of the 4 rows in DQ-10. Raised a new issue, DQ-29.
- **Decision:** **Option A: drop all 8 rows** where Age is outside 18–75 (rows 143, 364, 390, 715, 734, 989, 1090, 1127).
- **Rationale:** If a respondent's age is invalid, we can't be confident their other answers are careful and reliable. Two of the rows are clearly test/junk submissions and a third is suspicious. Dropping all 8 is one simple, consistent rule that is easy to explain and reproduce. The cost is small: 0.6% of rows, and the headline results don't change (treatment rate 50.6% → 50.5%, median age 31 → 31). The trade-off we accepted: 6 plausibly real people are removed, including row 734's detailed comment. It could still be quoted in the report as an example of qualitative feedback.
- **Rows affected:** 8 (0.6%) → 1,251 rows remain
- **Side effects (verified on the data):**
  - Age range becomes 18–72, mean 32.08, median 31.
  - Countries drop from 48 to 46 (Zimbabwe and Bahamas each had only one respondent).
  - Gender goes from 49 raw values to 46 (38 after trimming spaces and lowercasing). This removes the junk answers "All", "A little about you" and "p", which feeds into DQ-02.
  - DQ-10 falls from 4 rows to 3 (Bahamas→IL removed).
  - Blank counts: state 513, self_employed 18, work_interfere 262, comments 1,090.
  - Treatment rate: 50.52%.
- **Verification check (Phase 4):** `assert df['Age'].between(18, 75).all()` and `assert len(df) == 1251`

### DQ-02 / DQ-03 / DQ-04 — Gender free text, whitespace and capitalisation
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Column:** `Gender` — a free-text box, not a set of options
- **Evidence:** **44 distinct values across 1,247 respondents** (after the DQ-01 and DQ-16 drops). Four kinds:
  1. *Same meaning, different spelling:* Male / male / M / m / Man / Cis Male / Male (CIS) / Cis Man / Maile / Make / Mal / Malr / Msle / Mail — and the female equivalents.
  2. *Whitespace and case:* trailing spaces make "Male " a separate value from "Male" (DQ-03); mixed capitalisation splits the same answer again (DQ-04).
  3. *Gender identities beyond male/female:* non-binary, Enby, Genderqueer, Agender, Androgyne, fluid, queer, queer/she/they, Neuter, Female (trans) ×2, Trans woman, Trans-female.
  4. *Hedged or throwaway answers (6):* "Male-ish", "Guy (-ish) ^_^", "ostensibly male, unsure what that really means", "something kinda male?", "male leaning androgynous", "Nah". These respondents answered the rest of the survey seriously — two left long, thoughtful comments.
- **Decision — a new column `gender_clean` with three values:**
  1. **Strip whitespace and lowercase before matching**, so "Male ", "Male" and "male" resolve to one value (DQ-03, DQ-04).
  2. **Male** — all spelling variants, typos and cis-prefixed forms, **plus the 6 hedged/throwaway answers** (rows 55, 93, 387, 626, 628, 1234), which lean male in wording.
  3. **Female** — all spelling variants, typos and cis-prefixed forms.
  4. **Gender-diverse** — all identities beyond male/female, **including the 4 trans respondents** who wrote "Female (trans)", "Trans woman" and "Trans-female".
  - The original `Gender` text is kept untouched in the dataset so any grouping can be audited or redone.
- **Terminology:** the third category is called **"Gender-diverse"** throughout the report, charts and app. Rejected: "Other" (defines people by what they are not), "Third gender" (a specific South Asian legal category, not what these answers say), "LGBTQ+" (mixes sexual orientation with gender identity and is not what the question asked).
- **Resulting counts:** Male **987** (79.1%) · Female **247** (19.8%) · Gender-diverse **13** (1.0%) = 1,247 ✅
- **Rates by group:** treatment — Male 45.5%, Female 68.8%, Gender-diverse 84.6%; has a condition — 77.2% / 85.4% / 100%; family history — 35.3% / 53.4% / 53.8%.
- **Rationale:** Spelling variants are data-entry noise and merging them is uncontroversial. The hedged answers all contain the word "male" and come from respondents who engaged seriously with the survey, so reading their intent keeps them in the analysis rather than discarding them. The 4 trans respondents are grouped as gender-diverse to keep the category coherent, and the decision is recorded here because it is a judgement call, not a fact from the data.
- **Small-sample rule (links to DQ-24):** the Gender-diverse group is 13 people. Report its existence and count; **do not quote percentages for it** — the 84.6% treatment rate rests on 11 individuals.
- **Verification check (Phase 4):** `assert df['gender_clean'].value_counts().to_dict() == {'Male': 987, 'Female': 247, 'Gender-diverse': 13}` and `assert df['Gender'].str.strip().eq(df['Gender']).all()`

### DQ-05 — `work_interfere` blank because of survey design
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Column:** `work_interfere` — "*If you have a mental health condition*, do you feel that it interferes with your work?"
- **Evidence:** 262 blanks after the DQ-01 row drop (21% of 1,251). The question only applies to people with a condition, so a blank is an answer ("does not apply to me"), not lost information.
- **Investigation (4 checks):**
  1. *Do the blanks really mean "no condition"?* Of the 262, **258 (98.5%) have never sought treatment**. Only 4 (1.5%) have — logged separately as DQ-12.
  2. *Family history.* 43 of 262 (16%), close to the "Never" group (18%) and far below the groups whose work is affected (54–55%).
  3. *Comments.* 20 of the 262 left a comment. Several describe mental health as something affecting colleagues or relatives; none describes a condition of their own.
  4. *Is "blank" the same as "Never"?* No. Treatment rate is 2% for blanks and 14% for "Never". "Never" means a condition that doesn't disturb work; blank means no condition. Merging them would dilute "Never" to about 7%, a figure describing nobody.
- **Options considered:**
  - 1. Leave blank — 262 people disappear from every chart of this column.
  - 2. **Add a new category** for the blanks.
  - 3. Merge into "Never" — rejected; the two groups differ (2% vs 14% treatment).
  - 4. Drop the 262 rows — rejected; destroys the comparison group and 21% of the data.
  - 5. Fill with the most common answer ("Sometimes") — rejected; invents a condition for 258 people.
  - 6. **Derive a new `has_condition` column** from the same rule.
- **Decision:** **Options 2 + 6.** Fill the blanks with the category **"No condition"**, and derive a new column **`has_condition`** (blank → No, any answer → Yes).
- **Rationale:** The blank already carries a meaning, so labelling it states what is there rather than inventing anything, and all 1,251 respondents stay visible in every chart. The derived column turns that meaning into a clean Yes/No variable and supplies the "do you have a condition?" question the survey never asked directly (DQ-25).
- **Resulting counts:**
  - `work_interfere` (after the DQ-16 de-dup, on 1,247 rows): Sometimes 464 · **No condition 261** · Never 212 · Rarely 171 · Often 139 = 1,247 ✅
  - `has_condition`: Yes 986 (79%) · No 261 (21%)
- **What this unlocks:** 628 of the 989 people with a condition have sought treatment; **361 (29% of all respondents) have a condition but have never sought treatment**. Comparing those 361 with the 628 is a core analysis for the report.
- **Caution (links to DQ-26):** `has_condition` is derived from `work_interfere`, so the two hold the same information. Use one or the other in a model, never both.
- **Verification check (Phase 4):** `assert df['work_interfere'].isna().sum() == 0` and `assert (df['has_condition'] == 'No').sum() == 261`

### DQ-06 — `state` blank for non-US respondents
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Column:** `state` — "*If you live in the United States*, which state or territory do you live in?"
- **Evidence:** 509 blanks after the DQ-01 and DQ-16 drops, made up of two different groups: **498 non-US respondents** (the question did not apply) and **11 US respondents who skipped it** (genuinely missing — DQ-11). Of 746 US respondents, 735 gave a state (98.5% coverage) across 45 valid state codes; all codes are valid, so there is nothing to correct.
- **Options considered:** 1. Leave blank · 2. Label the two groups separately · 3. One "Unknown" label for all 513 · 4. Drop the column · 5. Drop non-US rows
- **Decision:** **Option 2, plus the US-subset rule.**
  - `state` is left untouched for the 735 respondents who answered.
  - Non-US blanks → **"Not applicable"** (498 blanks + 3 cleared under DQ-10 = 501 rows); US blanks → **"Not specified"** (11 rows).
  - Every state-level chart is built on the **US subset (746 respondents)** and captioned "US respondents only (n = 746)".
- **Rationale:** The two kinds of blank mean different things and a single label would hide that. Nothing is invented and no rows are lost. Stating the denominator stops state percentages being read against the full 1,251 and keeps mystery blanks out of the Streamlit filters.
- **Rows affected:** 509 relabelled (on 1,247 rows); 0 rows dropped
- **Verification check (Phase 4):** `assert df['state'].isna().sum() == 0`, `assert (df.state == 'Not applicable').sum() == 501`, `assert (df.state == 'Not specified').sum() == 11`

### DQ-07 — `self_employed` blank in the first 18 rows
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Column:** `self_employed` — "Are you self-employed?"
- **Evidence (cause):** All 18 blanks were submitted between **11:29:31 and 11:34:37**; the first answered response arrives at **11:34:53** and no response after that time is ever blank. The question was added to the form about five minutes after launch, so these 18 people were never shown it. Unlike DQ-05, this blank is genuinely unknown, not an implied answer.
- **Investigation (3 checks):**
  1. *Company size clue.* Self-employment runs at 59.5% among 1-5 employee companies but 0–11% in larger bands. The 18 blanks report 6-25 (6), 26-100 (5), 100-500 (3), 1-5 (2), 1000+ (1), 500-1000 (1), so most are probably "No".
  2. *Can the answer be predicted from response patterns?* A Naive Bayes classifier was trained on the 14 employer-support and attitude questions using the 1,233 known rows (pre-de-dup), validated with 5-fold cross-validation. Self-employed respondents do answer differently (benefits = No: 66% vs 25%; leave = Don't know: 19% vs 48%; mental_vs_physical = Yes: 46% vs 25%), but the attitude questions barely differ (2–6pp).
     - **Model accuracy 86.1%, below the majority-class baseline of 88.5%.** Recall on self-employed 28%, precision 37%.
     - It ranks usefully (top quintile 30% self-employed vs bottom quintile 2.8%) but cannot label individuals.
     - On the 18 blanks it predicts 2 as self-employed (expected count ≈ 3), but **those 2 report companies of 26-100 and 6-25**, while the two 1-5 company respondents get 34% and 11%. The two methods disagree on *which* people, so neither is reliable.
  3. *Are the 18 unusual?* No. Treatment rate 50.0% vs 50.5% overall, median age 32 vs 31, ordinary country and gender mix. Excluding them costs precision, not accuracy.
- **Options considered:** 1. Leave blank · 2. Fill all with "No" (majority) · 3. Fill by company size · 4. Drop the 18 rows · 5. Fill with "Unknown"
- **Decision:** **Option 1 — leave the 18 values blank**, and exclude them from charts and analyses that split by `self_employed` (those run on 1,229 rows), stating the n on the chart.
- **Rationale:** Imputation was tested, not assumed: the classifier scored below the majority-class baseline and contradicted the company-size clue on which individuals to flag, so there is no reliable basis for filling the field. The 18 rows are otherwise complete and stay in every other analysis. The cause is a form change, not respondent behaviour, so excluding them introduces no bias.
- **Rows affected:** 18 (1.4%) — excluded only from `self_employed` breakdowns
- **Reporting note:** Charts split by self-employment carry the caption "18 responses predate this question and are excluded". Modelling must handle the blanks explicitly if this column is used as a feature.
- **Verification check (Phase 4):** `assert df['self_employed'].isna().sum() == 18` and `assert df[df.self_employed.notna()].shape[0] == 1229`

### DQ-08 — `comments` mostly blank
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Column:** `comments` — "Any additional notes or comments" (optional free text)
- **Evidence:** After the DQ-01 drop, 161 comments and 1,090 blanks. A blank means the person had nothing to add — neither an implied answer (DQ-05) nor a lost one (DQ-07), so there is nothing to repair. 137 of the 161 are substantial (50+ characters); median length 167 characters, longest 3,548. **One comment is just "-"** (a typed "nothing"), so the honest count is 160.
- **Investigation (3 checks):**
  1. *Are commenters representative?* **No.** Treatment 64.6% vs 48.4%; has a condition 87.6% vs 77.8%; has seen consequences at work 19.9% vs 13.7%. People with personal experience were far more motivated to write.
  2. *Geographic skew.* 102 of 161 comments come from the US, so the qualitative material is even more US-weighted than the survey itself.
  3. *Text integrity.* The comments contain **no commas at all** though 146 contain full stops — the publisher stripped commas from the free text. Quotes are readable but not verbatim, which needs a footnote if any are quoted.
- **Options considered:** 1. Leave blank · 2. Fill with "No comment" · 3. Drop the column · 4. Add a `has_comment` flag · 5. Clean/tokenise for word clouds or topic analysis
- **Decision:** **Options 1 + 4.** Leave the blanks as missing, keep the text untouched, and derive a **`has_comment`** flag (Yes 160 / No 1,091 after the "-" is treated as blank, per DQ-09).
- **Rationale:** A blank is a true "nothing to add", so filling it would add 1,090 meaningless strings. The flag converts the commenter bias from a caveat into a measurable variable — commenting is itself a sign of engagement with the topic. Comments are used **illustratively only**: quoted individually, never counted ("many respondents said…" would be invalid given the 64.6% vs 48.4% skew).
- **Rejected:** option 5 — with 160 comments a word cloud is decorative rather than evidence; 3–4 well-chosen quotes carry more weight in the report and video.
- **Reporting note:** state the commenter bias once in the report, and footnote that commas were stripped from the source text.
- **Verification check (Phase 4):** `assert df['has_comment'].sum() == 160` and `assert df['comments'].notna().sum() == 160`

### DQ-09 — Blanks stored as the text "NA"
- **Status:** ✅ Decided
- **Evidence:** 1,892 cells across `state`, `self_employed`, `work_interfere` and `comments` hold the literal text `NA`. pandas converts them silently; SQL, Excel and Power BI may not. One `comments` value is "-", a typed "nothing". No question offers "NA" as a valid answer, and no other null-like token ("N/A", "NULL", "None", "?") appears anywhere.
- **Decision:** Load explicitly — `pd.read_csv(path, na_values=["NA", "-", ""], keep_default_na=True)` — and **lowercase all 27 column names** at load (`Age`→`age`, `Gender`→`gender`, `Timestamp`→`timestamp`, `Country`→`country`).
- **Rationale:** Nothing about the load is left to library defaults, so the same result is reproducible in any tool; the explicit list also catches the "-" comment (DQ-08). One naming convention avoids constant capitalisation errors and matches PostgreSQL's unquoted lowercase.
- **Verification check (Phase 4):** `assert df.columns.equals(df.columns.str.lower())` and `assert df['comments'].notna().sum() == 160`

### DQ-10 — Non-US respondents with a US state
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Evidence:** 3 rows remain after the DQ-01 drop removed the Bahamas→IL row: **Latvia→NY (row 319), Israel→MD (row 488), Bulgaria→UT (row 1179)**. The question is conditional on living in the US, so these rows should have no state. Row 488 left a comment explaining their answers in terms of **Israel's** public health insurance, which confirms the country is correct and the state is the stray value (most likely a remembered or pre-selected form value).
- **Options considered:** 1. Clear the state, keep the country · 2. Change the country to United States · 3. Drop the 3 rows · 4. Leave the contradiction
- **Decision:** **Option 1 — clear the state, keep the country.** The 3 values become "Not applicable" along with the other non-US rows.
- **Rationale:** The country is supported by evidence (row 488's comment) while the state contradicts the question's own condition. Option 2 would invent three Americans; option 4 would silently place Latvia and Bulgaria on a US state map.
- **Rows affected:** 3 values cleared; 0 rows dropped

### DQ-11 — US respondents with no state
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Evidence:** 11 US respondents left the state blank (rows 52, 294, 367, 525, 574, 596, 638, 817, 854, 926, 1019). They are spread through the survey rather than clustered in time, so this is not a form fault — they skipped an optional question. Minor pattern: 55% work remotely against 31% of other US respondents, which is suggestive but far too small to report.
- **Options considered:** 1. Label "Not specified" · 2. Guess the state · 3. Drop the 11 rows · 4. Treat them as non-US
- **Decision:** **Option 1 — label "Not specified"** (consistent with DQ-06). They remain in all US-level analysis; state-level charts either show them as a labelled group or exclude them with the n stated.
- **Rationale:** Nothing in the data supports guessing a state, and dropping complete responses over one optional field is wasteful.
- **Resulting rule (enforced in code):** after cleaning, `state` holds a real value **only** where `Country == "United States"` — `assert df.loc[df.Country != 'United States', 'state'].eq('Not applicable').all()` and `assert (df.state == 'Not specified').sum() == 11`

### DQ-12 — Treatment = Yes but `work_interfere` blank
- **Status:** ✅ Decided — no override
- **Evidence:** 4 rows (500 US, 937 Netherlands, 1202 Brazil, 1254 UK) sought treatment yet skipped the condition-conditional question. All four answer the rest of the survey normally. The likeliest reading is a past condition that has resolved: you sought treatment once, but today you would not say you *have* a condition.
- **Options considered:** 1. Leave them under the DQ-05 rule · 2. Override `has_condition` to Yes · 3. Set to missing · 4. Drop the 4 rows
- **Decision:** **Option 1 — leave them under the general rule**, so `work_interfere` = "No condition" and `has_condition` = No for these 4.
- **Rationale:** One rule applied consistently beats a special case for 0.3% of rows. Option 2 would treat "has sought treatment" as proof of a *current* condition, which the survey never claims; option 3 would put a third value into an otherwise clean Yes/No column for 4 people.
- **Rows affected:** 4 (0.3%) — documented, not overridden

### DQ-15 — benefits = No but care_options = Yes
- **Status:** ✅ Decided — valid answers, no change
- **Evidence:** 141 rows. The two questions ask different things: `benefits` = does your employer *provide* mental health benefits; `care_options` = do you *know* what options your employer provides. "I know exactly what my employer offers: nothing" is coherent and well-informed.
- **Investigation (3 checks):**
  1. *Who is in this group?* **Self-employed respondents are 31% of it against 11% overall** — people who work for themselves know their situation precisely, and it includes no benefits.
  2. *Does the mirror case exist?* Yes — **91 respondents say benefits = Yes but care_options = No**: the employer provides something and the employee doesn't know what. That is the familiar "benefits exist but nobody knows about them" problem, the same phenomenon in reverse, and nobody would call it a data error.
  3. *Do the genuinely uninformed answer consistently?* Yes — of 407 who don't know whether benefits exist, only 6 claim to know the care options.
- **Options considered:** 1. Treat as valid · 2. Force care_options to "No" where benefits = No · 3. Flag the rows · 4. Drop them
- **Decision:** **Option 1 — treat as valid answers and change nothing.**
- **Rationale:** The pattern is explained by the wording of the two questions and confirmed by the self-employment skew and the mirror case. Option 2 would overwrite 141 honest answers with an assumption.
- **Finding worth reporting:** this group's treatment rate is **58.9% against 50.5% overall** — respondents who clearly understand their (absent) benefits seek treatment more than average, suggesting awareness matters even where the benefit does not exist.
- **Rows affected:** 0

### DQ-13 — Self-employed at a large company
- **Status:** ✅ Decided — keep as given
- **Evidence:** 141 self-employed respondents after the DQ-01/DQ-16 drops: 1-5 (93), 6-25 (31), 26-100 (8), 100-500 (5), More than 1000 (4). So **9 report a company of 100+ employees**.
- **Options considered:** 1. Keep both answers · 2. Clear `no_employees` · 3. Clear `self_employed` · 4. Drop the 9 rows
- **Decision:** **Option 1 — keep both answers exactly as given.**
- **Rationale:** This is ambiguous rather than wrong. A contractor may be describing the size of the client organisation they work at, and a business owner may be counting their own staff. Clearing either field would assume which answer is mistaken with no evidence either way. With 9 rows (0.7%) no figure is affected.
- **Rows affected:** 0 — documented, not changed

### DQ-14 — Self-employed answering employer questions
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Evidence:** 141 self-employed respondents answered the six employer-support questions (benefits, care_options, wellness_program, seek_help, anonymity, leave) plus the employer-facing attitude questions, although for them "your employer" means themselves. Their answers differ systematically — 66% say "no benefits" against 25% of employees.
- **Distortion measured (all rows vs employees only, 1,088):** "No benefits" 29.4% → **24.9%** (4.5pp); "Leave: don't know" 44.9% → 48.2%; "Employer takes mental health seriously: Yes" 27.1% → 24.9%; "Anonymity: don't know" 65.2% → 67.0%.
- **Options considered:** 1. Employer questions on employees only · 2. Leave as is · 3. Blank the answers for self-employed · 4. Drop the 141 rows · 5. Report both groups side by side · 6. Add an `employment_type` column
- **Decision:** **Option 1 — the six employer-support questions are analysed on employees only (n = 1,088), captioned "employees only".** All other analysis continues to use all 1,247 respondents.
  - *Implementation:* a derived column **`employment_type`** — Employee 1,088 · Self-employed 141 · Unknown 18 — provides the filter and doubles as the Streamlit control. No source values are changed, so the self-employed answers remain available.
- **Rationale:** Including respondents who have no employer inflates figures such as "no mental health benefits" by about 4.5 points in a way a reader cannot detect. Filtering at analysis time fixes the denominator without destroying data (option 3) or discarding 11% of the sample (option 4).
- **Rows affected:** 0 changed; 141 excluded from six charts
- **Reporting note:** the report states the two denominators explicitly — 1,247 overall, 1,088 for employer-support questions.
- **Verification check (Phase 4):** `assert df['employment_type'].value_counts().to_dict() == {'Employee': 1088, 'Self-employed': 141, 'Unknown': 18}`

### DQ-16 — Probable double submissions
- **Status:** ✅ Decided (to be implemented in Phase 4)
- **Evidence:** 4 pairs identical in **all 26 non-timestamp columns**, including free-typed age and the exact spelling of gender (each pair uses the same spelling), submitted minutes apart:
  | Pair | Rows | Profile | Gap |
  |---|---|---|---|
  | 1 | 819 / 821 | 35 · Male · Denmark · self-employed 1-5 | 1 min 16 s |
  | 2 | 860 / 859 | 32 · male · UK · 6-25 · non-tech | **12 s** |
  | 3 | 1133 / 1134 | 27 · M · New Zealand · 26-100 | 4 min 52 s |
  | 4 | 1215 / 1218 | 28 · male · Netherlands · 6-25 | 4 min 9 s |
  Across 1,251 rows there are **1,247 unique answer combinations** — only these 4 repeat. Relaxing the test to 8 key fields matches 60 rows, so partial coincidences are common while a full 26-column match is not. Pair 2's 12-second gap rules out a second person filling in a 26-question form.
- **Options considered:** A. Keep both · B. Keep the first submission · C. Keep the last · D. Only remove gaps under 2 minutes (arbitrary cut-off) · E. Drop both rows of each pair · F. Keep and flag, run results both ways
- **Decision:** **Option B, with F as a footnote.** Drop the later submission of each pair — **rows 821, 859, 1134, 1218** (note: in pair 2 the earlier timestamp is row 860, so "first" means by timestamp, not row order). Report that results were checked both ways.
- **Rationale:** The evidence points to accidental resubmission rather than two identical respondents, so the dataset should claim 1,247 distinct people, not 1,251. Keeping one row of each pair preserves a genuine response; dropping both would discard it.
- **Rows affected:** 4 dropped → **1,247 rows**. Treatment rate 50.52% either way, so no result depends on this choice.
- **Report sentence:** "Four pairs of records were identical across all 26 answer fields with submission gaps of 12 seconds to 5 minutes. These were treated as accidental resubmissions; the first submission of each pair was retained. Results were unchanged either way."
- **Verification check (Phase 4):** `assert len(df) == 1247` and `assert df.drop(columns='Timestamp').duplicated().sum() == 0`

### DQ-17 — Same timestamp, different people
- **Status:** ✅ Decided — no action
- **Evidence:** 13 rows share a timestamp with another row but differ in their answers (different countries, ages, employers). Two people submitting in the same second is normal for a widely shared survey.
- **Decision:** **Keep all 13 rows.** A shared timestamp alone is not evidence of duplication; only the full 26-column match in DQ-16 is.
- **Rationale:** Recorded so a reviewer can see the case was checked and dismissed on evidence rather than missed.

### DQ-18 — Mixed survey period
- **Status:** ✅ Decided
- **Evidence:** On 1,247 rows: **1,171 responses in Aug–Sep 2014, 76 from Oct 2014 to Feb 2016**, including a burst from Ireland (14) and the UK (13) in Feb 2015.
- **Investigation:** The late group differs — treatment **63.2% vs 49.7%**, and only **38% US-based against 61%** in the main wave. Employer-support answers (`benefits`, `anonymity`) are nearly identical between the waves, so the difference is **composition, not time**: the survey was re-shared to a more European, more engaged audience. Six months is also too short for workplace attitudes to move.
- **Decision:** **Keep all 76 rows.** Add a **`survey_wave`** flag (Main 1,171 / Late 76), state the composition difference once in the limitations, and re-run the two headline figures excluding the late rows as a sensitivity check.
- **Rationale:** Dropping 6% of the data to tidy a date range costs more than it buys, and the difference is explained by who answered rather than when.

### DQ-19 — Timestamp stored as text
- **Status:** ✅ Decided
- **Evidence:** `Timestamp` loads as a string, so it sorts as text and no time analysis is possible.
- **Decision:** `pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")` — an **explicit format**, so a malformed value raises instead of being silently guessed. Derive only `survey_wave` (DQ-18) from it.
- **Rationale:** A one-month survey has no seasonality or day-of-week effect worth extracting; further time features would be noise.

### DQ-20 — Ordered answers stored as plain text
- **Status:** ✅ Decided — all three columns (to be implemented in Phase 4)
- **Columns:** `no_employees`, `leave`, `work_interfere`. Sorted alphabetically (the default), `no_employees` comes out as 1-5, 100-500, 26-100, 500-1000, 6-25, More than 1000 — a meaningless sequence that hides any trend.

**`no_employees` — ✅ Decided**
- **Why order matters:** benefits provision by company size (employees only) climbs almost linearly — 1-5: 9.7% · 6-25: 20.4% · 26-100: 35.4% · 100-500: 46.1% · 500-1000: 59.3% · 1000+: 65.6%. In alphabetical order the same figures read 9.7, 46.1, 35.4, 59.3, 20.4, 65.6 and the pattern disappears.
- **Options considered:** 1. Ordered categorical · 2. Sort manually per chart · 3. Numeric rank column · 4. Replace with midpoint numbers · 5. Merge into 3 bands
- **Decision:** **Options 1 + 3.** Define `no_employees` as an **ordered categorical** with the sequence 1-5 < 6-25 < 26-100 < 100-500 < 500-1000 < More than 1000, and add a numeric **`size_rank`** (1–6) for correlation tests.
- **Rationale:** The ordered categorical makes every chart, table and groupby sort correctly by default instead of relying on remembering an order list in ~15 places (option 2). `size_rank` supplies the numeric form needed for the "strongest predictors" analysis. Rejected: option 4 (midpoints are invented, and "More than 1000" has no ceiling) and option 5 as a data change (six bands are kept; grouping to three is a chart-time choice if needed).
- **Counts (1,247 rows):** 6-25: 287 · 26-100: 287 · More than 1000: 281 · 100-500: 175 · 1-5: 157 · 500-1000: 60
- **Verification check (Phase 4):** `assert list(df['no_employees'].cat.categories) == ['1-5','6-25','26-100','100-500','500-1000','More than 1000']` and `assert df['no_employees'].cat.ordered`

**`leave` — ✅ Decided**
- **Why order matters:** fear of negative consequences falls almost eight-fold across the scale — Very difficult 61.9% · Somewhat difficult 41.9% · Somewhat easy 12.9% · Very easy 7.9%. Alphabetical sorting puts "Very difficult" next to "Very easy" and destroys this.
- **Counts (1,247 rows):** Don't know 560 (45%) · Somewhat easy 263 · Very easy 203 · Somewhat difficult 124 · Very difficult 97. Treatment rate by level: 68.0 / 65.3 / 49.4 / 49.8 / 45.0%.
- **Options considered:** 1. Ordered scale with "Don't know" outside it · 2. Treat "Don't know" as missing · 3. Place "Don't know" in the middle · 4. Collapse to Difficult/Easy/Don't know · 5. Numeric `leave_score` · 6. `knows_leave_policy` flag
- **Decision:** **Options 1 + 5 + 6.**
  - Ordered categorical: Very difficult < Somewhat difficult < Somewhat easy < Very easy, with **"Don't know" placed last, outside the order**.
  - **`leave_score`** 1–4 (Very difficult = 1 … Very easy = 4), blank for "Don't know".
  - **`knows_leave_policy`** — Yes 687 / No 560.
- **Rationale:** "Don't know" is not a point on a difficulty scale (option 3 would claim it means "neutral"), but it is 45% of respondents and cannot be discarded (option 2). Parking it outside the order keeps charts correct while leaving the group visible, and the flag converts it into a variable that can be analysed in its own right. Option 4 was rejected as a data change because it loses the intensity difference; collapsing remains available at chart time.
- **Finding it unlocks:** respondents who don't know their leave policy have the **lowest treatment rate of any group (45.0%)** — uncertainty behaves like a barrier, not like neutrality.
- **Verification check (Phase 4):** `assert list(df['leave'].cat.categories)[:4] == ['Very difficult','Somewhat difficult','Somewhat easy','Very easy']` and `assert df['knows_leave_policy'].eq('No').sum() == 560`

**`work_interfere` — ✅ Decided**
- **Why order matters:** every measure climbs cleanly across the scale — treatment 14.2 → 70.8 → 76.9 → 84.9%; family history 17.9 → 46.8 → 53.9 → 54.7%; seen consequences 8.0 → 14.0 → 18.8 → 25.2%. Alphabetical sorting places "Often" between "No condition" and "Rarely".
- **Counts (1,247 rows):** Sometimes 464 · No condition 261 · Never 212 · Rarely 171 · Often 139.
- **Options considered:** 1. Ordered scale with "No condition" last · 2. "No condition" first, as position zero · 3. Drop "No condition" (rejected in DQ-05) · 4. Numeric `interfere_score` · 5. Collapse to Any/No interference/No condition
- **Decision:** **Options 1 + 4.** Ordered categorical Never < Rarely < Sometimes < Often with **"No condition" last, outside the order**, plus **`interfere_score`** 1–4 (Never = 1 … Often = 4), blank for "No condition".
- **Rationale:** Option 2 would imply a single continuum from "no condition" to "often", but having a condition and how much it interferes are two different questions — and `has_condition` (DQ-05) already carries the first, so no extra flag is needed here. Option 5 stays available as a chart-time simplification (Any interference 774 · Never 212 · No condition 261).
- **Note for the report:** the jump from Never (14.2%) to Rarely (70.8%) is the largest single step in the dataset — any interference at all, however rare, is associated with roughly five times the treatment rate.
- **Verification check (Phase 4):** `assert list(df['work_interfere'].cat.categories)[:4] == ['Never','Rarely','Sometimes','Often']` and `assert df['interfere_score'].notna().sum() == 986`

### DQ-21 — "Don't know" / "Not sure" / "Maybe" are real answers
- **Status:** ✅ Decided — and the source of a headline finding
- **Evidence (1,247 rows):** `anonymity` 813 (65%) · `mental_vs_physical` 573 (46%) · `leave` 560 (45%) · `phys_health_interview` 554 (44%) · `mental_health_consequence` 475 (38%) · `benefits` 407 (33%) · `seek_help` 363 (29%) · `care_options` 312 (25%) · `phys_health_consequence` 271 (22%) · `mental_health_interview` 206 (17%) · `wellness_program` 187 (15%). Treating these as missing would gut the dataset.
- **Investigation — are they meaningful?** Counting uncertain answers per respondent across the 7 employer-support questions produces a monotonic gradient in treatment-seeking:
  | Uncertain answers | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
  |---|---|---|---|---|---|---|---|---|
  | People | 186 | 214 | 253 | 218 | 157 | 127 | 66 | 26 |
  | Sought treatment | 61.8% | 61.7% | 54.2% | 45.9% | 45.2% | 37.0% | 31.8% | 26.9% |
- **Decision:**
  1. Every uncertain answer stays a **real category** — never imputed, never dropped.
  2. In ordered columns it sits **outside the order** (already applied to `leave` and `work_interfere` in DQ-20).
  3. Derive **`uncertainty_score`** (0–7): the count of "Don't know"/"Not sure" across `benefits`, `care_options`, `wellness_program`, `seek_help`, `anonymity`, `leave`, `mental_vs_physical`.
  4. Report the gradient as a finding, not a caveat.
- **Rationale:** Not knowing what your employer offers is itself a barrier — the data shows treatment-seeking falling from 62% to 27% as uncertainty rises.

### DQ-22 — Similar options worded differently
- **Status:** ✅ Decided
- **Evidence:** "Don't know" in 6 columns, "Not sure" in `care_options`, "Maybe" in the 4 consequence/interview columns. Code filtering on one spelling silently misses the others.
- **Decision:** Leave the **source values untouched** — they are the survey's own wording — and handle it in code with one shared constant, `UNCERTAIN = ["Don't know", "Not sure"]`, used by `uncertainty_score` and every filter. **"Maybe" is deliberately excluded** from that list.
- **Rationale:** "Maybe I would face negative consequences" is a judgement about risk, not a gap in knowledge. Merging it with "I don't know what my employer provides" would blend two different concepts into one meaningless measure. Chart labels may be harmonised for presentation, but the data keeps the original wording.

### DQ-23 — Country name with a comma
- **Status:** ✅ Decided — no action needed
- **Evidence:** "Bahamas, The" was the only country containing a comma, and that row was removed by DQ-01. One `Gender` value ("ostensibly male, unsure what that really means") still contains a comma. Both are correctly quoted in the source file, so `pd.read_csv` handles them; only manual comma-splitting would break.
- **Decision:** No data change. Recorded as a checked-and-cleared case, with the standing rule that the CSV is never parsed by splitting on commas.

### DQ-24 — Most countries have very few responses
- **Status:** ✅ Decided (applies at analysis/chart time, Phase 5+)
- **Evidence:** After the DQ-01 drop: **46 countries, 1,247 respondents**. 17 countries have a single respondent. Coverage by threshold — n ≥ 5: 18 countries (96% of people); n ≥ 10: 9 (92%); **n ≥ 20: 7 (90%)**; n ≥ 30: 4 (84%). US states: 45 states, 735 respondents, 6 with a single respondent; n ≥ 10: 20 states (88% of US respondents).
- **Why it matters (95% confidence intervals on the treatment rate):** US 54.7% ±3.5pp · UK 50.0% ±7pp · Canada 51.4% ±11pp · Germany 46.7% ±14pp · Netherlands 33.3% ±17pp · **India 30.0% ±25pp** · **New Zealand 62.5% ±28pp**. Below about n = 20 the interval is wider than any difference worth reporting. At n < 5 the only rates arithmetically possible are 0 / 25 / 33 / 50 / 100%.
- **Shrinkage illustration (why raw small-sample rates mislead):** Louisiana, 1 respondent who sought treatment, raw rate 100% → shrunk to 56.8% (the US average). California, 138 respondents, 62.3% → 61.4%, barely moved.
- **Options considered:** 1. Minimum-n threshold · 2. Show uncertainty (error bars, size by n) · 3. Group into regions · 4. Empirical-Bayes shrinkage
- **Decision:** **Options 1 + 2 + 3 together, each in its place.**
  - **Headline country chart:** only countries with **n ≥ 20** shown individually — United States 746, United Kingdom 183, Canada 72, Germany 45, Ireland 27, Netherlands 26, Australia 21 (90% of respondents) — with **error bars**; the remaining 39 countries (127 people) grouped as "Other".
  - **Map / regional comparison:** 5 region groups so all 1,247 respondents are represented — United States 746 (54.7%) · UK & Ireland 210 (49.5%) · Europe (other) 153 (33.3%) · Canada, Australia & NZ 100 (55.0%) · Rest of world 38 (31.6%).
  - **US state map:** states with **n ≥ 10** shown individually (20 states, 644 respondents = 88% of US); smaller states greyed out with a "too few responses" legend.
  - **Everywhere:** print the n on the chart. Stated rule for the report: *"No geographic figure is reported below n = 20; sub-threshold units are grouped."*
  - Option 4 (shrinkage) is mentioned once in the limitations section as a considered alternative, not implemented.
- **Rationale:** Thresholds keep every reported figure defensible, error bars make the remaining uncertainty visible instead of hidden, and the region grouping means no respondent is discarded. Together they answer the brief's geography question without ever publishing a percentage built on a handful of people.
- **Rows affected:** none — this is a reporting rule, not a data change. A derived `region` column is created at step 16.
- **Verification check (Phase 4/5):** `assert df.groupby('region').size().sum() == len(df)` and every geographic chart function refuses to plot a unit below its threshold.

### DQ-25 — No direct "have a condition?" question
- **Status:** ✅ Decided — terminology rule for the whole project
- **Evidence:** The survey never asks whether the respondent has a mental health condition. `treatment` ("have you sought treatment?") is the closest measure and is balanced (630 Yes / 617 No on 1,247 rows). `has_condition`, derived in DQ-05, is the second-best measure.
- **Decision:** Fixed wording everywhere — `treatment` = **treatment-seeking**; `has_condition` = **self-reported condition, inferred from the work-interference question**. Every headline figure names which measure it uses, and no figure is ever described as "prevalence of mental illness". The gap between the two — **361 respondents (29%) with a condition who never sought treatment** — gets its own section in the report.
- **Rationale:** Stating the limitation openly and then mining the gap between the two measures turns a weakness of the survey into one of the project's most useful analyses.

### DQ-26 — Leakage: `work_interfere` gives the answer away
- **Status:** ✅ Decided — modelling rule
- **Evidence:** Treatment rate by `work_interfere`: Often 84.9% · Sometimes 76.9% · Rarely 70.8% · Never 14.2% · No condition 1.5%. `work_interfere`, `has_condition` and `interfere_score` all encode "this person has a condition", so a model predicting `treatment` from them scores around 90% and teaches nothing.
- **Decision — an explicit feature rule in the code, not a comment:**
  - **Target:** `treatment`.
  - **Banned features:** `work_interfere`, `has_condition`, `interfere_score`.
  - **Allowed:** demographics (`age`, `age_group`, `gender_clean`, `country`, `region`), workplace (`no_employees`/`size_rank`, `remote_work`, `tech_company`, `employment_type`), the 6 employer-support questions, the 8 attitude questions, `uncertainty_score`, `support_score`.
  - Run the model **twice** — honest and leaky — and report the accuracy gap as a demonstration of leakage.
  - Build a **second model on the 986 respondents who have a condition**: among people who all have one, what predicts seeking help? That is the actionable question for an employer.
- **Rationale:** Makes the trap explicit and reusable, and converts it into a teaching point for the video rather than a hidden flaw.

### DQ-27 — Skewed, self-selected sample
- **Status:** ✅ Decided — limitations wording
- **Evidence:** 79.1% male, 82% at tech companies, 60% US-based, all volunteers recruited through mental-health advocacy channels (Open Sourcing Mental Illness).
- **Decision:** One short limitations paragraph carrying those four numbers, plus a standing wording rule: **no sentence begins "X% of tech workers…" — it reads "X% of respondents…"**. **No weighting is applied**, because there is no population benchmark for the tech workforce and weights would invent precision the data cannot support.
- **Rationale:** The honest framing costs nothing analytically and protects every finding from being overstated.

### DQ-28 — Few respondents aged 60+
- **Status:** ✅ Decided
- **Evidence:** Ages run 18–72 (median 31). Only 6 respondents are 60+, and 68 are 45+. Fine-grained bands would produce unstable rates at the top end.
- **Decision:** Four bands with an open-ended top: **`age_group` = 18–24 (156) · 25–34 (707) · 35–44 (320) · 45+ (68)**. Raw `age` is kept for distributions and correlations.
- **Rationale:** Every band clears the n ≥ 20 reporting threshold set in DQ-24, so no age figure rests on a handful of people.

### DQ-29 — Test/junk submissions
- **Status:** ✅ Decided — both rows are removed by the DQ-01 rule (found while investigating DQ-01)
- **Evidence:** Rows 989 and 1127 are the only respondents who answered "Yes" to all 17 Yes/No questions. Both also have an invalid age and a junk gender. Row 989's country (Bahamas) contradicts its state (IL). Row 1127's comment is "password: testered".
- **Decision:** No separate action needed; the DQ-01 age rule removes rows 989 and 1127. For the report: straight-lining (identical answers to every question) is a known sign of low-quality survey responses.

---

## Derived columns (step 16)

Thirteen new columns built from the cleaning decisions. No source column is overwritten.

| Column | Built from | Values | Source decision |
|---|---|---|---|
| `has_condition` | `work_interfere` blank or not | Yes 986 / No 261 | DQ-05 |
| `gender_clean` | `Gender` | Male 987 / Female 247 / Gender-diverse 13 | DQ-02 |
| `employment_type` | `self_employed` | Employee 1,088 / Self-employed 141 / Unknown 18 | DQ-14 |
| `age_group` | `Age` | 18–24: 156 · 25–34: 707 · 35–44: 320 · 45+: 68 | DQ-28 |
| `region` | `Country` | US 746 · UK & Ireland 210 · Europe (other) 153 · Canada/Australia/NZ 100 · Rest of world 38 | DQ-24 |
| `size_rank` | `no_employees` | 1–6 | DQ-20 |
| `leave_score` | `leave` | 1–4, blank for "Don't know" | DQ-20 |
| `interfere_score` | `work_interfere` | 1–4, blank for "No condition" | DQ-20 |
| `knows_leave_policy` | `leave` | Yes 687 / No 560 | DQ-20 |
| `has_comment` | `comments` | Yes 160 / No 1,087 | DQ-08 |
| `survey_wave` | `timestamp` | Main 1,171 / Late 76 | DQ-18 |
| `uncertainty_score` | 7 support questions | 0–7 | DQ-21 |
| `support_score` | 6 support questions | 0–6 count of "Yes" — **employees only** | DQ-14 + DQ-21 |

`support_score` and `uncertainty_score` are the two summary measures the dashboard is built around: one says what the employer provides, the other says whether the employee knows about it.

---

## Phase 2 summary

- **Rows:** 1,259 → **1,247** (8 invalid ages, 4 resubmissions)
- **Values changed:** 3 state values cleared; 4 columns relabelled (`work_interfere`, `state`, plus `gender_clean`/`employment_type` as new columns rather than edits)
- **Columns:** 27 → **40** (13 derived)
- **Nothing invented:** every fill is a label for a meaning the blank already carried
- **Two denominators, stated on every chart:** 1,247 overall · 1,088 for employer-support questions
- **Findings produced by the cleaning itself:**
  1. 361 respondents (29%) have a condition but have never sought treatment
  2. Treatment-seeking falls from 61.8% to 26.9% as uncertainty about employer support rises
  3. Women sought treatment at 68.8% vs 45.5% of men, not explained by who has a condition
