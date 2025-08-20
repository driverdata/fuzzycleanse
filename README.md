# FuzzyCleanse

FuzzyCleanse is a Streamlit application for uploading, joining, searching, and cleansing datasets using exact or fuzzy keyword matching.

## Features
- Upload multiple CSV or Excel files and automatically join them on shared fields.
- Include or exclude values using exact matching or fuzzy keywords powered by [rapidfuzz](https://github.com/maxbachmann/RapidFuzz).
- Adjust per-field fuzzy match thresholds for finer control.
- Preview the cleansed dataset and download the results as CSV or Excel.
- Supports `.xlsb` files when `pyxlsb` is installed.

## Getting Started
1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run app.py
   ```
3. Follow the on‑screen instructions to upload data, configure filters, and download the cleansed dataset.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
