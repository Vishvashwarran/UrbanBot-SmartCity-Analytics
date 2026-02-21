import streamlit as st
import datetime
import joblib
import numpy as np
import time
import cv2
import tempfile
import os
from PIL import Image
from tensorflow.keras.models import load_model
from ultralytics import YOLO
from utils.db import get_connection
from utils.email_alert import send_email_alert
from utils.s3_upload import upload_to_s3
from utils.system_alerts import create_alert
from utils.ui_components import app_footer

st.title("🚦 Traffic Analysis")

# LOAD MODELS 
@st.cache_resource
def load_models():
    yolo = YOLO("models/traffic_yolo_best.pt")
    lstm = load_model("models/traffic_lstm.h5", compile=False)
    scaler = joblib.load("models/traffic_scaler.pkl")
    return yolo, lstm, scaler

yolo_model, lstm_model, scaler = load_models()

current_hour = datetime.datetime.now().hour
is_peak_hour = current_hour in [8, 9, 18, 19]

left, right = st.columns(2)

# INPUTS 
with left:

    st.subheader("📍 Enter Location Details")

    city = st.text_input("City", placeholder="Eg : Chennai")
    area = st.text_input("Area / Junction",placeholder="Eg : Anna Nagar")

    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Latitude", format="%.6f")
    with col2:
        longitude = st.number_input("Longitude", format="%.6f")

    lane_count = st.number_input("Lane Count", min_value=1, value=2)
    weather = st.selectbox("Weather", ["Clear", "Rain", "Fog", "Cloudy"])

    traffic_file = st.file_uploader(
        "Upload Traffic Image / Video",
        type=["jpg", "png", "mp4"]
    )

    run_btn = st.button("🚀 Run Traffic Analysis", use_container_width=True)


# 🚀 RUN BUTTON PROCESS

if run_btn:

    if area == "" or traffic_file is None:
        left.warning("Please provide Area and media")
        st.stop()

    vehicle_count = 0
    file_path = None
    status_messages = []

    vehicle_classes = ["car", "bus", "truck", "motorbike", "bicycle"]

    # IMAGE 
    if traffic_file.type.startswith("image"):

        image = Image.open(traffic_file)

        results = yolo_model(image, conf=0.05)

        plotted = results[0].plot()
        plotted = cv2.cvtColor(plotted, cv2.COLOR_BGR2RGB)

        right.image(plotted, use_container_width=True)

        boxes = results[0].boxes
        if boxes is not None and boxes.cls is not None:
            class_ids = boxes.cls.cpu().numpy()
            names = yolo_model.names

            vehicle_count = sum(
                1 for cid in class_ids if names[int(cid)] in vehicle_classes
            )

    # VIDEO 
    else:

        suffix = os.path.splitext(traffic_file.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(traffic_file.read())
            file_path = tmp.name

        cap = cv2.VideoCapture(file_path)

        frame_skip = 5
        frame_count = 0

        frame_placeholder = right.empty()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_skip != 0:
                continue

            results = yolo_model(frame, conf=0.05, imgsz=960, verbose=False)

            boxes = results[0].boxes

            detected_vehicles = 0

            if boxes is not None and boxes.cls is not None:
                class_ids = boxes.cls.cpu().numpy()
                names = yolo_model.names

                detected_vehicles = sum(
                    1 for cid in class_ids if names[int(cid)] in vehicle_classes
                )

                vehicle_count = max(vehicle_count, detected_vehicles)

            annotated_frame = results[0].plot()
            frame_placeholder.image(annotated_frame, channels="BGR")

        cap.release()

    status_messages.append(f"🚗 Vehicles: {vehicle_count}")

    # LSTM 
    sequence = np.array([vehicle_count] * 24).reshape(24, 1)
    scaled_sequence = scaler.transform(sequence)
    X_input = scaled_sequence.reshape(1, 24, 1)

    predicted_scaled = lstm_model.predict(X_input, verbose=0)
    predicted_value = scaler.inverse_transform(predicted_scaled)[0][0]

    if predicted_value < 5:
        congestion = "low"
        avg_speed = 50
    elif predicted_value < 10:
        congestion = "medium"
        avg_speed = 30
    else:
        congestion = "high"
        avg_speed = 15

    status_messages.append(f"📈 Next Hour: {int(predicted_value)} ({congestion})")

    # S3 UPLOAD 
    if file_path:
        unique_name = f"traffic/{city}_{int(time.time())}_{traffic_file.name}"
        image_url = upload_to_s3(file_path, unique_name)

        if image_url:
            status_messages.append("☁ Stored in S3")
        else:
            status_messages.append("❌ S3 failed")

    # SAVE TO RDS 
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO traffic_data (
        timestamp, city, area, latitude, longitude,
        vehicle_count, avg_speed_kmph,
        congestion_level, lane_count,
        weather_condition, is_peak_hour
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        datetime.datetime.now(),
        city,
        area,
        latitude,
        longitude,
        vehicle_count,
        avg_speed,
        congestion,
        lane_count,
        weather,
        is_peak_hour
    ))

    conn.commit()
    conn.close()

    status_messages.append("💾 Stored in RDS")

    # EMAIL ALERT 
    if vehicle_count > 10:

        email_subject = f"🚦 Traffic Alert – {area}, {city} 🆘"

        email_body = f"""
🚨 {congestion.upper()} congestion at {area}, {city} – {vehicle_count} vehicles detected.
📈 Next hour estimate: {int(predicted_value)} vehicles | 🤖 This is an AI automated system alert.
"""

        send_email_alert(
            subject=email_subject,
            message=email_body
        )

        create_alert(
            alert_type="traffic",
            location=f"{area}, {city}",
            severity="high",
            message=f"High traffic congestion detected with {vehicle_count} vehicles. Next hour prediction: {int(predicted_value)}",
            email_sent=True
        )

        status_messages.append("🚨 Alert email sent")

    # FINAL STATUS 
    msg = " | ".join(status_messages)

    if vehicle_count > 10:
        right.error("🔔 " + msg)
    elif vehicle_count > 5:
        right.warning("🔔 " + msg)
    else:
        right.success("🔔 " + msg)

    # CLEAN TEMP FILE 
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except:
            pass



app_footer()