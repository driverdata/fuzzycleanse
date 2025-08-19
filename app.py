import io
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz


def load_file(uploaded_file):
    """Load uploaded file into a DataFrame based on extension."""
    file_buffer = io.BytesIO(uploaded_file.getvalue())
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file_buffer)
    if name.endswith(".xlsb"):
        return pd.read_excel(file_buffer, engine="pyxlsb")
    if name.endswith((".xls", ".xlsx", ".xlsm", ".xlsb")):
        return pd.read_excel(file_buffer)
    raise ValueError("Unsupported file type")


st.title("FuzzyCleanse Data Cleaner")

uploaded_files = st.file_uploader(
    "Step 1 - Upload CSV or Excel files",
    accept_multiple_files=True,
    type=["csv", "xls", "xlsx", "xlsm", "xlsb"],
)

if not uploaded_files:
    st.error("Please upload at least one file to continue.")
    st.stop()

# Load all dataframes
try:
    dataframes = [load_file(f) for f in uploaded_files]
except Exception as exc:
    st.error(f"Error loading files: {exc}")
    st.stop()

all_columns = sorted({col for df in dataframes for col in df.columns})
selected_fields = st.multiselect("Step 2 - Select field(s) to search", all_columns)

if not selected_fields:
    st.error("Please select at least one field to search.")
    st.stop()

# Prepare session state for undo functionality
if "history" not in st.session_state:
    st.session_state.history = []
if "state" not in st.session_state:
    st.session_state.state = {}

include_terms = {}
exclude_terms = {}
include_types = {}
exclude_types = {}

for field in selected_fields:
    st.subheader(f"Field: {field}")
    col1, col2 = st.columns(2)
    with col1:
        include_type = st.radio(
            f"Include match type for '{field}'", ["Exact", "Fuzzy"],
            key=f"include_type_{field}", horizontal=True,
        )
        include_types[field] = include_type
        if include_type == "Exact":
            unique_vals = pd.concat([df[field].dropna().astype(str) for df in dataframes]).unique().tolist()
            include_vals = st.multiselect(
                f"Values to include in '{field}'", unique_vals, key=f"include_vals_{field}"
            )
        else:
            include_text = st.text_input(
                f"Comma-separated terms to include in '{field}'", key=f"include_text_{field}"
            )
            include_vals = [v.strip() for v in include_text.split(",") if v.strip()]
            if include_vals:
                st.markdown(
                    " ".join(
                        f"<span style='color: white;background-color: green;padding:2px 6px;border-radius:8px;'>{v}</span>"
                        for v in include_vals
                    ),
                    unsafe_allow_html=True,
                )
        include_terms[field] = include_vals
    with col2:
        exclude_type = st.radio(
            f"Exclude match type for '{field}'", ["Exact", "Fuzzy"],
            key=f"exclude_type_{field}", horizontal=True,
        )
        exclude_types[field] = exclude_type
        if exclude_type == "Exact":
            unique_vals = pd.concat([df[field].dropna().astype(str) for df in dataframes]).unique().tolist()
            exclude_vals = st.multiselect(
                f"Values to exclude in '{field}'", unique_vals, key=f"exclude_vals_{field}"
            )
        else:
            exclude_text = st.text_input(
                f"Comma-separated terms to exclude in '{field}'", key=f"exclude_text_{field}"
            )
            exclude_vals = [v.strip() for v in exclude_text.split(",") if v.strip()]
            if exclude_vals:
                st.markdown(
                    " ".join(
                        f"<span style='color: white;background-color: red;padding:2px 6px;border-radius:8px;'>{v}</span>"
                        for v in exclude_vals
                    ),
                    unsafe_allow_html=True,
                )
        exclude_terms[field] = exclude_vals

current_state = {
    "include": include_terms,
    "exclude": exclude_terms,
    "include_types": include_types,
    "exclude_types": exclude_types,
    "fields": selected_fields,
}

if current_state != st.session_state.state and not st.session_state.get("_undo", False):
    st.session_state.history.append(st.session_state.state)
    st.session_state.state = current_state

if st.button("Undo last keyword change") and st.session_state.history:
    prev = st.session_state.history.pop()
    st.session_state.state = prev
    st.session_state["_undo"] = True
    for field in selected_fields:
        st.session_state[f"include_type_{field}"] = prev["include_types"].get(field, "Exact")
        st.session_state[f"exclude_type_{field}"] = prev["exclude_types"].get(field, "Exact")
        if prev["include_types"].get(field) == "Exact":
            st.session_state[f"include_vals_{field}"] = prev["include"].get(field, [])
        else:
            st.session_state[f"include_text_{field}"] = ", ".join(prev["include"].get(field, []))
        if prev["exclude_types"].get(field) == "Exact":
            st.session_state[f"exclude_vals_{field}"] = prev["exclude"].get(field, [])
        else:
            st.session_state[f"exclude_text_{field}"] = ", ".join(prev["exclude"].get(field, []))
    st.experimental_rerun()

st.session_state["_undo"] = False

if not any(include_terms.values()) and not any(exclude_terms.values()):
    st.error("Please provide keywords to include or exclude.")
    st.stop()

# Apply filtering
filtered_frames = []
for df in dataframes:
    mask = pd.Series(True, index=df.index)
    for field in selected_fields:
        series = df[field].astype(str)
        inc_vals = include_terms.get(field, [])
        exc_vals = exclude_terms.get(field, [])
        if inc_vals:
            if include_types[field] == "Exact":
                mask &= series.isin(inc_vals)
            else:
                mask &= series.apply(
                    lambda x: any(fuzz.partial_ratio(term, x) >= 80 for term in inc_vals)
                )
        if exc_vals:
            if exclude_types[field] == "Exact":
                mask &= ~series.isin(exc_vals)
            else:
                mask &= series.apply(
                    lambda x: all(fuzz.partial_ratio(term, x) < 80 for term in exc_vals)
                )
    filtered_frames.append(df[mask])

result_df = pd.concat(filtered_frames, ignore_index=True)

st.subheader("Step 4 - Preview")
st.dataframe(result_df)

csv = result_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Step 5 - Download cleaned data",
    data=csv,
    file_name="cleaned_data.csv",
    mime="text/csv",
)
