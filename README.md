# Speed vs. Sense: TfL Cycle Hire Route-Choice Analysis

This repository contains the code and notebooks used for the project/paper **“Speed vs. Sense: The Hidden Logic of Cyclist Routes”** ([1c_paper_andrii_kolisnyk.pdf](1c_paper_andrii_kolisnyk.pdf)).

At a high level, it:
- Takes **TfL Cycle Hire** trip records (two 2-week windows: winter vs. summer).
- Converts docking-station identifiers to **lat/long coordinates** using the live station feed.
- Enriches trips with **TfL Journey Planner API** estimates for:
	- theoretical cycling time (fastest route)
	- public-transport time (alternative)
- Builds a **logistic regression** model to explore which contextual factors are associated with choosing the **fastest** vs. **slower / “scenic/ideal”** route.

## What the repo is (and isn’t)

- This is primarily an **exploratory, reproducible research pipeline**.
- “Fastest route vs. scenic route” is an **operational definition** derived from time deltas: trips within **+10%** of the API’s theoretical cycling duration are treated as “fastest-route” choices.
- Because the TfL Journey Planner API does not support historical queries beyond a short window, the notebook maps each historical trip date to the **nearest upcoming date with the same weekday** before calling the API.

## Data sources

- TfL Cycling Data Portal: trip extracts (stored under [data/raw](data/raw))
	- January (winter): [data/raw/cycling_jan15-31.csv](data/raw/cycling_jan15-31.csv)
	- July (summer): [data/raw/cycling_jul15-31.csv](data/raw/cycling_jul15-31.csv)
- Cycle hire station feed (XML): [data/raw/livecyclehireupdates.xml](data/raw/livecyclehireupdates.xml)
- TfL Journey Planner API (used during enrichment; see [utils/tfl_api.py](utils/tfl_api.py))

## Repository layout

```
tfl-analysis/
	1c_paper_andrii_kolisnyk.pdf
	notebooks/
		1_bike_data_extraction.ipynb
		2_cyclists_efficiency_modeling.ipynb
	utils/
		tfl_api.py
	data/
		raw/                         # input CSVs + station XML
		processed/
			cleaned_data_sample10.csv  # stratified 10% sample (from notebook 1)
			api_processed/
				sample_10.parquet        # API-enriched dataset (from utils/tfl_api.py)
		result/                      # optional exports (see notebook 2)
	logs/
		tfl_api.log                  # API call logs (when running utils/tfl_api.py)
```

## Quick start

### 1) Create env + install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Build the cleaned stratified sample (Notebook 1)

Open and run: [notebooks/1_bike_data_extraction.ipynb](notebooks/1_bike_data_extraction.ipynb)

This notebook:
- loads the two raw CSV extracts
- removes trips with the same start/end station
- creates API-compatible date/time fields
- joins station coordinates from the XML feed
- writes a stratified sample to: [data/processed/cleaned_data_sample10.csv](data/processed/cleaned_data_sample10.csv)

### 3) Enrich the sample using TfL Journey Planner API

Run the API script:

```bash
python utils/tfl_api.py
```

It reads [data/processed/cleaned_data_sample10.csv](data/processed/cleaned_data_sample10.csv) and writes:
- [data/processed/api_processed/sample_10.parquet](data/processed/api_processed/sample_10.parquet)

Notes:
- The API has rate limits (the code includes sleeps/retries and logs to [logs/tfl_api.log](logs/tfl_api.log)).
- The script currently embeds an API key; if you fork this, you should replace it with your own key.

### 4) Fit the logistic regression + generate diagnostics (Notebook 2)

Open and run: [notebooks/2_cyclists_efficiency_modeling.ipynb](notebooks/2_cyclists_efficiency_modeling.ipynb)

This notebook:
- loads the API-enriched parquet
- engineers variables used in the paper (time-of-day class, distance class, deltas)
- fits a logistic regression with treatment-coded categorical variables
- produces odds ratios + residual plots
- includes optional exports to [data/result](data/result)

## Model definition (as implemented)

- Dependent variable: `cyclist_class` (binary)
	- `1` if `(real_duration - cycling_api_duration) / real_duration < 0.1`
	- else `0`
- Key predictor: `cycling_public_delta_pct` (cycling vs public transport)
- Controls (categorical): `type_of_day`, `time_class`, `season`, `distance_class`, `bike_model`

## Paper

For methodology rationale, assumptions, limitations, and findings, see:
- [1c_paper_andrii_kolisnyk.pdf](1c_paper_andrii_kolisnyk.pdf)

## Support

If this repository or paper helped you, please consider **starring the repo**. It helps others find it and supports continued work.

## Acknowledgements

Powered by **TfL Open Data**.

