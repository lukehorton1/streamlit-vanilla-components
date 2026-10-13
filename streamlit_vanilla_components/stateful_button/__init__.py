"""A st.button look-alike that disables itself while your script is busy."""

from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

_FRONTEND = Path(__file__).parent / "frontend"


def _read(name: str) -> str:
    return (_FRONTEND / name).read_text(encoding="utf-8")


# Registered once at import time (re-registering the same name causes warnings)
_COMPONENT = st.components.v2.component(
    "stateful_button",
    html=_read("index.html"),
    css=_read("style.css"),
    js=_read("index.js"),
)


class StatefulButton:
    """Returned by `stateful_button`. Use it as a bool, a context manager, or both."""

    def __init__(self, clicked: bool, release):
        self.clicked = clicked
        self._release = release
        self._released = False

    def release(self, success: bool = True) -> None:
        # Only ever re-render once per run, or Streamlit complains about a duplicate key
        if self.clicked and not self._released:
            self._released = True
            self._release(success)

    def __bool__(self) -> bool:
        return self.clicked

    def __enter__(self) -> StatefulButton:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Runs on success and on errors, so the button never gets stuck
        self.release(exc_type is None)
        return False


def stateful_button(
    label: str,
    key: str | None = None,
    help: str | None = None,
    on_click=None,
    args=None,
    kwargs=None,
    *,
    type: str = "secondary",
    icon: str | None = None,
    icon_position: str = "left",
    disabled: bool = False,
    width: str | int = "content",
    shortcut: str | None = None,
    wrap: bool | None = None,
) -> StatefulButton:
    """Same parameters as `st.button`. Labels are plain text (no Markdown).

    The button disables itself the moment it's clicked and shows a spinner in place
    of its icon, then a tick when the work succeeds. Pick one way to do the work:

        # Several lines, or you want to show results afterwards
        with stateful_button("Submit") as clicked:
            if clicked:
                save_records()

        # A single function call
        stateful_button("Submit", on_click=save_records)

    Without either, nothing tells the button when the work is done, so it keeps
    spinning until the next rerun.
    """
    # Without a key, the same arguments give the same identity on every rerun
    ident = key or hashlib.md5(
        repr((label, type, icon, icon_position, width, shortcut)).encode()
    ).hexdigest()[:10]
    nonce_name = f"_stateful_button_nonce_{ident}"
    done_name = f"_stateful_button_done_{ident}"
    failed_name = f"_stateful_button_failed_{ident}"
    nonce = st.session_state.get(nonce_name, 0)
    # Must match what the browser is already showing, or the data changes and the
    # button resets itself mid-click (losing its spinner and disabled state)
    was_done = st.session_state.pop(done_name, False)

    data = {
        "label": label,
        "help": help,
        "type": type,
        "icon": icon,
        "iconPosition": icon_position,
        "disabled": disabled,
        "width": width,
        "shortcut": shortcut,
        "wrap": wrap,
    }

    def callback():
        if on_click:
            try:
                on_click(*(args or ()), **(kwargs or {}))
            except Exception as e:
                # Raising here would abort the whole run before the button is drawn,
                # so keep the error and raise it later in the script instead
                st.session_state[failed_name] = e

    def mount(n: int, done: bool = False):
        # A new nonce means a new component identity, which gives a fresh idle button
        return _COMPONENT(
            key=f"{ident}-{n}",
            data={**data, "done": done},
            width=width,
            on_clicked_change=callback,
        )

    slot = st.empty()
    with slot:
        result = mount(nonce, done=was_done)

    if not result.clicked:
        return StatefulButton(False, lambda ok: None)

    # The browser keeps the old button disabled. Bump the nonce so the next run
    # (or the end of the `with` block) mounts a fresh, enabled one.
    st.session_state[nonce_name] = nonce + 1

    def release(success: bool):
        # On success the fresh button briefly shows a tick before going back to normal
        st.session_state[done_name] = success
        with slot:
            mount(nonce + 1, done=success)

    button = StatefulButton(True, release)
    if on_click:
        # The callback already ran before this script started, so the work is finished
        error = st.session_state.pop(failed_name, None)
        button.release(error is None)
        if error is not None:
            raise error
    return button
