"""Demo app: run with `streamlit run example_searchbox.py`."""

import pandas as pd
import streamlit as st

from streamlit_vanilla_components import st_live_searchbox

DATA_URL = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/refs/heads/master/csv/states.csv"


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


# Load and cache everything before the first search
places = load_places()


def search_places(term: str) -> list[str]:
    # Stand-in for SQL: WHERE name/country_name/type LIKE '%term%' ORDER BY population DESC LIMIT 300
    # Over-fetch candidates; the searchbox ranks them by match quality and trims to max_results
    mask = (
        places["name"].str.contains(term, case=False, regex=False)
        | places["country_name"].str.contains(term, case=False, regex=False)
        | places["type"].str.contains(term, case=False, regex=False)
    )
    return places.loc[mask, "label"].head(300).tolist()  # `places` is already sorted by population


st.title("Live searchbox")
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
