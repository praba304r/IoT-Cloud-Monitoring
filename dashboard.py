import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import csv
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

# Load environment variables
load_dotenv()

# Shared control file used by app.py and dashboard.py
CONTROL_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "monitoring_control.txt",
)

CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID")
READ_API_KEY = os.getenv("THINGSPEAK_READ_API_KEY", "").strip()

# Configure dashboard
st.set_page_config(
    page_title="IoT Cloud Monitoring",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ IoT Cloud Monitoring Dashboard")
st.write("Real-Time Temperature and Humidity Monitoring")


# Read monitoring status
def get_monitoring_status():
    if not os.path.exists(CONTROL_FILE):
        return "running"

    try:
        with open(CONTROL_FILE, "r") as file:
            status = file.read().strip().lower()

        return status if status in ["running", "stopped"] else "running"

    except OSError:
        return "running"


# Update monitoring status
def set_monitoring_status(status):
    with open(CONTROL_FILE, "w") as file:
        file.write(status)


# Sidebar settings
st.sidebar.header("Monitoring Controls")

status = get_monitoring_status()

if status == "running":
    st.sidebar.success("Monitoring Status: RUNNING")
else:
    st.sidebar.warning("Monitoring Status: STOPPED")

col_start, col_stop = st.sidebar.columns(2)

with col_start:
    if st.button("▶ Start", use_container_width=True):
        set_monitoring_status("running")
        st.rerun()

with col_stop:
    if st.button("⏹ Stop", use_container_width=True):
        set_monitoring_status("stopped")
        st.rerun()

st.sidebar.divider()

st.sidebar.header("Dashboard Settings")

refresh_seconds = st.sidebar.selectbox(
    "Automatic Refresh Interval",
    [15, 30, 60],
    index=1,
)

# Automatically refresh dashboard
st_autorefresh(
    interval=refresh_seconds * 1000,
    limit=None,
    key="iot_dashboard_refresh",
)

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()


# Check ThingSpeak channel
if not CHANNEL_ID:
    st.error("Channel ID is missing. Check your .env file.")
    st.stop()


# Fetch cloud readings
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


# Retrieve data
try:
    with st.spinner("Loading sensor data from ThingSpeak..."):
        df = fetch_data(CHANNEL_ID, READ_API_KEY)

except requests.RequestException as error:
    st.error(f"Unable to retrieve cloud data: {error}")
    st.stop()

except ValueError:
    st.error("ThingSpeak returned invalid data.")
    st.stop()


# Display readings
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


# Temperature chart
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


# Humidity chart
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


# Recent readings
st.subheader("📋 Recent Sensor Readings")

st.dataframe(
    df[["Timestamp", "Temperature", "Humidity"]]
    .sort_values("Timestamp", ascending=False)
    .head(20),
    use_container_width=True,
)

# Dashboard information
st.caption(
    f"Data source: ThingSpeak Channel {CHANNEL_ID}"
)

st.info(
    f"Dashboard automatically refreshes every "
    f"{refresh_seconds} seconds."
)

st.caption(
    "Note: The displayed measurements are simulated "
    "until physical sensors are connected."
)
# ==========================================
# ALERT HISTORY
# ==========================================

ALERT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "alert_history.csv",
)

st.divider()

st.header("🚨 Alert History")

if os.path.exists(ALERT_FILE):

    try:
        alert_df = pd.read_csv(ALERT_FILE)

        if not alert_df.empty:
            st.metric("Total Alerts", len(alert_df))

            st.dataframe(
                alert_df.sort_values(
                    "Timestamp",
                    ascending=False,
                ),
                use_container_width=True,
            )

            csv_data = alert_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="📥 Download Alert History",
                data=csv_data,
                file_name="alert_history.csv",
                mime="text/csv",
            )

        else:
            st.info("No alerts recorded yet.")

    except (OSError, pd.errors.ParserError) as error:
        st.error(f"Unable to read alert history: {error}")

else:
    st.info(
        "No alert history available yet. "
        "Alerts will appear here when temperature exceeds 35°C "
        "or humidity exceeds 80%."
    )