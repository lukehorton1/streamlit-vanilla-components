# AGENTS.md

Standards for building components in this repo. Components are small, fast, vanilla HTML/CSS/JS Streamlit components that look and behave exactly like native Streamlit widgets.

## Hard rules

- **No npm, no bundlers, no frameworks, no CDN assets.** Plain HTML, CSS and JS only.
- **Streamlit components v2 only** (`st.components.v2`). No iframes, no `declare_component`, no `postMessage`, no `setFrameHeight`. Send values back with `setStateValue` / `setTriggerValue`.
- **Fast and responsive.** Fast first paint, no layout shift, fill the container width, and no work per keystroke or render beyond what is needed. Debounce anything that triggers a Streamlit rerun.
- **Native look, copied not guessed.** See "Matching native styling" below.

## Structure

```
streamlit_vanilla_components/
  __init__.py              <- export every public component here
  <name>/
    __init__.py            <- Python API and component registration
    frontend/
      index.html
      index.js
      style.css
example.py                 <- ONE shared demo app for all components
```

- Use `stateful_button` and `searchbox` as the reference implementations.
- Frontend files are read at import time. Restart Streamlit after editing them (reload is not enough).
- Add a section for each new component to `example.py`. Do not create per-component example files.

## Python API

- Mirror the signature of the closest native widget: `key`, `on_change`, `args`/`kwargs`, `label`, `label_visibility`, `help`, `disabled`, `width`, etc.
- A state key only appears in the component result if its `on_<key>_change` callback is passed, so always pass wrappers.
- Return plain Python values (`str | None`, etc.), not raw component dicts.
- Type-hint the public function and give it a short docstring.

## JavaScript

- The default export runs again on every data change. Keep UI state (open/closed, timers, selection) on `parentElement`, not in closure variables.
- Query elements from `parentElement` (shadow DOM). Clean up listeners and timers.
- Prefer `textContent` and DOM APIs over `innerHTML` for any user or server data.
- Support keyboard use and `disabled`, and set ARIA roles where native widgets do.

## Theming

- Style only with Streamlit's `--st-*` CSS variables (primary, background, secondary background, text, font, border colour, button radius), with sensible fallbacks.
- Do not hard-code colours. Derive tints with `color-mix(in srgb, var(--text) 60%, transparent)`.
- Check the component in both light and dark themes.

## Matching native styling (one-to-one)

Copy native CSS directly. Use screenshots only when the DOM or CSS cannot be read.

1. Add the closest native widget to `example.py` temporarily, next to your component.
2. In the browser, read the real thing with JavaScript (`evaluate_javascript` in the browser canvas, or DevTools):
   - structure: `element.outerHTML` (including SVG icons, copied verbatim);
   - computed values: `getComputedStyle(el)` for padding, font size, line height, weight, radius, colours, flex behaviour;
   - authored rules: walk `document.styleSheets` and `cssRules` for the emotion class (for example `.st-emotion-cache-xxxx`) to get `:hover`, `:focus-visible` and `[data-*]` states.
3. Reproduce the same DOM structure (not just the same look) and the same values, in rem where native uses rem.
4. Verify with numbers: compare `getBoundingClientRect()` of both widgets (height, width, offsets).
5. Remove the temporary native widgets before opening a PR.

Streamlit's DOM is not stable API, so copy values and structure, never class names.

## Dev workflow

- Use `python3`. Run `streamlit run example.py`.
- Smoke-test the demo with `streamlit.testing.v1.AppTest` and check it in the browser.
- Before a PR: demo tidy (no debug or comparison widgets), `WORKING_NOTES.md` updated, and no stray files.
