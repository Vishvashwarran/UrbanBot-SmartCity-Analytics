import streamlit as st
import datetime
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from utils.db import get_connection
from utils.email_alert import send_email_alert
from utils.system_alerts import create_alert
from utils.ui_components import app_footer

st.title("🌫 Air Quality Prediction")

# LOAD MODEL 
model = load_model("models/aqi_lstm_model.h5", compile=False)
scaler = joblib.load("models/aqi_scaler.pkl")

# MONITORING STATIONS (INDIA)
stations = [
    "Anand Vihar - Delhi", "RK Puram - Delhi", "Punjabi Bagh - Delhi",
    "Bandra Kurla Complex - Mumbai", "Worli - Mumbai",
    "Alipore - Kolkata", "Ballygunge - Kolkata",
    "Velachery - Chennai", "Adyar - Chennai", "Perungudi - Chennai",
    "Anna Nagar - Chennai", "Manali - Chennai", "Tambaram - Chennai",
    "Hebbal - Bengaluru", "BTM Layout - Bengaluru",
    "Hyderabad Zoo Park", "Sanathnagar - Hyderabad",
    "Lucknow Central", "Kanpur IIT",
    "Jaipur Adarsh Nagar", "Ahmedabad Navrangpura",
    "Chandigarh Sector 22", "Bhopal TT Nagar", "Patna Rajbansi Nagar"
]

# INPUT SECTION 
st.subheader("📍 Monitoring Location")

col1, col2 = st.columns(2)

with col1:
    city = st.text_input("City", placeholder="Eg : Chennai")
    station = st.selectbox("Monitoring Station", stations)
    latitude = st.number_input("Latitude", format="%.6f")

with col2:
    longitude = st.number_input("Longitude", format="%.6f")

st.subheader("🧪 Pollutant Values")

col3, col4 = st.columns(2)

with col3:
    pm25 = st.number_input("PM2.5")
    pm10 = st.number_input("PM10")
    co = st.number_input("CO")

with col4:
    no2 = st.number_input("NO2")
    so2 = st.number_input("SO2")
    o3 = st.number_input("O3")

#  AQI CATEGORY FUNCTION 
def aqi_to_category(aqi):
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 200:
        return "Poor"
    elif aqi <= 300:
        return "Very Poor"
    else:
        return "Severe"

# BUTTON 
if st.button("Run AQI Analysis"):

    status_messages = []

    # 🔹 Create 72-hour sequence using same input
    input_data = np.array([[pm25, pm10, co, no2, so2, o3, 0]])
    sequence = np.repeat(input_data, 72, axis=0)

    scaled = scaler.transform(sequence)
    X = scaled[:, :-1].reshape(1, 72, 6)

    predicted_scaled = model.predict(X)

    aqi_index = 6
    aqi_min = scaler.data_min_[aqi_index]
    aqi_max = scaler.data_max_[aqi_index]

    predicted_aqi = predicted_scaled[0][0] * (aqi_max - aqi_min) + aqi_min
    category = aqi_to_category(predicted_aqi)

    status_messages.append(f"AQI: {int(predicted_aqi)} ({category})")

    # SAVE TO RDS 
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO air_quality_data (
        timestamp, city, monitoring_station,
        latitude, longitude,
        pm25, pm10, co, no2, so2, o3,
        aqi, aqi_category
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        datetime.datetime.now(),
        city,
        station,
        latitude,
        longitude,
        pm25, pm10, co, no2, so2, o3,
        int(predicted_aqi),
        category
    ))

    conn.commit()
    conn.close()

    status_messages.append("💾 Stored in RDS")

    # EMAIL ALERT 
    if category == "Severe":
        send_email_alert(
            subject="🚨 Severe Air Pollution Alert 🆘",
            message=f"""
Severe AQI detected!

📍 Location: {city} - {station}
AQI: {int(predicted_aqi)}
Take immediate action.
"""
        )

        create_alert(
            alert_type="pollution",
            location=f"{city} - {station}",
            severity="high",
            message=f"Severe AQI detected: {int(predicted_aqi)}",
            email_sent=True
        )

        status_messages.append("🚨 Alert email sent")

    # FINAL NOTIFICATION 
    if category == "Severe":
        st.error("🔔 " + " | ".join(status_messages))
    elif category in ["Poor", "Very Poor"]:
        st.warning("🔔 " + " | ".join(status_messages))
    else:
        st.success("🔔 " + " | ".join(status_messages))



app_footer()