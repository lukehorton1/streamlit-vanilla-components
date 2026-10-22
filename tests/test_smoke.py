"""Smoke tests: the package imports, ships its frontend assets, and renders in a Streamlit app."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import streamlit_vanilla_components as svc
from streamlit_vanilla_components.searchbox import _normalise, _rank

PACKAGE_DIR = Path(svc.__file__).parent
FRONTEND_DIRS = [PACKAGE_DIR / "searchbox" / "frontend", PACKAGE_DIR / "stateful_button" / "frontend"]


def test_public_api_exports():
    assert callable(svc.st_live_searchbox)
    assert callable(svc.stateful_button)
    assert set(svc.__all__) == {"st_live_searchbox", "stateful_button"}


@pytest.mark.parametrize("folder", FRONTEND_DIRS, ids=lambda p: p.parent.name)
@pytest.mark.parametrize("name", ["index.html", "index.js", "style.css"])
def test_frontend_assets_present(folder, name):
    path = folder / name
    assert path.is_file(), f"missing {path}"
    assert path.read_text(encoding="utf-8").strip(), f"empty {path}"


def _labels(options):
    return [o["label"] for o in options]


def test_normalise_accepts_strings_and_tuples():
    assert _normalise(["a", ("P1", "P1 · Liverpool"), (2, "Two")]) == [
        {"value": "a", "label": "a"},
        {"value": "P1", "label": "P1 · Liverpool"},
        {"value": "2", "label": "Two"},
    ]


def test_normalise_keeps_duplicates():
    assert len(_normalise([("A", "x"), ("A", "x")])) == 2


def test_rank_puts_exact_matches_before_partial_matches():
    options = _normalise(["Old Liverpool", "Liverpool, United Kingdom", "Liverpool"])
    ranked = _labels(_rank(options, "liverpool"))
    assert ranked[-1] == "Old Liverpool"
    assert set(ranked[:2]) == {"Liverpool, United Kingdom", "Liverpool"}


def test_rank_uses_label_not_value():
    options = _normalise([("zzz", "Other"), ("liverpool", "Liverpool")])
    assert _labels(_rank(options, "liverpool"))[0] == "Liverpool"


def test_rank_blank_term_keeps_order():
    options = _normalise(["b", "a"])
    assert _rank(options, "  ") == options


def test_searchbox_signature():
    import inspect

    params = inspect.signature(svc.st_live_searchbox).parameters
    assert "on_clear" in params
    assert "clear_on_submit" not in params


def test_stateful_button_renders_in_app():
    # AppTest uses a fresh component registry per run; the module-level
    # registration only happens on import, so reload it inside the script.
    script = """
import importlib
import streamlit as st

sb = importlib.import_module("streamlit_vanilla_components.stateful_button")
importlib.reload(sb)
if sb.stateful_button("Go", key="go"):
    st.write("clicked")
"""
    at = AppTest.from_string(script).run()
    assert not at.exception
