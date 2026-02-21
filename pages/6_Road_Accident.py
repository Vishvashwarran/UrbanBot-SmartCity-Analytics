import streamlit as st
import datetime
import uuid
import time
import os
import cv2
import tempfile
from PIL import Image
from ultralytics import YOLO
from utils.db import get_connection
from utils.s3_upload import upload_to_s3
from utils.email_alert import send_email_alert
from utils.system_alerts import create_alert
from utils.ui_components import app_footer

st.title("🚨 Road Accident Detection")

# LOAD MODEL 
@st.cache_resource
def load_model():
    return YOLO("models/accident_best.pt")

model = load_model()

# INPUT SECTION 
st.subheader("📍 Location Details")

city = st.text_input("City", placeholder="Eg : Chennai")

col1, col2 = st.columns(2)
with col1:
    latitude = st.number_input("Latitude", format="%.6f")
with col2:
    longitude = st.number_input("Longitude", format="%.6f")

accident_file = st.file_uploader(
    "Upload Accident Image / Video",
    type=["jpg", "png", "mp4"]
)

# RUN BUTTON 
if st.button("🚀 Run Detection"):

    if accident_file is None:
        st.warning("Please upload an image or video")
        st.stop()

    accident_id = str(uuid.uuid4())
    image_id = str(uuid.uuid4())

    vehicle_count = 0
    max_conf = 0
    severity = None
    accident_detected = False

# SEVERITY MAP 
    severity_map = {
        "no_accident": None,
        "minor_damage": "low",
        "moderate_damage": "medium",
        "severe_accident": "high",
        "total_loss": "high"
    }

    # IMAGE
    if accident_file.type.startswith("image"):

        image = Image.open(accident_file)

        results = model(image, conf=0.10, verbose=False)

        plotted = results[0].plot()
        plotted = cv2.cvtColor(plotted, cv2.COLOR_BGR2RGB)
        st.image(plotted, use_container_width=True)

        boxes = results[0].boxes

        names = model.names

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0])
                class_name = names[cls_id]

                mapped = severity_map.get(class_name)

                if mapped:
                    accident_detected = True

                if mapped == "high":
                    severity = "high"
                elif mapped == "medium" and severity != "high":
                    severity = "medium"
                elif mapped == "low" and severity not in ["high", "medium"]:
                    severity = "low"

                if class_name != "no_accident":
                    vehicle_count += 1
                max_conf = max(max_conf, float(box.conf[0]))

        temp_path = f"temp_{time.time()}.jpg"
        image.save(temp_path)

    # VIDEO  
    else:

        suffix = os.path.splitext(accident_file.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(accident_file.read())
            temp_path = tmp.name

        cap = cv2.VideoCapture(temp_path)

        frame_placeholder = st.empty()

        frame_vehicle_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, conf=0.60, verbose=False)

            boxes = results[0].boxes

            names = model.names

            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    class_name = names[cls_id]

                    mapped = severity_map.get(class_name)

                    if mapped:
                        accident_detected = True

                    if mapped == "high":
                        severity = "high"
                    elif mapped == "medium" and severity not in ["high"]:
                        severity = "medium"
                    elif mapped == "low" and severity not in ["high", "medium"]:
                        severity = "low"

                    if class_name != "no_accident":
                        frame_vehicle_count += 1
                    max_conf = max(max_conf, float(box.conf[0]))

            if boxes is not None and len(boxes) > 0:

                if boxes.conf is not None and boxes.conf.numel() > 0:
                    max_conf = max(max_conf, float(boxes.conf.max()))
                vehicle_count = max(vehicle_count, frame_vehicle_count)
                frame_vehicle_count = 0

            annotated_frame = results[0].plot()

            frame_placeholder.image(annotated_frame, channels="BGR")

        cap.release()

    if not accident_detected:
        severity = "none"
        vehicle_count = 0

    if severity == "high":
        response_time = 300
    elif severity == "medium":
        response_time = 600
    elif severity == "low":
        response_time = 900
    else:
        response_time = 0

    if severity != "none":
        # S3 UPLOAD 

        s3_key = f"accidents/{city}_{int(time.time())}_{accident_file.name}"
        image_url = upload_to_s3(temp_path, s3_key)

        # SAVE TO RDS 
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO road_infra_images (
                image_id, image_url, captured_at, city,
                latitude, longitude, resolution, annotated
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            image_id,
            image_url,
            datetime.datetime.now(),
            city,
            latitude,
            longitude,
            "N/A",
            True
        ))

        cursor.execute("""
            INSERT INTO accident_events (
                accident_id, detected_at, image_id,
                latitude, longitude, severity,
                vehicle_count, confidence_score,
                emergency_alert_sent, response_time_sec
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            accident_id,
            datetime.datetime.now(),
            image_id,
            latitude,
            longitude,
            severity,
            vehicle_count,
            max_conf,
            vehicle_count >= 1,
            response_time
        ))

        conn.commit()
        conn.close()

        # EMAIL ALERT 
        if vehicle_count >= 1:

            if severity == "high":
                subject = "🚨 CRITICAL: Major Road Accident Detected"
                action = "Immediate emergency response required."
            elif severity == "medium":
                subject = "⚠ Road Accident Detected – Quick Response Needed"
                action = "Dispatch traffic control and medical support.🚑"
            else:
                subject = "ℹ Minor Road Incident Detected"
                action = "⛑️Monitor the situation."

            send_email_alert(
                subject=subject,
                message=f"""
    SMART CITY – AI ACCIDENT ALERT 🆘

    City: {city}
    Coordinates: {latitude}, {longitude}

    Vehicles involved: {vehicle_count}
    Severity: {severity.upper()}
    Confidence: {max_conf:.2f}

    Estimated Response Time: {response_time} seconds

    {action}
    """
            )

            create_alert(
                alert_type="accident",
                location=f"{city} ({latitude}, {longitude})",
                severity=severity,
                message=f"Accident detected involving {vehicle_count} vehicles",
                email_sent=True
            )

    # FINAL MESSAGE 
    if severity == "high":
        st.error(f"Major accident detected involving {vehicle_count} vehicles.")
    elif severity == "medium":
        st.warning(f"Moderate accident detected involving {vehicle_count} vehicles.")
    elif severity == "low":
        st.info(f"Minor accident detected involving {vehicle_count} vehicles.")
    else:
        st.success("No accident detected. Traffic conditions normal.")

    os.remove(temp_path)



app_footer()