const MATERIAL = /^:material\/([a-z0-9_]+):$/

// Maps the key names Streamlit documents for `shortcut` to KeyboardEvent.key values
const KEY_NAMES = {
  esc: "Escape", space: " ", up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight",
  pageup: "PageUp", pagedown: "PageDown", enter: "Enter", tab: "Tab",
  backspace: "Backspace", delete: "Delete", home: "Home", end: "End",
}

// "Cmd+Shift+O" -> a function that tests a KeyboardEvent
function parseShortcut(text) {
  const parts = text.split("+").map((p) => p.trim().toLowerCase())
  const key = parts.pop()
  const want = {
    mod: parts.some((p) => ["ctrl", "cmd", "meta", "mod"].includes(p)),
    alt: parts.some((p) => ["alt", "option"].includes(p)),
    shift: parts.includes("shift"),
  }
  const expected = KEY_NAMES[key] ?? key
  return (e) =>
    e.key.toLowerCase() === expected.toLowerCase() &&
    (e.ctrlKey || e.metaKey) === want.mod &&
    e.altKey === want.alt &&
    e.shiftKey === want.shift
}

function renderIcon(el, icon, busy, done) {
  el.className = "icon"
  el.textContent = ""
  if (busy) {
    el.className = "icon spinner"
  } else if (done) {
    el.className = "icon material-symbols"
    el.textContent = "check"
  } else if (icon) {
    const match = MATERIAL.exec(icon)
    el.textContent = match ? match[1] : icon
    if (match) el.className = "icon material-symbols"
  }
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component

  const btn = parentElement.querySelector("#btn")
  const icon = parentElement.querySelector("#icon")
  const label = parentElement.querySelector("#label")

  btn.dataset.type = data.type
  btn.dataset.width = data.width === "stretch" ? "stretch" : "content"
  btn.dataset.iconPosition = data.iconPosition
  btn.dataset.wrap = String(data.wrap !== false)
  btn.style.width = typeof data.width === "number" ? `${data.width}px` : ""
  btn.title = [data.help, data.shortcut && `(${data.shortcut})`].filter(Boolean).join(" ")
  label.textContent = data.label
  renderIcon(icon, data.icon, false, data.done)
  btn.disabled = data.disabled || data.done

  // After a successful run, show a tick for a moment, then restore the original icon
  const timer = data.done
    ? setTimeout(() => {
        renderIcon(icon, data.icon, false, false)
        btn.disabled = data.disabled
      }, 1500)
    : null

  // Disable straight away in the browser, so a second click can't happen
  // while Python is still working. Python re-renders the button when it's done.
  function click() {
    if (btn.disabled) return
    btn.disabled = true
    renderIcon(icon, data.icon, true)
    setTriggerValue("clicked", true)
  }
  btn.onclick = click

  let onKey = null
  if (data.shortcut) {
    const matches = parseShortcut(data.shortcut)
    onKey = (e) => {
      if (matches(e)) {
        e.preventDefault()
        click()
      }
    }
    document.addEventListener("keydown", onKey)
  }

  return () => {
    clearTimeout(timer)
    onKey && document.removeEventListener("keydown", onKey)
  }
}
