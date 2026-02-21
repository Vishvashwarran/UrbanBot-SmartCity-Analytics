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

st.title("💡 Streetlight & Road Infrastructure Monitoring")

# LOAD MODEL 
@st.cache_resource
def load_model():
    return YOLO("models/streetlight_best.pt")  

model = load_model()

# INPUT SECTION 
st.subheader("📍 Location Details")

city = st.text_input("City", placeholder="Eg : Chennai")
area = st.text_input("Area / Zone", placeholder="Eg : Anna Nagar")

col1, col2 = st.columns(2)
with col1:
    latitude = st.number_input("Latitude", format="%.6f")
with col2:
    longitude = st.number_input("Longitude", format="%.6f")

camera_source = st.selectbox("Camera Source", ["CCTV", "Drone", "Mobile"])
weather = st.selectbox("Weather", ["Clear", "Rain", "Fog", "Cloudy"])

infra_file = st.file_uploader(
    "Upload Infrastructure Image / Video",
    type=["jpg", "png", "mp4"]
)

# PRIORITY FUNCTION
def get_priority(defect_count):
    if defect_count >= 3:
        return "high"
    elif defect_count == 2:
        return "medium"
    elif defect_count == 1:
        return "low"
    return "none"

# RUN BUTTON 
if st.button("🚀 Run Infrastructure Analysis"):

    if infra_file is None or area == "":
        st.warning("Please provide area and media file")
        st.stop()

    image_id = str(uuid.uuid1())
    defect_count = 0
    max_conf = 0

    # IMAGE
    if infra_file.type.startswith("image"):

        image = Image.open(infra_file)
        results = model(image, conf=0.05)

        plotted = results[0].plot()
        st.image(plotted, use_container_width=True)

        boxes = results[0].boxes

        if boxes is not None:
            defect_count = len(boxes)
            if boxes is not None and boxes.conf is not None and boxes.conf.numel() > 0:
                max_conf = float(boxes.conf.max())

        temp_path = f"temp_{time.time()}.jpg"
        image.convert("RGB").save(temp_path)

    # VIDEO 
    else:

        suffix = os.path.splitext(infra_file.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(infra_file.read())
            temp_path = tmp.name

        cap = cv2.VideoCapture(temp_path)

        frame_skip = 5

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if int(cap.get(1)) % frame_skip != 0:
                continue

            results = model(frame, conf=0.05)

            boxes = results[0].boxes

            if boxes is not None:
                defect_count += len(boxes)
                if boxes.conf.numel() > 0:
                    max_conf = max(max_conf, float(boxes.conf.max()))

        cap.release()
        st.video(temp_path)

    priority = get_priority(defect_count)

    # S3 UPLOAD 
    s3_key = f"infrastructure/{city}_{int(time.time())}_{infra_file.name}"
    image_url = upload_to_s3(temp_path, s3_key)

    # SAVE TO RDS 
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO road_infra_images (
            image_id, image_url, captured_at, city,
            latitude, longitude, camera_source,
            weather, road_type, resolution, annotated
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        image_id,
        image_url,
        datetime.datetime.now(),
        city,
        latitude,
        longitude,
        camera_source,
        weather,
        "street_infra",
        "N/A",
        True
    ))

    conn.commit()
    conn.close()

    # EMAIL ALERT
    if priority == "high":

        send_email_alert(
            subject="🚨 Smart City Alert: Critical Infrastructure Failure 🆘",
            message=f"""
Smart City Infrastructure Monitoring System

Critical infrastructure defects detected.

Location:
City: {city}
Area: {area}
Coordinates: {latitude}, {longitude}

Defect Summary:
Total Defects: {defect_count}
Priority Level: HIGH
Confidence Score: {max_conf:.2f}
Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Recommended Action:
Immediate maintenance crew deployment required.

This is an automated alert from the Smart City AI Platform.
"""
        )

        create_alert(
            alert_type="infra",
            location=f"{city} - {area} ({latitude}, {longitude})",
            severity="high",
            message=f"Critical infrastructure defects detected ({defect_count})",
            email_sent=True
        )

        

    # PROFESSIONAL OUTPUT
    if priority == "high":
        st.error(
            f"Critical infrastructure defects detected ({defect_count}). "
            f"Maintenance team has been alerted."
        )

    elif priority == "medium":
        st.warning(
            f"Multiple infrastructure issues identified ({defect_count}). "
            f"Scheduled for priority maintenance."
        )

    elif priority == "low":
        st.info(
            "Minor infrastructure issue detected. Logged for routine inspection."
        )

    else:
        st.success(
            "All monitored infrastructure assets are functioning normally."
        )

    os.remove(temp_path)


app_footer()