"""The answer engine behind Ask MIND//TECH.

Two layers, and the order matters.

The PRESET questions are answered by pandas. They run against the filtered
view, return exact figures with the n they rest on, and work with no API key,
no network and no model. They are the product; they cannot hallucinate,
because there is nothing in them that generates text from a distribution.

The free-text layer is optional. When an API key is configured it hands a
model a precomputed fact sheet - never the rows - and asks it to answer only
from that sheet. Everything the model can say has already been computed here.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import charts

# --------------------------------------------------------------------------
# The fact sheet
# --------------------------------------------------------------------------
SUPPORT_LABELS = {
    "benefits": "employer provides mental health benefits",
    "care_options": "knows what care options are covered",
    "wellness_program": "mental health raised in a wellness programme",
    "seek_help": "employer says where to seek help",
    "anonymity": "anonymity is protected",
    "mental_vs_physical": "employer treats it as seriously as physical health",
}

FACTOR_COLUMNS = {
    "family history of mental illness": "family_history",
    "gender": "gender_clean",
    "age group": "age_group",
    "region": "region",
    "company size": "no_employees",
    "knows the care options": "care_options",
    "employer offers benefits": "benefits",
    "ease of taking medical leave": "leave",
    "has seen a colleague penalised": "obs_consequence",
    "fears consequences at work": "mental_health_consequence",
    "would tell coworkers": "coworkers",
    "would tell supervisor": "supervisor",
    "works remotely": "remote_work",
    "works at a tech company": "tech_company",
}


def _rate(frame: pd.DataFrame, col: str = "treatment", val: str = "Yes") -> float:
    return frame[col].eq(val).mean() * 100 if len(frame) else 0.0


@st.cache_data(show_spinner=False)
def data_brief(view: pd.DataFrame, filter_text: str) -> str:
    """A compact fact sheet describing the CURRENT view, in plain text.

    Everything a model is allowed to say is in here. It is regenerated every
    time the filters change, so an answer can never describe a slice the
    reader is not looking at.
    """
    n = len(view)
    if n == 0:
        return "No respondents match the current filters."

    emp = view[view.employment_type.eq("Employee")]
    cond = view.has_condition.eq("Yes")
    treated = view.treatment.eq("Yes")

    lines = [
        "# MIND//TECH data brief",
        f"Source: OSMI Mental Health in Tech Survey 2014, cleaned to 1,247 rows.",
        f"Current view: {n:,} respondents. Filters: {filter_text}.",
        "",
        "## Headline",
        f"- Reports a mental health condition: {cond.mean() * 100:.1f}% ({int(cond.sum()):,} people)",
        f"- Sought treatment: {treated.mean() * 100:.1f}% ({int(treated.sum()):,} people)",
        f"- Reports a condition but never sought treatment: {int((cond & ~treated).sum()):,} people "
        f"({(cond & ~treated).mean() * 100:.1f}% of this view)",
        f"- Employees (self-employed excluded): {len(emp):,}",
        "",
        "## Treatment-seeking by factor (rate, n)",
    ]

    for label, col in FACTOR_COLUMNS.items():
        if col not in view.columns:
            continue
        g = view.groupby(col, observed=True).agg(
            n=("treatment", "size"),
            rate=("treatment", lambda s: s.eq("Yes").mean() * 100))
        g = g[g.n >= 20]
        if len(g) < 2:
            continue
        parts = [f"{i}: {r.rate:.1f}% (n={int(r.n)})" for i, r in g.iterrows()]
        lines.append(f"- {label} - " + "; ".join(parts))

    if len(emp) >= 20:
        lines += ["", "## What employers provide (employees only, n=%d)" % len(emp)]
        for col, label in SUPPORT_LABELS.items():
            share = emp[col].value_counts(normalize=True) * 100
            unsure = share.get("Don't know", 0.0) + share.get("Not sure", 0.0)
            lines.append(
                f"- {label}: yes {share.get('Yes', 0.0):.1f}%, "
                f"no {share.get('No', 0.0):.1f}%, don't know {unsure:.1f}%")

    lines += ["", "## Stigma: the same question asked twice"]
    for label, m, p in [
        ("fears negative consequences at work",
         "mental_health_consequence", "phys_health_consequence"),
        ("would raise it in a job interview",
         "mental_health_interview", "phys_health_interview"),
    ]:
        lines.append(f"- {label}: mental health {_rate(view, m):.1f}%, "
                     f"physical health {_rate(view, p):.1f}%")

    if "uncertainty_score" in view.columns:
        u = view.groupby(view.uncertainty_score.astype(int)).agg(
            n=("treatment", "size"),
            rate=("treatment", lambda s: s.eq("Yes").mean() * 100))
        u = u[u.n >= 20]
        if len(u) >= 2:
            lines += ["", "## Uncertainty about employer support (0 = knows everything)",
                      "- " + "; ".join(f"score {i}: {r.rate:.1f}% treated (n={int(r.n)})"
                                       for i, r in u.iterrows())]

    counts = view.country.value_counts()
    big = counts[counts >= 20]
    if len(big):
        lines += ["", "## Geography (countries with n >= 20 only)"]
        for c, cn in big.items():
            sub = view[view.country.eq(c)]
            lo, hi = charts.wilson(int(sub.treatment.eq("Yes").sum()), int(cn))
            lines.append(f"- {c}: {_rate(sub):.1f}% treated, 95% CI {lo:.1f}-{hi:.1f}, n={cn}")
        hidden = int(counts[counts < 20].sum())
        lines.append(f"- {hidden} respondents live in {int((counts < 20).sum())} countries "
                     "below the reporting threshold and have no individual figure.")

    lines += [
        "",
        "## Rules you must follow when answering",
        "- Say 'treatment-seeking', never 'prevalence of mental illness'. The survey "
        "never asked for a diagnosis.",
        "- Never report a figure for a group with fewer than 20 respondents "
        "(10 for US states). Say the sample is too small instead.",
        "- Always state the n behind any percentage you give.",
        "- The six employer-support questions apply to employees only (1,088 of 1,247 "
        "unfiltered); the self-employed are their own employer.",
        "- This is a self-selected volunteer sample: 79% male, 82% tech, 60% US. Say "
        "'X% of respondents', never 'X% of tech workers'.",
        "- Everything here is association, not cause.",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Preset answers - pure pandas, no model
# --------------------------------------------------------------------------
def _headline(view: pd.DataFrame) -> str:
    n = len(view)
    cond = view.has_condition.eq("Yes")
    treated = view.treatment.eq("Yes")
    gap = int((cond & ~treated).sum())
    return (
        f"Of the **{n:,} respondents** in view, **{cond.mean() * 100:.1f}%** "
        f"({int(cond.sum()):,}) report a mental health condition and "
        f"**{treated.mean() * 100:.1f}%** ({int(treated.sum()):,}) have sought "
        f"treatment.\n\n**{gap:,} people** — {gap / n * 100:.1f}% of this view — report "
        "a condition and have never sought treatment. That gap is what the rest of "
        "the dashboard is about."
    )


def _biggest_factor(view: pd.DataFrame) -> str:
    rows = []
    for label, col in FACTOR_COLUMNS.items():
        if col not in view.columns:
            continue
        g = view.groupby(col, observed=True).agg(
            n=("treatment", "size"),
            rate=("treatment", lambda s: s.eq("Yes").mean() * 100))
        g = g[g.n >= 20]
        if len(g) < 2:
            continue
        lo, hi = g.rate.idxmin(), g.rate.idxmax()
        rows.append((g.rate[hi] - g.rate[lo], label, lo, g.rate[lo], int(g.n[lo]),
                     hi, g.rate[hi], int(g.n[hi])))
    if not rows:
        return "No factor has two groups of 20+ respondents under these filters."
    rows.sort(reverse=True)
    out = ["Ranked by the widest gap between two answer groups, each with at least "
           "20 respondents:\n"]
    for gap, label, lo, lo_r, lo_n, hi, hi_r, hi_n in rows[:5]:
        out.append(f"- **{label}** — {gap:.1f}pp: *{hi}* {hi_r:.1f}% (n={hi_n}) "
                   f"vs *{lo}* {lo_r:.1f}% (n={lo_n})")
    out.append("\nThese are raw differences with nothing held constant. The forest "
               "plot on the Overview page is the version that controls for the rest.")
    return "\n".join(out)


def _gender(view: pd.DataFrame) -> str:
    g = view.groupby("gender_clean", observed=True).agg(
        n=("treatment", "size"),
        treated=("treatment", lambda s: s.eq("Yes").mean() * 100),
        cond=("has_condition", lambda s: s.eq("Yes").mean() * 100))
    lines = []
    for name, r in g.iterrows():
        if r.n < 20:
            lines.append(f"- **{name}** — only {int(r.n)} respondents, below the "
                         "reporting threshold, so no figure.")
        else:
            lines.append(f"- **{name}** — {r.treated:.1f}% sought treatment "
                         f"({r.cond:.1f}% report a condition), n={int(r.n)}")
    return ("\n".join(lines) + "\n\nThe gap is not explained by who has a condition: "
            "the condition rates are much closer together than the treatment rates.")


def _mental_vs_physical(view: pd.DataFrame) -> str:
    a = _rate(view, "mental_health_consequence")
    b = _rate(view, "phys_health_consequence")
    c = _rate(view, "mental_health_interview")
    d = _rate(view, "phys_health_interview")
    return (
        f"Same {len(view):,} people, same employers, two versions of each question:\n\n"
        f"- Fears negative consequences at work: **{a:.1f}%** for mental health vs "
        f"**{b:.1f}%** for physical health\n"
        f"- Would raise it in a job interview: **{c:.1f}%** for mental health vs "
        f"**{d:.1f}%** for physical health\n\n"
        "The two gaps run in opposite directions, which is what makes this specific "
        "to mental health rather than to illness in general."
    )


def _uncertainty(view: pd.DataFrame) -> str:
    u = view.groupby(view.uncertainty_score.astype(int)).agg(
        n=("treatment", "size"),
        rate=("treatment", lambda s: s.eq("Yes").mean() * 100))
    u = u[u.n >= 20]
    if len(u) < 2:
        return "Not enough respondents per uncertainty level under these filters."
    first, last = u.iloc[0], u.iloc[-1]
    emp = view[view.employment_type.eq("Employee")]
    anon = ""
    if len(emp) >= 20:
        share = emp.anonymity.value_counts(normalize=True) * 100
        # Pulled out of the f-string: the apostrophe in "Don't know" ends the
        # inner quote on Python < 3.12, so the expression cannot live inline.
        unsure = share.get("Don't know", 0.0)
        anon = (f"\n\nFor context, **{unsure:.1f}%** of the "
                f"{len(emp):,} employees in view do not know whether their anonymity "
                "would be protected - the largest single answer in the survey.")
    return (
        f"Treatment-seeking falls from **{first.rate:.1f}%** among people who could "
        f"answer every question about employer support (n={int(first.n)}) to "
        f"**{last.rate:.1f}%** among those who could answer fewest "
        f"(n={int(last.n)}).{anon}\n\nNot knowing behaves like a barrier — arguably a "
        "worse one than a known 'no', because there is nothing to act on."
    )


def _company_size(view: pd.DataFrame) -> str:
    emp = view[view.employment_type.eq("Employee")]
    if len(emp) < 40:
        return "Too few employees in this view to break down by company size."
    g = emp.groupby("no_employees", observed=True).agg(
        n=("benefits", "size"),
        yes=("benefits", lambda s: s.eq("Yes").mean() * 100))
    g = g[g.n >= 20]
    if len(g) < 2:
        return "No company-size band has 20+ employees under these filters."
    lines = [f"- **{i}** — {r.yes:.1f}% say their employer provides mental health "
             f"benefits (n={int(r.n)})" for i, r in g.iterrows()]
    return ("Employees only, since the self-employed have no employer to answer "
            "about:\n\n" + "\n".join(lines))


def _geography(view: pd.DataFrame) -> str:
    counts = view.country.value_counts()
    big = counts[counts >= 20]
    if not len(big):
        return "No country reaches 20 respondents under these filters."
    lines = []
    for c, n in big.items():
        sub = view[view.country.eq(c)]
        lo, hi = charts.wilson(int(sub.treatment.eq("Yes").sum()), int(n))
        lines.append(f"- **{c}** — {_rate(sub):.1f}% (95% CI {lo:.1f}–{hi:.1f}, n={n})")
    hidden = int(counts[counts < 20].sum())
    return ("\n".join(lines) + f"\n\nOnly {len(big)} countries clear the n = 20 "
            f"threshold. The other {int((counts < 20).sum())} countries hold {hidden} "
            "respondents between them and get no individual figure — several sent "
            "exactly one person.")


def _witnessing(view: pd.DataFrame) -> str:
    seen = view[view.obs_consequence.eq("Yes")]
    unseen = view[view.obs_consequence.eq("No")]
    if len(seen) < 20 or len(unseen) < 20:
        return "Too few respondents on one side of this question in the current view."
    rows = [("Sought treatment", "treatment", "Yes"),
            ("Would tell their supervisor", "supervisor", "Yes"),
            ("Fears consequences at work", "mental_health_consequence", "Yes")]
    lines = []
    for label, col, val in rows:
        a, b = _rate(unseen, col, val), _rate(seen, col, val)
        lines.append(f"- **{label}** — {a:.1f}% → {b:.1f}% ({b - a:+.1f}pp)")
    return (f"Comparing the {len(seen):,} people who have seen a colleague penalised "
            f"with the {len(unseen):,} who have not:\n\n" + "\n".join(lines) +
            "\n\nThe directions differ. People who have seen it happen seek **more** "
            "treatment and are **less** willing to tell a supervisor — they do not "
            "stop dealing with it, they stop talking about it at work.")


PRESETS: dict[str, callable] = {
    "How many people are affected, and how many got help?": _headline,
    "What predicts treatment-seeking most strongly?": _biggest_factor,
    "Do women seek treatment more than men?": _gender,
    "How different is mental health from physical health?": _mental_vs_physical,
    "Does knowing about employer support matter?": _uncertainty,
    "Do bigger companies offer more?": _company_size,
    "Which countries can actually be reported?": _geography,
    "What happens after someone sees a colleague penalised?": _witnessing,
}


# --------------------------------------------------------------------------
# The optional model layer
# --------------------------------------------------------------------------
SYSTEM = """You are the analyst behind the MIND//TECH dashboard, answering \
questions about the 2014 OSMI Mental Health in Tech Survey.

You will be given a DATA BRIEF computed from the exact slice the reader is \
looking at. Answer ONLY from that brief.

Hard rules:
- If the brief does not contain the number, say so plainly and suggest which \
  page of the dashboard would show it. Never estimate, interpolate or recall \
  a figure from anywhere else.
- Quote the n behind every percentage.
- Say "treatment-seeking", never "prevalence of mental illness".
- Never give a figure for a group of fewer than 20 respondents.
- Describe associations, never causes.
- Be brief: three or four sentences unless asked for more. No preamble.

You are talking to an analyst. Do not add disclaimers they did not ask for, \
and do not offer mental health advice - this is a dataset, not a patient."""


def secret(name: str, default=None):
    """Read a secret without blowing up when there is no secrets file.

    st.secrets raises rather than returning empty when .streamlit/secrets.toml
    does not exist, which is the normal state of a fresh clone.
    """
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _importable(module: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module) is not None


def provider() -> str | None:
    """Which model backend is usable right now, or None.

    Deliberately provider-agnostic. The fact sheet and the system prompt are
    the product; the model is a text renderer for them, and which vendor does
    that rendering should be a line in secrets.toml, not a rewrite.

    Set LLM_PROVIDER to force one when both keys are present.
    """
    have = {}
    if (secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY")) and _importable("google.genai"):
        have["gemini"] = True
    if secret("ANTHROPIC_API_KEY") and _importable("anthropic"):
        have["anthropic"] = True

    forced = secret("LLM_PROVIDER")
    if forced and str(forced).lower() in have:
        return str(forced).lower()
    for name in ("gemini", "anthropic"):     # free tier first
        if name in have:
            return name
    return None


def model_available() -> bool:
    return provider() is not None


# --- Gemini ---------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def _gemini_model(_key: str) -> str:
    """Resolve a model id from the API instead of hardcoding one.

    A hardcoded id works until that model is retired, then breaks for a
    reason nobody remembers. GEMINI_MODEL pins one if you want that.
    """
    pinned = secret("GEMINI_MODEL")
    if pinned:
        return str(pinned)
    from google import genai
    # The client MUST be held in a variable: models.list() returns a lazy
    # pager, and a temporary client is closed before the pager iterates
    # ("Cannot send a request, as the client has been closed").
    client = genai.Client(api_key=_key)
    models = client.models.list(config={"query_base": True})
    usable = []
    for m in models:
        actions = getattr(m, "supported_actions", None)
        if actions and "generateContent" not in actions:
            continue
        usable.append(m.name)
    # "flash" is the small, fast, free-tier-friendly tier.
    for want in ("flash-lite", "flash", "pro"):
        match = [n for n in usable if want in n.lower()]
        if match:
            return match[0]
    if not usable:
        raise RuntimeError("No Gemini model supports generateContent for this key.")
    return usable[0]


def _ask_gemini(question: str, brief: str, history: list[dict]) -> str:
    from google import genai
    from google.genai import types

    key = str(secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY"))
    client = genai.Client(api_key=key)
    # Gemini calls the assistant turn "model", not "assistant".
    contents = [
        types.Content(role="model" if t["role"] == "assistant" else "user",
                      parts=[types.Part(text=t["content"])])
        for t in history
    ]
    contents.append(types.Content(role="user", parts=[types.Part(
        text=f"DATA BRIEF (the only facts you may use):\n\n{brief}\n\n"
             f"QUESTION: {question}")]))

    reply = client.models.generate_content(
        model=_gemini_model(key),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            max_output_tokens=900,
            temperature=0.2,
        ),
    )
    return (reply.text or "").strip() or "The model returned nothing."


# --- Anthropic ------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def _anthropic_model(_key: str) -> str:
    pinned = secret("ANTHROPIC_MODEL")
    if pinned:
        return str(pinned)
    import anthropic
    client = anthropic.Anthropic(api_key=_key)
    ids = [m.id for m in client.models.list(limit=20).data]
    for want in ("haiku", "sonnet"):
        match = [i for i in ids if want in i.lower()]
        if match:
            return match[0]
    return ids[0]


def _ask_anthropic(question: str, brief: str, history: list[dict]) -> str:
    import anthropic

    key = str(secret("ANTHROPIC_API_KEY"))
    client = anthropic.Anthropic(api_key=key)
    messages = history + [
        {"role": "user",
         "content": f"DATA BRIEF (the only facts you may use):\n\n{brief}\n\n"
                    f"QUESTION: {question}"},
    ]
    reply = client.messages.create(
        model=_anthropic_model(key), max_tokens=900,
        system=SYSTEM, messages=messages,
    )
    return "".join(b.text for b in reply.content if b.type == "text")


def ask_model(question: str, brief: str, history: list[dict]) -> str:
    """Send one question with the brief as context. Raises on failure."""
    which = provider()
    if which == "gemini":
        return _ask_gemini(question, brief, history)
    if which == "anthropic":
        return _ask_anthropic(question, brief, history)
    raise RuntimeError("No model provider is configured.")


def provider_label() -> str:
    return {"gemini": "Google Gemini", "anthropic": "Anthropic Claude"}.get(
        provider() or "", "none")