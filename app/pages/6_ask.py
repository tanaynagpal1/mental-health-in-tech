"""Ask MIND//TECH.

An answer desk over the same filtered view the rest of the dashboard uses.

The preset questions are computed in pandas and are the default experience:
exact figures, the n behind each one, no API key and no network. The free-text
box appears only when a key is configured, and even then the model is handed a
precomputed fact sheet rather than the data - so it is summarising arithmetic
that has already happened, not doing arithmetic of its own.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import answers, charts, data, theme

view: pd.DataFrame = st.session_state["view"]
full: pd.DataFrame = st.session_state["full"]
filter_text: str = st.session_state.get("filter_text", "No filters")

theme.hero(
    "The answer desk",
    "Ask MIND//TECH",
    "Every answer here is computed from the same filtered slice you set in the "
    "sidebar, and carries the number of respondents it rests on.",
)

if not data.guard(view, "the answer desk", 50):
    st.stop()

brief = answers.data_brief(view, filter_text)

# --------------------------------------------------------------------------
# What this thing actually knows
# --------------------------------------------------------------------------
with st.expander("What this answer desk can see"):
    st.markdown(
        f"""
        It sees **one fact sheet**, recomputed from your current filters
        (**{len(view):,} of {len(full):,} respondents** — {filter_text}). It does not
        see the raw responses, and it cannot run a new calculation on request.

        The eight questions below are answered by **pandas, not by a language
        model** — the same code that draws the charts. They are exact and they
        are reproducible.

        The fact sheet itself is printed at the bottom of this page. If a number
        is not in it, nothing on this page can tell you that number, and it will
        say so rather than guess.
        """
    )

# --------------------------------------------------------------------------
# Preset questions
# --------------------------------------------------------------------------
charts.section(
    "Questions with exact answers",
    "Pick one. These run in pandas against your current view.",
)

QUESTIONS = list(answers.PRESETS)
asked = st.session_state.get("ask_preset", QUESTIONS[0])

cols = st.columns(2)
for i, q in enumerate(QUESTIONS):
    with cols[i % 2]:
        if st.button(q, key=f"ask_q_{i}", width="stretch"):
            st.session_state["ask_preset"] = q
            asked = q
            st.rerun()

st.markdown(
    f'<div class="mt-answer"><div class="q">{asked}</div></div>',
    unsafe_allow_html=True,
)
st.markdown(answers.PRESETS[asked](view))
st.caption(
    f"Computed from {len(view):,} respondents · {filter_text} · "
    "no language model involved"
)

# --------------------------------------------------------------------------
# Free text, when a key is configured
# --------------------------------------------------------------------------
charts.section("Ask your own question")

if not answers.model_available():
    st.info(
        "**Free-text questions are off.** They need an API key in "
        "`.streamlit/secrets.toml` — either will do:\n\n"
        "```toml\nGEMINI_API_KEY = \"...\"      # free tier, aistudio.google.com/apikey\n"
        "ANTHROPIC_API_KEY = \"sk-ant-...\"\n```\n\n"
        "plus the matching package (`pip install google-genai` or "
        "`pip install anthropic`). Everything above works without either — "
        "the presets are the part that cannot be wrong."
    )
else:
    st.caption(
        f"Answers come from **{answers.provider_label()}**, given the fact sheet "
        "below and nothing else. It is instructed to refuse figures that are not "
        "in the sheet and to quote the n behind every percentage. Check anything "
        "surprising against the charts."
    )

    if "ask_history" not in st.session_state:
        st.session_state["ask_history"] = []

    for turn in st.session_state["ask_history"]:
        with st.chat_message(turn["role"]):
            st.markdown(turn["display"])

    question = st.chat_input("Ask about this slice of the survey")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Reading the fact sheet..."):
                    # Only prior turns are replayed - the brief is attached to
                    # the current question, so a filter change takes effect
                    # immediately instead of being contradicted by history.
                    reply = answers.ask_model(
                        question, brief,
                        [{"role": t["role"], "content": t["display"]}
                         for t in st.session_state["ask_history"][-6:]],
                    )
                st.markdown(reply)
                st.session_state["ask_history"] += [
                    {"role": "user", "display": question},
                    {"role": "assistant", "display": reply},
                ]
            except Exception as exc:
                st.error(
                    f"The model call failed: `{type(exc).__name__}: {exc}`\n\n"
                    "The preset questions above are unaffected — they never "
                    "touch the network."
                )

    if st.session_state["ask_history"]:
        if st.button("Clear conversation", key="ask_clear"):
            st.session_state["ask_history"] = []
            st.rerun()

# --------------------------------------------------------------------------
# The fact sheet, in full
# --------------------------------------------------------------------------
charts.section(
    "The fact sheet",
    "Everything this page is allowed to say, recomputed from your current "
    "filters. Nothing else is available to it.",
)

with st.expander(f"Show the {len(brief.splitlines())} lines of computed facts"):
    st.code(brief, language="markdown")

st.download_button(
    "Download this fact sheet",
    brief,
    file_name="mindtech_brief.md",
    mime="text/markdown",
    width="content",
)

st.caption(
    f"Showing {len(view):,} of {len(full):,} respondents · {filter_text}"
)