# Streamlit vanilla components

Lightweight [Streamlit components v2](https://docs.streamlit.io/develop/api-reference/custom-components) in plain HTML, CSS and JavaScript. No npm packages, no build step. Each component copies its native Streamlit look and follows the active theme.

Built using GitHub Copilot as an AI coding agent, with manual oversight, design and testing throughout.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://vanilla-components.streamlit.app)

## Installation

```bash
pip install streamlit-vanilla-components
```

Requires Python 3.10+ and Streamlit 1.57+.

## Quickstart

```python
from streamlit_vanilla_components import st_live_searchbox, stateful_button
```

*Or download the `example.py` demo and run locally:* `streamlit run example.py`


## Components

- [`st_live_searchbox`](#st_live_searchbox)
- [`stateful_button`](#stateful_button)

---

## `st_live_searchbox`

A search box whose dropdown is filled by your Python function as the user types. Returns the picked option as a string.

```python
def search_places(term: str) -> list[str]:
    return db.query("SELECT label FROM places WHERE label ILIKE %s LIMIT 300", f"%{term}%")

choice = st_live_searchbox(search_places, placeholder="Search a place...", rank=True, max_results=50)
```

### Parameters

| Parameter | Description |
|---|---|
| `search_fn` *(callable)* | Receives the typed text and returns a list of options: strings, or `(value, label)` tuples. Required. |
| `placeholder` *(str)* | Placeholder text. Default `"Type to search..."`. |
| `key` *(str)* | Widget key. Default `"live_search"`. |
| `on_change` *(callable or None)* | Runs when the typed text changes. |
| `on_submit` *(callable or None)* | Runs when an option is picked. |
| `on_clear` *(callable or None)* | Runs when the box is cleared, by the ✕ button or by deleting all the text. |
| `args` *(tuple or None)* | Passed to `on_change`, `on_submit` and `on_clear`. |
| `kwargs` *(dict or None)* | Passed to `on_change`, `on_submit` and `on_clear`. |
| `debounce` *(int)* | Milliseconds to wait after typing stops before searching. Default `250`. |
| `default` *(str or None)* | Returned until something is picked. Default `None`. |
| `label` *(str or None)* | Label above the box. |
| `label_visibility` *(str)* | `"visible"`, `"hidden"` or `"collapsed"`. Default `"visible"`. |
| `help` *(str or None)* | Tooltip next to the label. |
| `disabled` *(bool)* | Disables the box. Default `False`. |
| `min_chars` *(int)* | Characters typed before `search_fn` runs. Default `1`. |
| `max_results` *(int or None)* | Maximum options shown, applied after ranking. Default `None`. |
| `rank` *(bool)* | Sorts options by match quality (exact, starts with, word starts with, contains). Default `False`. |
| `width` *(str or int)* | `"stretch"` or a pixel width. Default `"stretch"`. |

**Returns** *(str or None)*: the picked option's value, or `default`.

### See also

- Typing again after a pick replaces it with the new text.
- Return `(value, label)` tuples to show a rich label while returning a short value, e.g. `("P00769", "P00769 · Liverpool · United Kingdom · pop. 508,961")`. Build the label in your query so only matching rows are sent. The value is returned as a string, `rank` and `max_results` use the label, and duplicates are kept.
- `st.session_state[key].selected` holds the value, not the label.
- Ranking only sees what `search_fn` returns, so return more candidates than `max_results`.

---

## `stateful_button`

A `st.button` look-alike that disables itself on click, shows a spinner in place of its icon while your code runs, then a tick on success.

```python
with stateful_button("Submit", type="primary") as clicked:
    if clicked:
        save_records()
        st.success("Saved!")

# or, for a single function call
stateful_button("Run job", on_click=run_job, args=("Job 1",))
```

### Parameters

Same as `st.button`, plus `icon_position` and `wrap`.

| Parameter | Description |
|---|---|
| `label` *(str)* | Button text. Plain text, no Markdown. Required. |
| `key` *(str or None)* | Widget key. Derived from the other arguments if omitted. |
| `help` *(str or None)* | Tooltip. |
| `on_click` *(callable or None)* | Work to run. The button stays busy until it finishes. |
| `args` *(tuple or None)* | Passed to `on_click`. |
| `kwargs` *(dict or None)* | Passed to `on_click`. |
| `type` *(str)* | `"primary"`, `"secondary"` or `"tertiary"`. Default `"secondary"`. |
| `icon` *(str or None)* | Emoji or `:material/name:`. |
| `icon_position` *(str)* | `"left"` or `"right"`. Default `"left"`. |
| `disabled` *(bool)* | Disables the button. Default `False`. |
| `width` *(str or int)* | `"content"`, `"stretch"` or a pixel width. Default `"content"`. |
| `shortcut` *(str or None)* | Keyboard shortcut. |
| `wrap` *(bool or None)* | Whether the label may wrap. |

**Returns** *(StatefulButton)*: truthy on the run it was clicked. Works as a context manager, and `.release(success=True)` ends the busy state early.

### See also

- Use either the `with` form or `on_click`. Without either, the spinner never stops.
- Errors in the `with` block or in `on_click` re-enable the button, then raise.
