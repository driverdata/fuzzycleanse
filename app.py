import pathlib
from io import BytesIO
from typing import Dict, List

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

st.set_page_config(page_title="FuzzyCleanse", layout="wide")
st.title("FuzzyCleanse - Dataset Cleanser")


def read_file(uploaded_file: BytesIO) -> pd.DataFrame:
    """Read uploaded file into a DataFrame supporting csv and Excel formats."""
    suffix = pathlib.Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    if suffix == ".xlsb":
        try:
            return pd.read_excel(uploaded_file, engine="pyxlsb")
        except ImportError:
            st.error("Reading .xlsb files requires the pyxlsb package. Please install it and retry.")
            st.stop()
    return pd.read_excel(uploaded_file)


def join_frames(frames: List[pd.DataFrame]) -> pd.DataFrame:
    """Join multiple DataFrames on common columns."""
    common = set(frames[0].columns).intersection(*(set(f.columns) for f in frames[1:]))
    if not common:
        st.error("Uploaded files do not share common fields and cannot be joined.")
        st.stop()
    result = frames[0]
    for f in frames[1:]:
        overlap = set(result.columns).intersection(set(f.columns)) - common
        if overlap:
            f = f.rename(columns={c: f"{c}__src" for c in overlap})
        result = result.merge(f, how="outer", on=sorted(common))
    st.caption(
        f"Joined on: {', '.join(sorted(common))} • Rows: {len(result):,} • Columns: {len(result.columns):,}"
    )
    return result


def _match_any(x, terms, threshold):
    x = str(x).lower()
    return any(fuzz.partial_ratio(x, t.lower()) >= threshold for t in terms)


def apply_filters(data: pd.DataFrame, filts: Dict[str, Dict[str, object]]) -> pd.DataFrame:
    result = data
    for col, f in filts.items():
        threshold = f.get("threshold", 80)
        if f["include_exact"]:
            result = result[result[col].astype(str).isin(f["include_exact"])]
        if f["include_fuzzy"]:
            result = result[
                result[col].apply(lambda x: _match_any(x, f["include_fuzzy"], threshold))
            ]
        if f["exclude_exact"]:
            result = result[~result[col].astype(str).isin(f["exclude_exact"])]
        if f["exclude_fuzzy"]:
            result = result[
                ~result[col].apply(lambda x: _match_any(x, f["exclude_fuzzy"], threshold))
            ]
    return result


def snapshot_state(fields: List[str]) -> Dict[str, object]:
    state: Dict[str, object] = {"fields_selection": fields}
    for field in fields:
        state[f"inc_exact_{field}"] = st.session_state.get(f"inc_exact_{field}", [])
        state[f"inc_fuzzy_{field}"] = st.session_state.get(f"inc_fuzzy_{field}", "")
        state[f"exc_exact_{field}"] = st.session_state.get(f"exc_exact_{field}", [])
        state[f"exc_fuzzy_{field}"] = st.session_state.get(f"exc_fuzzy_{field}", "")
        state[f"threshold_{field}"] = st.session_state.get(f"threshold_{field}", 80)
    return state


with st.sidebar:
    st.header("Settings")

    uploaded_files = st.file_uploader(
        "Upload CSV or Excel files",
        type=["csv", "xls", "xlsx", "xlsm", "xlsb"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.error("Please upload at least one file to continue.")
        st.stop()

    frames = [read_file(f) for f in uploaded_files]
    df = join_frames(frames)

    if "filter_state" not in st.session_state:
        st.session_state.filter_state = {}
    if "history" not in st.session_state:
        st.session_state.history = []

    for k, v in st.session_state.filter_state.items():
        st.session_state[k] = v

    fields = st.multiselect("Select field(s) to search", list(df.columns), key="fields_selection")
    if not fields:
        st.error("Please select at least one field to continue.")
        st.stop()

    filters: Dict[str, Dict[str, object]] = {}
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
        threshold = st.slider(
            f"Fuzzy match threshold for {field}", 0, 100, 80, key=f"threshold_{field}"
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
            "threshold": threshold,
        }
        if any([inc_exact, inc_fuzzy, exc_exact, exc_fuzzy]):
            has_keyword = True

    if not has_keyword:
        st.error("Please provide at least one keyword for filtering.")
        st.stop()

    current_state = snapshot_state(fields)
    if not st.session_state.history or st.session_state.history[-1] != current_state:
        st.session_state.history.append(current_state)
    st.session_state.filter_state = current_state

    if st.button("Undo last change"):
        if len(st.session_state.history) > 1:
            st.session_state.history.pop()
            st.session_state.filter_state = st.session_state.history[-1]
            st.experimental_rerun()


filter_state = st.session_state.get("filter_state", {})
fields = filter_state.get("fields_selection", [])
filters: Dict[str, Dict[str, object]] = {}
for field in fields:
    inc_fuzzy = [s.strip() for s in filter_state.get(f"inc_fuzzy_{field}", "").split(",") if s.strip()]
    exc_fuzzy = [s.strip() for s in filter_state.get(f"exc_fuzzy_{field}", "").split(",") if s.strip()]
    filters[field] = {
        "include_exact": filter_state.get(f"inc_exact_{field}", []),
        "include_fuzzy": inc_fuzzy,
        "exclude_exact": filter_state.get(f"exc_exact_{field}", []),
        "exclude_fuzzy": exc_fuzzy,
        "threshold": filter_state.get(f"threshold_{field}", 80),
    }

result = apply_filters(df, filters) if filters else df

st.subheader("Preview of results")
st.dataframe(result.head(100), use_container_width=True)

csv_data = result.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download cleansed data",
    data=csv_data,
    file_name="cleansed.csv",
    mime="text/csv",
)

excel_buf = BytesIO()
result.to_excel(excel_buf, index=False)
st.download_button(
    "Download as Excel",
    data=excel_buf.getvalue(),
    file_name="cleansed.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

