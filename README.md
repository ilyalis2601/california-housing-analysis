# California Housing Analysis

Python Pilot project by Ilya Lisitsyn.

The project uses the California housing dataset. I analyze missing values, clean the data, calculate descriptive statistics, add a few new columns and compare house value by income and location.

## What is inside

- `notebooks/housing_analysis.ipynb` - the main notebook report with code, tables, charts and conclusions.
- `streamlit_app.py` - Streamlit page with the same analysis in web form.
- `app.py` - small Streamlit Cloud entry point.
- `api.py` - FastAPI app for getting filtered data and adding a new record.
- `analysis_utils.py` - shared functions for loading, cleaning and transforming the dataset.
- `data/housing.csv` - source dataset.
- `requirements.txt` - packages needed to run the project.

## How to run locally

Create a virtual environment with Python 3.13:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Start the API:

```powershell
.\.venv\Scripts\python -m uvicorn api:app --reload --port 8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Start Streamlit in another terminal:

```powershell
$env:API_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python -m streamlit run app.py
```

Streamlit page:

```text
http://127.0.0.1:8501
```

Open the notebook:

```powershell
.\.venv\Scripts\python -m jupyter notebook notebooks/housing_analysis.ipynb
```

## API

- `GET /housing` - returns dataset rows with filters and pagination.
- `POST /housing` - adds one new housing record.
- `GET /stats` - returns summary statistics for the cleaned dataset.

Example:

```text
http://127.0.0.1:8000/housing?ocean_proximity=INLAND&min_income=3&limit=5&offset=0
```

## Deployment note

For the public Streamlit link, upload the project to GitHub and deploy it on Streamlit Community Cloud:

- Repository: the GitHub repository with this project.
- Branch: `main`.
- Main file path: `app.py`.

The Streamlit report works online without starting FastAPI. The FastAPI code is still included in `api.py`.

If the API is also deployed, set the Streamlit environment variable `API_URL` to the public FastAPI URL.

For a public API version, the API can be deployed as a separate Render service:

- FastAPI: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Streamlit on Render: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

In Streamlit, set `API_URL` to the public FastAPI URL.
