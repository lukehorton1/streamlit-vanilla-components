export default function (component) {
  const { data, parentElement, setStateValue, setTriggerValue } = component

  const input = parentElement.querySelector("#input")
  const list = parentElement.querySelector("#list")
  const label = parentElement.querySelector("#label")
  const clear = parentElement.querySelector("#clear")

  // The script reruns after each query and this function runs again every time, so
  // what the user is doing (open/closed, pending debounce) lives on the element.
  const ui = (parentElement._searchbox ??= { open: false, index: 0, timer: null, picked: null })
  const options = data.options ?? []

  input.placeholder = data.placeholder ?? ""
  input.title = data.help ?? ""
  input.disabled = !!data.disabled
  parentElement.querySelector("#box").classList.toggle("disabled", input.disabled)
  label.hidden = !data.label
  label.textContent = data.label ?? ""
  label.className = data.labelVisibility === "visible" ? "" : "collapsed"
  if (!ui.initialized) {
    input.value = data.initial ?? ""
    ui.initialized = true
  }

  // Fresh options from Python: highlight the first. Open state is left alone, so a
  // rerun after a selection never pops the list back open.
  ui.index = 0

  function render() {
    clear.hidden = !input.value || input.disabled
    const show = ui.open && options.length > 0
    list.hidden = !show
    input.setAttribute("aria-expanded", String(show))
    list.textContent = ""
    options.forEach(({ label: text }, i) => {
      const li = document.createElement("li")
      const span = document.createElement("span")
      span.title = text
      const term = input.value.trim()
      const at = term ? text.toLowerCase().indexOf(term.toLowerCase()) : -1
      if (at < 0) {
        span.textContent = text
      } else {
        const strong = document.createElement("strong")
        strong.textContent = text.slice(at, at + term.length)
        span.append(text.slice(0, at), strong, text.slice(at + term.length))
      }
      li.appendChild(span)
      li.role = "option"
      li.className = i === ui.index ? "active" : ""
      li.onmouseenter = () => highlight(i, false)
      // mousedown fires before the input loses focus, so the click can't be lost
      li.onmousedown = (e) => {
        e.preventDefault()
        select(i)
      }
      list.appendChild(li)
    })
    if (show) list.children[ui.index]?.scrollIntoView({ block: "nearest" })
  }

  function highlight(i, scroll = true) {
    ui.index = i
    ;[...list.children].forEach((li, n) => li.classList.toggle("active", n === i))
    if (scroll) list.children[i]?.scrollIntoView({ block: "nearest" })
  }

  function close() {
    ui.open = false
    render()
    input.blur()
  }

  function select(i) {
    const option = options[i]
    if (option === undefined) return
    clearTimeout(ui.timer)
    setStateValue("selected", option.value)
    setTriggerValue("submitted", option.value)
    input.value = option.label
    ui.picked = option.label
    close()
  }

  // mousedown keeps focus in the input; the click clears text and the picked result
  clear.onmousedown = (e) => e.preventDefault()
  function cleared() {
    clearTimeout(ui.timer)
    ui.picked = null
    input.value = ""
    setStateValue("selected", "")
    setStateValue("query", "")
    setTriggerValue("cleared", true)
  }

  clear.onclick = () => {
    cleared()
    input.focus()
    render()
  }

  function changed() {
    ui.open = true
    const text = input.value
    if (!text) {
      cleared()
      render()
      return
    }
    clearTimeout(ui.timer)
    ui.timer = setTimeout(() => setStateValue("query", text), data.debounce ?? 250)
    render()
  }

  // Typing over a picked result replaces it instead of appending to it. Changing the
  // value inside beforeinput drops the pending keystroke, so apply the edit ourselves.
  input.onbeforeinput = (e) => {
    if (ui.picked === null || input.value !== ui.picked) return
    ui.picked = null
    e.preventDefault()
    input.value = e.inputType.startsWith("insert") ? (e.data ?? e.dataTransfer?.getData("text") ?? "") : ""
    changed()
  }
  input.oninput = changed
  input.onfocus = () => {
    ui.open = true
    render()
  }
  input.onblur = () => {
    ui.open = false
    render()
  }
  input.onkeydown = (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault()
      if (!options.length) return
      if (!ui.open) {
        ui.open = true
        render()
        return
      }
      const step = e.key === "ArrowDown" ? 1 : -1
      highlight((ui.index + step + options.length) % options.length)
    } else if (e.key === "Enter") {
      e.preventDefault()
      if (ui.open && options.length) select(ui.index)
      else input.blur()
    } else if (e.key === "Escape") {
      e.preventDefault()
      close()
    }
  }

  render()

  return () => {
    clear.onclick = clear.onmousedown = input.onbeforeinput = input.oninput = input.onfocus = input.onblur = input.onkeydown = null
  }
}
