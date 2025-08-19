# fuzzycleanse

A Streamlit application for uploading, joining, searching and cleansing datasets using exact or fuzzy keyword matching.

## Features
- Upload multiple CSV or Excel files and join them automatically on shared fields.
- Select fields to search.
- Include or exclude keywords with exact or fuzzy matching powered by [rapidfuzz](https://github.com/maxbachmann/RapidFuzz).
- Filters live in a scrollable sidebar and update results when you press Enter.
- Preview the cleansed dataset and download the results.

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```
3. Follow on‑screen instructions to upload data, configure filters and download the cleansed dataset.

## License
This project is licensed under the terms of the MIT license. See [LICENSE](LICENSE) for details.
