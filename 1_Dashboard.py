import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from utils.db import execute_query
from utils.ui_components import app_footer

st.set_page_config(page_title="Smart City Analytics Dashboard", layout="wide")

st.title("📊 Smart City Analytics Dashboard")
st.caption("Real-time Urban Intelligence for Data-Driven City Governance")

st.markdown("""
### 🧠 Command Center Overview
This dashboard provides real-time monitoring of:

- Traffic congestion
- Air quality levels
- Road accidents
- Crowd density
- Infrastructure issues
- Citizen complaints

Enabling faster, data-driven urban governance.
""")

# SIDEBAR FILTERS 

st.sidebar.header("🎛 Dashboard Filters")

city_list = execute_query("SELECT DISTINCT city FROM traffic_data")
cities = ["All"] + [c["city"] for c in city_list if c["city"]]

selected_city = st.sidebar.selectbox("Select City", cities)

auto_refresh = st.sidebar.toggle("🔄 Auto Refresh")

refresh_rate = st.sidebar.selectbox(
    "Refresh Interval",
    ["15 sec", "30 sec", "60 sec"],
    index=1
)

refresh_seconds = int(refresh_rate.split()[0])

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="dashboard_refresh")

city_condition = ""

if selected_city != "All":
    city_condition = f" AND city = '{selected_city}' "

# KPI QUERIES 

traffic = execute_query(f"""
SELECT COUNT(*) AS count
FROM traffic_data
WHERE congestion_level='high' {city_condition}
""")

aqi = execute_query(f"""
SELECT aqi, aqi_category
FROM air_quality_data
WHERE 1=1 {city_condition}
ORDER BY timestamp DESC
LIMIT 1
""")

accidents = execute_query("""
SELECT COUNT(*) AS count
FROM accident_events
WHERE DATE(detected_at)=CURDATE()
""")

crowd = execute_query(f"""
SELECT COUNT(*) AS count
FROM crowd_density_data
WHERE density_level IN ('high','extreme') {city_condition}
""")

potholes = execute_query("""
SELECT COUNT(*) AS count
FROM road_infra_annotations
WHERE object_class='pothole'
""")

infra = execute_query(f"""
SELECT COUNT(*) AS count
FROM road_infra_images
WHERE road_type='street_infra' {city_condition}
""")

complaints = execute_query(f"""
SELECT COUNT(*) AS count
FROM complaint_nlp_analysis
WHERE sentiment = 'negative' {city_condition}
""")

st.markdown("### 🚨 Key Urban Risk Indicators")
# KPI DISPLAY 

col1, col2, col3, col4 = st.columns(4)
col5, col6, col7 = st.columns(3)

col1.metric("🚦 High Traffic Zones", traffic[0]["count"])
col2.metric("🌫 Latest AQI", aqi[0]["aqi"] if aqi else "N/A")
col3.metric("🚑 Accidents Today", accidents[0]["count"])
col4.metric("🧍 High Crowd Locations", crowd[0]["count"])

col5.metric("🛣 Potholes Detected", potholes[0]["count"])
col6.metric("💡 Streetlight Issues", infra[0]["count"])
col7.metric("🧾 Negative Complaints", complaints[0]["count"])

st.divider()

st.markdown("### 📊 Urban Analytics")
# CHARTS 

col1, col2 = st.columns(2)

# 🚦 TRAFFIC
traffic_chart = execute_query(f"""
SELECT city, COUNT(*) AS high_congestion_count
FROM traffic_data
WHERE congestion_level='high' {city_condition}
GROUP BY city
""")

df = pd.DataFrame(traffic_chart)

if not df.empty:
    fig = px.bar(df, x="city", y="high_congestion_count", title="🚦 High Traffic Zones")
    col1.plotly_chart(fig, use_container_width=True)

# 🌫 AQI TREND
aqi_chart = execute_query(f"""
SELECT timestamp, aqi
FROM air_quality_data
WHERE 1=1 {city_condition}
ORDER BY timestamp DESC
LIMIT 50
""")

df = pd.DataFrame(aqi_chart)

if not df.empty:
    fig = px.line(df, x="timestamp", y="aqi", title="🌫 AQI Trend")
    col2.plotly_chart(fig, use_container_width=True)

# 🚑 ACCIDENT SEVERITY
accident_chart = execute_query("""
SELECT severity, COUNT(*) AS total
FROM accident_events
GROUP BY severity
""")

df = pd.DataFrame(accident_chart)

if not df.empty:
    fig = px.pie(df, names="severity", values="total", title="🚑 Accident Severity")
    st.plotly_chart(fig, use_container_width=True)

# 🧍 CROWD HOTSPOTS
crowd_chart = execute_query(f"""
SELECT location, estimated_count
FROM crowd_density_data
WHERE 1=1 {city_condition}
ORDER BY estimated_count DESC
LIMIT 10
""")

df = pd.DataFrame(crowd_chart)

if not df.empty:
    fig = px.bar(df, x="location", y="estimated_count", title="🧍 Crowd Hotspots")
    st.plotly_chart(fig, use_container_width=True)

# 🧾 COMPLAINTS
complaint_chart = execute_query(f"""
SELECT category, COUNT(*) AS total
FROM citizen_complaints
WHERE 1=1 {city_condition}
GROUP BY category
""")

df = pd.DataFrame(complaint_chart)

if not df.empty:
    fig = px.bar(df, x="category", y="total", title="🧾 Complaints by Category")
    st.plotly_chart(fig, use_container_width=True)

# 💡 INFRASTRUCTURE
infra_chart = execute_query(f"""
SELECT city, COUNT(*) AS issues
FROM road_infra_images
WHERE road_type='street_infra' {city_condition}
GROUP BY city
""")

df = pd.DataFrame(infra_chart)

if not df.empty:
    fig = px.bar(df, x="city", y="issues", title="💡 Infrastructure Issues")
    st.plotly_chart(fig, use_container_width=True)

#  System Alerts
st.divider()
st.subheader("🚨 Recent System Alerts")

alerts = execute_query("""
SELECT alert_type, location, severity, generated_at, resolved
FROM system_alerts
ORDER BY generated_at DESC
LIMIT 10
""")

df_alerts = pd.DataFrame(alerts)

if not df_alerts.empty:
    st.dataframe(df_alerts, use_container_width=True)
else:
    st.info("No recent alerts.")


app_footer()
