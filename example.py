"""Demo app: run with `streamlit run example.py`. Add a section here for each new component."""

import inspect
import textwrap
import time

import pandas as pd
import streamlit as st

from streamlit_vanilla_components import st_live_searchbox, stateful_button

DATA_URL = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/refs/heads/master/csv/states.csv"


def demo(fn):
    """Show a function's body as code, then run it, so the code shown is always the code that runs."""
    source = inspect.getsource(fn)
    body = source.split("\n", 2)[2]  # drop the @demo and def lines
    st.code(textwrap.dedent(body), language="python", wrap_lines=True)
    fn()
    return fn


@st.cache_data(show_spinner="Loading places...")
def load_places() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_URL, usecols=["name", "country_name", "type", "latitude", "longitude", "population"]
    )
    df["type"] = df["type"].fillna("")
    df["population"] = pd.to_numeric(df["population"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    # Most populous first, so every search returns results in that order
    df = df.sort_values("population", ascending=False, na_position="last", kind="stable")
    df["label"] = df["name"] + ", " + df["country_name"]
    return df.drop_duplicates("label").reset_index(drop=True)


def slow_job(name):
    time.sleep(3)
    st.session_state["job_result"] = f"{name} finished"


def quick():
    time.sleep(1)


def fail_job():
    time.sleep(1)
    raise RuntimeError("Callback went wrong")


def stateful_button_section():
    st.caption("A button that disables itself, shows a spinner in place of its icon, then a tick.")

    st.markdown("##### "+"`with` block")

    @demo
    def with_block():
        with stateful_button("Submit", type="primary", icon=":material/send:", key="submit") as clicked:
            if clicked:
                time.sleep(3)
                st.success("Saved!")

    st.markdown("##### "+"`on_click` callback")

    @demo
    def callback():
        stateful_button("Run slow job", icon="🚀", on_click=slow_job, args=("Job 1",), key="job")
        if "job_result" in st.session_state:
            st.write(st.session_state["job_result"])

    st.markdown("##### "+"Variants")

    @demo
    def variants():
        cols = st.columns(3)
        with cols[0]:
            stateful_button("Tertiary", type="tertiary", on_click=quick, key="t")
        with cols[1]:
            stateful_button("Icon right", icon=":material/arrow_forward:", icon_position="right", on_click=quick, key="r")
        with cols[2]:
            stateful_button("Disabled", disabled=True, key="d")

    st.markdown("##### "+"Errors re-enable the button")

    @demo
    def errors():
        stateful_button("Fail in callback", on_click=fail_job, key="fail_cb")


def searchbox_section():
    st.caption("Type to query a Python function live; the picked result stays in the box and is returned as a string.")
    places = load_places()  # load and cache everything before the first search

    def search_places(term: str) -> list[str]:
        # Stand-in for SQL: WHERE name/country_name/type LIKE '%term%' ORDER BY population DESC LIMIT 300
        # Over-fetch candidates; the searchbox ranks them by match quality and trims to max_results
        mask = (
            places["name"].str.contains(term, case=False, regex=False)
            | places["country_name"].str.contains(term, case=False, regex=False)
            | places["type"].str.contains(term, case=False, regex=False)
        )
        return places.loc[mask, "label"].head(300).tolist()  # `places` is already sorted by population

    @demo
    def searchbox_example():
        choice = st_live_searchbox(
            search_places,
            placeholder="Search state, region or country...",
            label="Search a place",
            key="place",
            min_chars=2,
            max_results=50,
            rank=True,
        )
        st.write("Selected:", choice)

        if choice:
            row = places[places["label"] == choice].iloc[0]
            # A single point makes st.map centre and zoom on it
            st.map(pd.DataFrame({"lat": [row["latitude"]], "lon": [row["longitude"]]}), zoom=6, size=300)

    @demo
    def label_example():
        st.caption(
            "Return `(value, label)` tuples: the box shows the long label, the function returns the short place_id."
        )

        def search_place_ids(term: str) -> list[tuple[str, str]]:
            # Stand-in for SQL that builds the label in the query:
            # SELECT place_id, place_id || ' · ' || name || ' · ' || country || ' · ' || population FROM places WHERE ...
            mask = places["name"].str.contains(term, case=False, regex=False)
            rows = places.loc[mask].head(50)
            return [
                (f"P{i:05d}", f"P{i:05d} · {r['name']} · {r['country_name']} · pop. {int(r['population']):,}")
                for i, r in rows.iterrows()
                if pd.notna(r["population"])
            ]

        def on_clear():
            st.toast("Search cleared")

        place_id = st_live_searchbox(
            search_place_ids,
            placeholder="Search by place name...",
            label="Select a place",
            key="place_id",
            on_clear=on_clear,
        )
        st.write("Returned place_id:", place_id)


st.title("Vanilla Streamlit components")
tab_button, tab_search = st.tabs(["Stateful button", "Live searchbox"], on_change="rerun")
if tab_button.open:
    stateful_button_section()
elif tab_search.open:
    searchbox_section()
