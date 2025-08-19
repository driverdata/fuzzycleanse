import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
from io import BytesIO
from typing import Dict, List
import pathlib

st.set_page_config(page_title="FuzzyCleanse", layout="wide")
st.title("FuzzyCleanse - Dataset Cleanser")


def read_file(uploaded_file: BytesIO) -> pd.DataFrame:
    """Read uploaded file into a DataFrame supporting csv and Excel formats."""
    suffix = pathlib.Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

# --- Step 1: Upload ---
uploaded_files = st.file_uploader(
    "Upload CSV or Excel files",
    type=["csv", "xls", "xlsx", "xlsm", "xlsb"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.error("Please upload at least one file to continue.")
    st.stop()

frames = [read_file(f) for f in uploaded_files]
df = pd.concat(frames, ignore_index=True)

# --- Step 2: Field Selection ---
fields = st.multiselect("Select field(s) to search", list(df.columns))
if not fields:
    st.error("Please select at least one field to continue.")
    st.stop()

# --- Step 3: Keyword Search ---
filters: Dict[str, Dict[str, List[str]]] = {}
has_keyword = False

for field in fields:
    st.subheader(f"Filters for `{field}`")
    values = sorted(df[field].dropna().astype(str).unique())
    inc_exact = st.multiselect(
        f"Exact values to include from {field}", values, key=f"inc_exact_{field}"
    )
    inc_fuzzy_raw = st.text_input(
        f"Fuzzy keywords to include in {field} (comma separated)",
        key=f"inc_fuzzy_{field}",
    )
    exc_exact = st.multiselect(
        f"Exact values to exclude from {field}", values, key=f"exc_exact_{field}"
    )
    exc_fuzzy_raw = st.text_input(
        f"Fuzzy keywords to exclude from {field} (comma separated)",
        key=f"exc_fuzzy_{field}",
    )

    inc_fuzzy = [s.strip() for s in inc_fuzzy_raw.split(",") if s.strip()]
    exc_fuzzy = [s.strip() for s in exc_fuzzy_raw.split(",") if s.strip()]

    if inc_fuzzy:
        tags = "".join(
            f"<span style='background-color:#90EE90;padding:2px 6px;border-radius:4px;margin-right:4px;'>{t}</span>"
            for t in inc_fuzzy
        )
        st.markdown(tags, unsafe_allow_html=True)
    if exc_fuzzy:
        tags = "".join(
            f"<span style='background-color:#FF7F7F;padding:2px 6px;border-radius:4px;margin-right:4px;'>{t}</span>"
            for t in exc_fuzzy
        )
        st.markdown(tags, unsafe_allow_html=True)

    filters[field] = {
        "include_exact": inc_exact,
        "include_fuzzy": inc_fuzzy,
        "exclude_exact": exc_exact,
        "exclude_fuzzy": exc_fuzzy,
    }
    if any([inc_exact, inc_fuzzy, exc_exact, exc_fuzzy]):
        has_keyword = True

if not has_keyword:
    st.error("Please provide at least one keyword for filtering.")
    st.stop()

# Function to apply filters

def apply_filters(data: pd.DataFrame, filts: Dict[str, Dict[str, List[str]]]) -> pd.DataFrame:
    result = data
    for col, f in filts.items():
        if f["include_exact"]:
            result = result[result[col].astype(str).isin(f["include_exact"])]
        if f["include_fuzzy"]:
            result = result[
                result[col]
                .astype(str)
                .apply(lambda x: any(fuzz.partial_ratio(x, term) >= 80 for term in f["include_fuzzy"]))
            ]
        if f["exclude_exact"]:
            result = result[~result[col].astype(str).isin(f["exclude_exact"])]
        if f["exclude_fuzzy"]:
            result = result[
                ~result[col]
                .astype(str)
                .apply(lambda x: any(fuzz.partial_ratio(x, term) >= 80 for term in f["exclude_fuzzy"]))
            ]
    return result

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "result" not in st.session_state:
    st.session_state.result = df.copy()

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Apply search"):
        st.session_state.history.append(filters)
        st.session_state.result = apply_filters(df, filters)
with col2:
    if st.button("Undo last change"):
        if st.session_state.history:
            st.session_state.history.pop()
            previous = st.session_state.history[-1] if st.session_state.history else {}
            st.session_state.result = apply_filters(df, previous) if previous else df.copy()

# --- Step 4: Final Preview ---
st.subheader("Preview of results")
st.dataframe(st.session_state.result.head(100))

# --- Step 5: Download ---
csv_data = st.session_state.result.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download cleansed data",
    data=csv_data,
    file_name="cleansed.csv",
    mime="text/csv",
)
