# Data Dictionary — Mental Health in Tech Survey (survey.csv)

1,259 rows × 27 columns. Counts below are from the **raw** file, before any cleaning.

## Group 1: Who answered (demographics)

| # | Column | In plain terms | Type | Values / spread | Blanks |
|---|---|---|---|---|---|
| 1 | `Timestamp` | Date and time the person submitted the form | Text (should be a date) | 27 Aug 2014 → 1 Feb 2016; 90% in Aug 2014 | 0 |
| 2 | `Age` | The person's age in years | Number | Valid values 18–72, median 31; 8 impossible values | 0 |
| 3 | `Gender` | Gender, typed freely by the person | Text | 49 different spellings; ~79% male, ~19% female, rest non-binary/trans/junk | 0 |
| 4 | `Country` | Country they live in | Text | 48 countries; US 751, UK 185, Canada 72; 30 countries have fewer than 5 | 0 |
| 5 | `state` | US state, asked only of US residents | Text | 45 state codes; CA 138, WA 70, NY 56 | 515 (non-US) |

## Group 2: Their mental health

| # | Column | The question asked | Values (counts) | Blanks |
|---|---|---|---|---|
| 6 | `family_history` | Does mental illness run in your family? | No 767, Yes 492 | 0 |
| 7 | `treatment` | Have you ever sought treatment for a mental health condition? **This is our main outcome — the closest thing to "does this person have a condition".** | Yes 637, No 622 | 0 |
| 8 | `work_interfere` | *If* you have a condition, does it get in the way of your work? | Sometimes 465, Never 213, Rarely 173, Often 144 | 264 (most likely means "no condition") |

## Group 3: Their job

| # | Column | The question asked | Values (counts) | Blanks |
|---|---|---|---|---|
| 9 | `self_employed` | Do you work for yourself? | No 1,095, Yes 146 | 18 (the first 18 rows) |
| 10 | `no_employees` | How big is the company? (an ordered scale) | 6-25: 290, 26-100: 289, 1000+: 282, 100-500: 176, 1-5: 162, 500-1000: 60 | 0 |
| 11 | `remote_work` | Do you work remotely at least half the time? | No 883, Yes 376 | 0 |
| 12 | `tech_company` | Is your employer mainly a tech company? | Yes 1,031, No 228 | 0 |

## Group 4: What the employer offers (six support questions)

| # | Column | The question asked | Values (counts) | Blanks |
|---|---|---|---|---|
| 13 | `benefits` | Does your employer provide mental health benefits? | Yes 477, Don't know 408, No 374 | 0 |
| 14 | `care_options` | Do you know what mental health care options your employer offers? | No 501, Yes 444, Not sure 314 | 0 |
| 15 | `wellness_program` | Has your employer ever raised mental health in a wellness programme? | No 842, Yes 229, Don't know 188 | 0 |
| 16 | `seek_help` | Does your employer give you resources for learning about mental health and getting help? | No 646, Don't know 363, Yes 250 | 0 |
| 17 | `anonymity` | If you use those resources, is your privacy protected? | **Don't know 819**, Yes 375, No 65 | 0 |
| 18 | `leave` | How easy is it to take medical leave for a mental health reason? (an ordered scale) | Don't know 563, Somewhat easy 266, Very easy 206, Somewhat difficult 126, Very difficult 98 | 0 |

## Group 5: Attitudes and stigma (eight questions)

| # | Column | The question asked | Values (counts) | Blanks |
|---|---|---|---|---|
| 19 | `mental_health_consequence` | Would discussing a **mental** health issue with your employer hurt you? | No 490, Maybe 477, Yes 292 | 0 |
| 20 | `phys_health_consequence` | Would discussing a **physical** health issue hurt you? (the comparison question) | No 925, Maybe 273, Yes 61 | 0 |
| 21 | `coworkers` | Would you discuss a mental health issue with colleagues? | Some of them 774, No 260, Yes 225 | 0 |
| 22 | `supervisor` | Would you discuss it with your manager? | Yes 516, No 393, Some of them 350 | 0 |
| 23 | `mental_health_interview` | Would you raise a **mental** health issue in a job interview? | No 1,008, Maybe 207, **Yes 44** | 0 |
| 24 | `phys_health_interview` | Would you raise a **physical** health issue in a job interview? (the comparison question) | Maybe 557, No 500, Yes 202 | 0 |
| 25 | `mental_vs_physical` | Does your employer take mental health as seriously as physical health? | Don't know 576, Yes 343, No 340 | 0 |
| 26 | `obs_consequence` | Have you seen or heard of a colleague suffering consequences for a mental health condition? | No 1,075, Yes 184 | 0 |

## Group 6: Free text

| # | Column | In plain terms | Blanks |
|---|---|---|---|
| 27 | `comments` | Anything else the person wanted to say | 1,095 (87%) |

---

## How to read this dataset

- **Only one real number.** `Age` is the only numeric column. Everything else is a category, so the analysis is built on counts, percentages and cross-tabs rather than averages and correlations.
- **Three columns have a built-in order** (`no_employees`, `leave`, `work_interfere`). They must be sorted by meaning, not alphabetically.
- **Paired questions.** Four columns exist in mental/physical pairs (`*_consequence`, `*_interview`). The gap between each pair measures stigma directly, and it's one of the strongest stories in the data: 202 people would raise a physical health issue in an interview, against 44 for mental health.
- **"Don't know" is an answer, not a blank.** It appears in 9 columns. 819 people don't know whether their privacy would be protected, which is a finding in itself: support that people don't know about doesn't help them.
- **The three columns with blanks each have a different cause:** `state` (question not asked of non-US), `work_interfere` (asked only of people with a condition), `self_employed` (the question was added after the first 18 responses).
