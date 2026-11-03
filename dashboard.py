
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID")
READ_API_KEY = os.getenv("THINGSPEAK_READ_API_KEY", "").strip()

st.set_page_config(
    page_title="IoT Cloud Monitoring",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ IoT Cloud Monitoring Dashboard")
st.write("Real-Time Temperature and Humidity Monitoring")

if not CHANNEL_ID:
    st.error("Channel ID is missing. Check your .env file.")
    st.stop()

st.sidebar.header("Dashboard Settings")
refresh_seconds = st.sidebar.selectbox(
    "Refresh interval",
    [15, 30, 60],
    index=1,
)

if st.sidebar.button("Refresh Now"):
    st.rerun()


@st.cache_data(ttl=15)
def fetch_data(channel_id, read_api_key):
    url = (
        f"https://api.thingspeak.com/channels/"
        f"{channel_id}/feeds.json"
    )

    params = {"results": 100}

    if read_api_key:
        params["api_key"] = read_api_key

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    result = response.json()
    feeds = result.get("feeds", [])

    if not feeds:
        return pd.DataFrame()

    df = pd.DataFrame(feeds)

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce",
    )

    df["field1"] = pd.to_numeric(
        df["field1"],
        errors="coerce",
    )

    df["field2"] = pd.to_numeric(
        df["field2"],
        errors="coerce",
    )

    df = df.rename(
        columns={
            "created_at": "Timestamp",
            "field1": "Temperature",
            "field2": "Humidity",
        }
    )

    df = df.dropna(
        subset=["Timestamp", "Temperature", "Humidity"]
    )

    return df


try:
    with st.spinner("Loading sensor data from ThingSpeak..."):
        df = fetch_data(CHANNEL_ID, READ_API_KEY)

except requests.RequestException as error:
    st.error(f"Unable to retrieve cloud data: {error}")
    st.stop()

except ValueError:
    st.error("ThingSpeak returned invalid data.")
    st.stop()

if df.empty:
    st.warning(
        "No sensor readings are available yet. "
        "Run app.py and check your ThingSpeak channel."
    )
    st.stop()

latest = df.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Latest Temperature",
    f"{latest['Temperature']:.2f} °C",
)

col2.metric(
    "Latest Humidity",
    f"{latest['Humidity']:.2f} %",
)

col3.metric(
    "Recorded Readings",
    len(df),
)

st.subheader("📈 Temperature History")

temperature_chart = px.line(
    df,
    x="Timestamp",
    y="Temperature",
    markers=True,
    title="Temperature Over Time",
)

st.plotly_chart(
    temperature_chart,
    use_container_width=True,
)

st.subheader("💧 Humidity History")

humidity_chart = px.line(
    df,
    x="Timestamp",
    y="Humidity",
    markers=True,
    title="Humidity Over Time",
)

st.plotly_chart(
    humidity_chart,
    use_container_width=True,
)

st.subheader("📋 Recent Sensor Readings")

st.dataframe(
    df[["Timestamp", "Temperature", "Humidity"]]
    .sort_values("Timestamp", ascending=False)
    .head(20),
    use_container_width=True,
)

st.caption(
    f"Data source: ThingSpeak Channel {CHANNEL_ID}"
)

st.info(
    f"This dashboard refreshes every {refresh_seconds} seconds. "
    "Refresh the browser to fetch the latest readings."
)

st.caption(
    "Note: The displayed measurements are simulated until "
    "physical sensors are connected."
)
