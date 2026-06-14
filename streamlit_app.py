import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from analysis_utils import (
    NUMERIC_COLUMNS,
    add_features,
    clean_data,
    descriptive_statistics,
    grouped_overview,
    load_data,
    missing_summary,
)


API_URL = os.getenv("API_URL", "").strip()

st.set_page_config(
    page_title="California Housing Analysis",
    layout="wide",
)


@st.cache_data
def get_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = load_data(include_new_records=True)
    cleaned = clean_data(raw)
    featured = add_features(cleaned)
    return raw, cleaned, featured


raw_df, clean_df, df = get_frames()

st.title("California Housing Analysis / Анализ жилья в Калифорнии")
st.caption("Ilya Lisitsyn")

st.header("Abstract / Аннотация")
st.write(
    "This project looks at housing districts in California and compares house value with income, "
    "location and several housing characteristics. I use the dataset to clean missing values, calculate "
    "basic statistics, build charts and check two hypotheses."
)
st.write(
    "В проекте я разбираю данные о районах Калифорнии и смотрю, как стоимость жилья связана "
    "с доходом, расположением и характеристиками района. Вклад: Ilya Lisitsyn - 100%."
)

st.header("Dataset Description / Описание датасета")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Raw rows", f"{len(raw_df):,}")
col2.metric("Clean rows", f"{len(clean_df):,}")
col3.metric("Columns", raw_df.shape[1])
col4.metric("Removed rows", f"{len(raw_df) - len(clean_df):,}")

st.write(
    "The dataset contains one row per district. The columns describe coordinates, housing age, "
    "rooms, bedrooms, population, households, median income, median house value and ocean proximity."
)
st.write(
    "В строках описаны районы: координаты, возраст жилья, комнаты, спальни, население, "
    "домохозяйства, медианный доход, медианная стоимость жилья и близость к океану."
)

with st.expander("Data quality / Качество данных", expanded=True):
    quality = missing_summary(raw_df)
    missing_only = quality[quality["missing_values"] > 0]
    st.dataframe(missing_only, width="stretch")
    st.write(
        "Only `total_bedrooms` has missing values: 207 rows. The other columns are complete, "
        "so I removed these rows before building statistics and charts."
    )
    st.write(
        "Пропуски есть только в `total_bedrooms`: 207 строк. Остальные колонки заполнены, "
        "поэтому строки с пропусками были удалены перед анализом."
    )

st.header("Filters / Фильтры")
categories = sorted(df["ocean_proximity"].unique())
selected_categories = st.multiselect(
    "Ocean proximity / Близость к океану",
    categories,
    default=categories,
)
income_range = st.slider(
    "Median income range / Диапазон медианного дохода",
    min_value=float(df["median_income"].min()),
    max_value=float(df["median_income"].max()),
    value=(float(df["median_income"].min()), float(df["median_income"].max())),
)
value_range = st.slider(
    "Median house value range / Диапазон стоимости жилья",
    min_value=float(df["median_house_value"].min()),
    max_value=float(df["median_house_value"].max()),
    value=(float(df["median_house_value"].min()), float(df["median_house_value"].max())),
    step=1000.0,
)

filtered = df[
    df["ocean_proximity"].isin(selected_categories)
    & df["median_income"].between(*income_range)
    & df["median_house_value"].between(*value_range)
]

if filtered.empty:
    st.warning(
        "No rows match the selected filters. Please widen the income or house value range."
    )
    st.write(
        "По выбранным фильтрам строк нет. Расширьте диапазон дохода или стоимости жилья."
    )
    st.stop()

st.header("Descriptive Statistics / Описательная статистика")
st.dataframe(descriptive_statistics(filtered), width="stretch")

st.header("Overview Plots / Основные графики")
left, right = st.columns(2)
left.plotly_chart(
    px.histogram(filtered, x="median_house_value", nbins=45, title="Median House Value Distribution"),
    width="stretch",
)
right.plotly_chart(
    px.scatter(
        filtered,
        x="median_income",
        y="median_house_value",
        color="ocean_proximity",
        opacity=0.55,
        title="Income vs House Value",
    ),
    width="stretch",
)

left, right = st.columns(2)
left.plotly_chart(
    px.box(filtered, x="ocean_proximity", y="median_house_value", title="House Value by Ocean Proximity"),
    width="stretch",
)
corr = filtered[NUMERIC_COLUMNS].corr(numeric_only=True)
if len(filtered) > 1:
    right.plotly_chart(
        px.imshow(corr, text_auto=".2f", aspect="auto", title="Correlation Heatmap"),
        width="stretch",
    )
else:
    right.info("Correlation heatmap needs at least two rows.")

st.header("Detailed Overview / Детальный обзор")
overview = grouped_overview(filtered)
st.dataframe(overview, width="stretch")

left, right = st.columns(2)
median_by_ocean = (
    filtered.groupby("ocean_proximity", as_index=False)["median_house_value"].median().sort_values("median_house_value")
)
left.plotly_chart(
    px.bar(median_by_ocean, x="ocean_proximity", y="median_house_value", title="Median Value by Ocean Proximity"),
    width="stretch",
)
comparison = filtered[filtered["ocean_proximity"].isin(["INLAND", "NEAR OCEAN", "<1H OCEAN"])]
right.plotly_chart(
    px.histogram(
        comparison,
        x="median_house_value",
        color="ocean_proximity",
        barmode="overlay",
        opacity=0.6,
        title="Distribution Comparison by Location",
    ),
    width="stretch",
)

st.header("Data Transformation / Преобразование данных")
st.write(
    "I added several columns that are easier to compare than raw totals: rooms per household, "
    "bedrooms per room, population per household and income group."
)
st.dataframe(
    filtered[
        [
            "total_rooms",
            "households",
            "rooms_per_household",
            "bedrooms_per_room",
            "population_per_household",
            "income_group",
        ]
    ].head(20),
    width="stretch",
)

st.header("Hypothesis Check / Проверка гипотез")
h1 = (
    filtered.groupby(["ocean_proximity", "income_group"], observed=True)["median_house_value"]
    .median()
    .reset_index()
)
st.plotly_chart(
    px.bar(
        h1,
        x="ocean_proximity",
        y="median_house_value",
        color="income_group",
        barmode="group",
        title="H1: Median Value by Income Group within Ocean Proximity",
    ),
    width="stretch",
)
st.write(
    "H1 result: the pattern is visible in most location groups. Districts with higher income usually "
    "have higher median house values. По графику видно, что в большинстве групп стоимость растет вместе с доходом."
)

high_income = filtered[filtered["income_group"].astype(str) == "high"]
h2 = high_income[high_income["ocean_proximity"].isin(["INLAND", "<1H OCEAN", "NEAR OCEAN", "NEAR BAY"])]
if h2.empty:
    st.info("H2 needs high-income rows in the selected filters.")
else:
    st.plotly_chart(
        px.box(
            h2,
            x="ocean_proximity",
            y="median_house_value",
            title="H2: High-Income Districts by Location",
        ),
        width="stretch",
    )
    st.write(
        "H2 result: among high-income districts, coastal groups are usually more expensive than INLAND. "
        "Среди районов с высоким доходом прибрежные категории в среднем дороже внутренних."
    )

st.header("FastAPI Backend / FastAPI часть")
if API_URL:
    with st.form("new_record_form"):
        st.subheader("Create a new housing record / Добавить запись")
        c1, c2, c3 = st.columns(3)
        record = {
            "longitude": c1.number_input("Longitude", value=-118.25),
            "latitude": c2.number_input("Latitude", value=34.05),
            "housing_median_age": c3.number_input("Housing median age", min_value=0.0, value=30.0),
            "total_rooms": c1.number_input("Total rooms", min_value=1.0, value=2500.0),
            "total_bedrooms": c2.number_input("Total bedrooms", min_value=1.0, value=500.0),
            "population": c3.number_input("Population", min_value=1.0, value=1200.0),
            "households": c1.number_input("Households", min_value=1.0, value=450.0),
            "median_income": c2.number_input("Median income", min_value=0.1, value=4.5),
            "median_house_value": c3.number_input("Median house value", min_value=1.0, value=250000.0),
            "ocean_proximity": c1.selectbox("Ocean proximity", categories),
        }
        submitted = st.form_submit_button("Submit to FastAPI")
        if submitted:
            try:
                response = requests.post(f"{API_URL}/housing", json=record, timeout=5)
                if response.ok:
                    st.success("Record submitted. Refresh the page to include it in the analysis.")
                else:
                    st.error(f"API error: {response.status_code} - {response.text}")
            except requests.RequestException as exc:
                st.error(f"Could not reach API at {API_URL}: {exc}")
    st.caption(f"FastAPI URL: {API_URL}")
else:
    st.write(
        "The project also includes a FastAPI backend in `api.py`. It provides `GET /housing`, "
        "`POST /housing` and `GET /stats` endpoints."
    )
    st.write(
        "In this online Streamlit version, the analytical report works directly with the dataset. "
        "The API can be launched locally or deployed separately."
    )
    st.write(
        "В проекте также есть FastAPI backend в файле `api.py`. Онлайн-отчет работает напрямую "
        "с датасетом, а API можно запустить локально или развернуть отдельно."
    )
