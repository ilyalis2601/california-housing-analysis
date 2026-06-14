from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "housing.csv"
NEW_RECORDS_PATH = BASE_DIR / "data" / "new_housing_records.csv"

NUMERIC_COLUMNS = [
    "longitude",
    "latitude",
    "housing_median_age",
    "total_rooms",
    "total_bedrooms",
    "population",
    "households",
    "median_income",
    "median_house_value",
]

ANALYSIS_COLUMNS = [
    "housing_median_age",
    "total_rooms",
    "total_bedrooms",
    "population",
    "households",
    "median_income",
    "median_house_value",
]

OCEAN_ORDER = ["INLAND", "<1H OCEAN", "NEAR BAY", "NEAR OCEAN", "ISLAND"]


def load_data(include_new_records: bool = True) -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    if include_new_records and NEW_RECORDS_PATH.exists():
        new_df = pd.read_csv(NEW_RECORDS_PATH)
        df = pd.concat([df, new_df], ignore_index=True)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned = cleaned.dropna(subset=NUMERIC_COLUMNS + ["ocean_proximity"]).copy()
    cleaned["ocean_proximity"] = cleaned["ocean_proximity"].astype(str)
    return cleaned


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    featured = df.copy()
    featured["rooms_per_household"] = featured["total_rooms"] / featured["households"]
    featured["bedrooms_per_room"] = featured["total_bedrooms"] / featured["total_rooms"]
    featured["population_per_household"] = featured["population"] / featured["households"]
    featured["income_group"] = pd.cut(
        featured["median_income"],
        bins=[0, 2.5, 5.0, np.inf],
        labels=["low", "medium", "high"],
        include_lowest=True,
    )
    return featured


def prepare_data(include_new_records: bool = True) -> pd.DataFrame:
    return add_features(clean_data(load_data(include_new_records=include_new_records)))


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.isna()
        .sum()
        .rename("missing_values")
        .to_frame()
        .assign(missing_percent=lambda x: x["missing_values"] / len(df) * 100)
    )


def descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    return df[ANALYSIS_COLUMNS].agg(["mean", "median", "std"]).T.round(2)


def grouped_overview(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["ocean_proximity", "income_group"], observed=True)
        .agg(
            districts=("median_house_value", "size"),
            mean_value=("median_house_value", "mean"),
            median_value=("median_house_value", "median"),
            mean_income=("median_income", "mean"),
            rooms_per_household=("rooms_per_household", "mean"),
        )
        .reset_index()
        .round(2)
    )


def save_new_record(record: dict) -> None:
    row = pd.DataFrame([record])
    if NEW_RECORDS_PATH.exists():
        row.to_csv(NEW_RECORDS_PATH, mode="a", header=False, index=False)
    else:
        row.to_csv(NEW_RECORDS_PATH, index=False)
