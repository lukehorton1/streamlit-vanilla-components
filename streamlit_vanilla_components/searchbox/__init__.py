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


def _normalise(results) -> list[dict[str, str]]:
    """Turn `str` or `(value, label)` items into `{"value", "label"}` dicts."""
    options = []
    for item in results or []:
        if isinstance(item, (tuple, list)):
            value, label = item
        else:
            value = label = item
        options.append({"value": str(value), "label": str(label)})
    return options


def _rank(options: list[dict[str, str]], term: str) -> list[dict[str, str]]:
    """Stable sort by match quality, judged on the label text before the first comma."""
    t = term.strip().lower()
    if not t:
        return options
    word_start = re.compile(r"\b" + re.escape(t))

    def tier(option: dict[str, str]) -> int:
        text = option["label"].split(",")[0].strip().lower()
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
    search_fn: Callable[[str], list[str] | list[tuple[str, str]]],
    placeholder: str = "Type to search...",
    key: str = "live_search",
    *,
    on_change: Callable | None = None,
    on_submit: Callable | None = None,
    on_clear: Callable | None = None,
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
    width: str | int = "stretch",
) -> str | None:
    """Show a text box whose dropdown is filled by `search_fn(search_term)`.

    `search_fn` returns a list (e.g. from a SQL query) and runs after the user pauses
    typing for `debounce` milliseconds. Each item is either a string, or a
    `(value, label)` tuple: the label is shown, the value is returned (as a string).
    Returns the last option the user picked (or `default`).

    `on_change` runs when the typed text changes, `on_submit` when an option is picked
    and `on_clear` when the box is cleared (the X button, or deleting all the text).
    `st.session_state[key].selected` holds the value, not the label. All run before the script reruns, like native widgets, and can read
    `st.session_state[key].query` and `st.session_state[key].selected`.

    `rank=True` re-orders the results by match quality: exact match, starts with the
    term, a word starts with the term, contains the term. Results in the same tier keep
    the order `search_fn` returned them in, so sort by e.g. population there. Because
    ranking only sees what `search_fn` returns, return more candidates than
    `max_results` or the best match may already have been cut off.

    `min_chars` holds back searching until enough text is typed and `max_results` caps
    the list (applied after ranking).
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

    options: list[dict[str, str]] = []
    if len(query) >= min_chars:
        options = _normalise(search_fn(query))
        if rank:
            options = _rank(options, query)
        if max_results is not None:
            options = options[:max_results]

    result = _COMPONENT(
        key=key,
        data={
            "options": options,
            "placeholder": placeholder,
            "initial": selected or "",
            "debounce": max(0, int(debounce)),
            "label": label,
            "labelVisibility": label_visibility,
            "help": help,
            "disabled": disabled,
        },
        width=width,
        on_query_change=wrap(on_change),
        on_selected_change=lambda: None,
        on_submitted_change=wrap(on_submit),
        on_cleared_change=wrap(on_clear),
    )
    if result.selected is None:
        return default
    return result.selected or None
