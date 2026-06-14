from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from analysis_utils import (
    NUMERIC_COLUMNS,
    descriptive_statistics,
    grouped_overview,
    prepare_data,
    save_new_record,
)


app = FastAPI(
    title="California Housing Analysis API",
    description="REST API for the Pilot Python project based on the California housing dataset.",
    version="1.0.0",
)


class HousingRecord(BaseModel):
    longitude: float = Field(..., ge=-125, le=-113)
    latitude: float = Field(..., ge=32, le=43)
    housing_median_age: float = Field(..., ge=0)
    total_rooms: float = Field(..., gt=0)
    total_bedrooms: float = Field(..., gt=0)
    population: float = Field(..., gt=0)
    households: float = Field(..., gt=0)
    median_income: float = Field(..., gt=0)
    median_house_value: float = Field(..., gt=0)
    ocean_proximity: str


@app.get("/")
def root() -> dict:
    return {
        "project": "California Housing Analysis",
        "docs": "/docs",
        "endpoints": ["/housing", "/stats"],
    }


@app.get("/housing")
def get_housing(
    ocean_proximity: Optional[str] = Query(None, description="Filter by ocean proximity category"),
    min_income: Optional[float] = Query(None, ge=0, description="Minimum median income"),
    max_value: Optional[float] = Query(None, ge=0, description="Maximum median house value"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    df = prepare_data()
    if ocean_proximity:
        df = df[df["ocean_proximity"] == ocean_proximity]
    if min_income is not None:
        df = df[df["median_income"] >= min_income]
    if max_value is not None:
        df = df[df["median_house_value"] <= max_value]

    total = len(df)
    page = df.iloc[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": page.to_dict(orient="records"),
    }


@app.post("/housing", status_code=201)
def create_housing(record: HousingRecord) -> dict:
    data = record.model_dump()
    save_new_record(data)
    return {"message": "Record created", "record": data}


@app.get("/stats")
def get_stats() -> dict:
    df = prepare_data()
    stats = descriptive_statistics(df)
    overview = grouped_overview(df)
    correlations = df[NUMERIC_COLUMNS].corr(numeric_only=True)["median_house_value"].sort_values(ascending=False)
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "ocean_proximity_counts": df["ocean_proximity"].value_counts().to_dict(),
        "descriptive_statistics": stats.to_dict(orient="index"),
        "grouped_overview": overview.to_dict(orient="records"),
        "correlation_with_house_value": correlations.round(4).to_dict(),
    }
