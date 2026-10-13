"""Demo app: run with `streamlit run example.py`."""

import inspect
import textwrap
import time

import streamlit as st

from streamlit_vanilla_components import stateful_button


def demo(fn):
    """Show a function's body as code, then run it, so the code shown is always the code that runs."""
    source = inspect.getsource(fn)
    body = source.split("\n", 2)[2]  # drop the @demo and def lines
    st.code(textwrap.dedent(body), language="python", wrap_lines=True)
    fn()
    st.divider()
    return fn


st.title("Stateful button")
st.caption("A button that disables itself, shows a spinner in place of its icon, then a tick.")


st.subheader("`with` block")


@demo
def with_block():
    with stateful_button("Submit", type="primary", icon=":material/send:", key="submit") as clicked:
        if clicked:
            time.sleep(3)
            st.success("Saved!")


st.subheader("`on_click` callback")


def slow_job(name):
    time.sleep(3)
    st.session_state["job_result"] = f"{name} finished"


@demo
def callback():
    stateful_button("Run slow job", icon="🚀", on_click=slow_job, args=("Job 1",), key="job")
    if "job_result" in st.session_state:
        st.write(st.session_state["job_result"])


st.subheader("Progress ring")


@demo
def progress_ring():
    with stateful_button("Import", progress=True, icon=":material/upload:", key="import") as btn:
        if btn:
            for step in (25, 50, 75, 100):
                time.sleep(1)
                btn.update(step)
            st.success("Imported!")


st.subheader("Variants")


def quick():
    time.sleep(1)


@demo
def variants():
    cols = st.columns(3)
    with cols[0]:
        stateful_button("Tertiary", type="tertiary", on_click=quick, key="t")
    with cols[1]:
        stateful_button("Icon right", icon=":material/arrow_forward:", icon_position="right", on_click=quick, key="r")
    with cols[2]:
        stateful_button("Disabled", disabled=True, key="d")
    stateful_button("Stretch with shortcut", width="stretch", shortcut="Ctrl+K", help="Press Ctrl+K", on_click=quick, key="s")


st.subheader("Errors re-enable the button")


def fail_job():
    time.sleep(1)
    raise RuntimeError("Callback went wrong")


@demo
def errors():
    stateful_button("Fail in callback", on_click=fail_job, key="fail_cb")

    with stateful_button("Fail in with block", key="fail") as clicked:
        if clicked:
            time.sleep(1)
            raise RuntimeError("Something went wrong")
