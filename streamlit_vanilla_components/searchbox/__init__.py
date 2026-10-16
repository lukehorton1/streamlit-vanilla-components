"""A live search box: typing runs your Python search function."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import re

import streamlit as st

_FRONTEND = Path(__file__).parent / "frontend"


def _read(name: str) -> str:
    return (_FRONTEND / name).read_text(encoding="utf-8")


_COMPONENT = st.components.v2.component(
    "live_searchbox",
    html=_read("index.html"),
    css=_read("style.css"),
    js=_read("index.js"),
)


def _rank(options: list[str], term: str) -> list[str]:
    """Stable sort by match quality, judged on the text before the first comma."""
    t = term.strip().lower()
    if not t:
        return options
    word_start = re.compile(r"\b" + re.escape(t))

    def tier(option: str) -> int:
        text = option.split(",")[0].strip().lower()
        if text == t:
            return 0
        if text.startswith(t):
            return 1
        if word_start.search(text):
            return 2
        if t in text:
            return 3
        return 4

    return sorted(options, key=tier)  # sorted() is stable: incoming order breaks ties


def st_live_searchbox(
    search_fn: Callable[[str], list[str]],
    placeholder: str = "Type to search...",
    key: str = "live_search",
    *,
    on_change: Callable | None = None,
    on_submit: Callable | None = None,
    args: tuple | None = None,
    kwargs: dict | None = None,
    debounce: int = 250,
    default: str | None = None,
    label: str | None = None,
    label_visibility: str = "visible",
    help: str | None = None,
    disabled: bool = False,
    min_chars: int = 1,
    max_results: int | None = None,
    rank: bool = False,
    clear_on_submit: bool = False,
    width: str | int = "stretch",
) -> str | None:
    """Show a text box whose dropdown is filled by `search_fn(search_term)`.

    `search_fn` returns a list of strings (e.g. from a SQL query) and runs after the
    user pauses typing for `debounce` milliseconds. Returns the last option the user
    picked (or `default`).

    `on_change` runs when the typed text changes, `on_submit` when an option is picked.
    Both run before the script reruns, like native widgets, and can read
    `st.session_state[key].query` and `st.session_state[key].selected`.

    `rank=True` re-orders the results by match quality: exact match, starts with the
    term, a word starts with the term, contains the term. Results in the same tier keep
    the order `search_fn` returned them in, so sort by e.g. population there. Because
    ranking only sees what `search_fn` returns, return more candidates than
    `max_results` or the best match may already have been cut off.

    `min_chars` holds back searching until enough text is typed, `max_results` caps the
    list (applied after ranking), and `clear_on_submit` empties the box after a pick.
    """

    def wrap(fn):
        if fn is None:
            return lambda: None
        return lambda: fn(*(args or ()), **(kwargs or {}))

    state = st.session_state.get(key)
    query = getattr(state, "query", None) or ""
    selected = getattr(state, "selected", None)
    if selected is None:
        selected = default
    selected = selected or None  # "" means the user cleared it

    options: list[str] = []
    if len(query) >= min_chars:
        options = [str(o) for o in (search_fn(query) or [])]
        if rank:
            options = _rank(options, query)
        if max_results is not None:
            options = options[:max_results]

    result = _COMPONENT(
        key=key,
        data={
            "options": options,
            "placeholder": placeholder,
            "initial": "" if clear_on_submit else (selected or ""),
            "debounce": max(0, int(debounce)),
            "label": label,
            "labelVisibility": label_visibility,
            "help": help,
            "disabled": disabled,
            "clearOnSubmit": clear_on_submit,
        },
        width=width,
        on_query_change=wrap(on_change),
        on_selected_change=lambda: None,
        on_submitted_change=wrap(on_submit),
    )
    if result.selected is None:
        return default
    return result.selected or None
