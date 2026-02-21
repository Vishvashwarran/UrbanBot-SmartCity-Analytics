import streamlit as st
import datetime
import uuid
import time
import os
import tempfile
import cv2
from PIL import Image
from ultralytics import YOLO
from utils.db import get_connection
from utils.s3_upload import upload_to_s3
from utils.email_alert import send_email_alert
from utils.system_alerts import create_alert
from utils.ui_components import app_footer

st.title("🛣 Pothole Detection")

# LOAD MODEL 
@st.cache_resource
def load_model():
    return YOLO("models/pothole_best.pt")

model = load_model()

# INPUT SECTION 
st.subheader("📍 Location Details")

city = st.text_input("City", placeholder="Eg : Chennai")
road_type = st.selectbox("Road Type", ["Highway", "Main Road", "Street"])

col1, col2 = st.columns(2)
with col1:
    latitude = st.number_input("Latitude", format="%.6f")
with col2:
    longitude = st.number_input("Longitude", format="%.6f")

camera_source = st.selectbox("Camera Source", ["CCTV", "Drone", "Mobile"])
weather = st.selectbox("Weather", ["Clear", "Rain", "Fog", "Cloudy"])

infra_file = st.file_uploader(
    "Upload Road Image / Video",
    type=["jpg", "png", "mp4"]
)

# BUTTON 
if st.button("🚀 Run Detection"):

    if infra_file is None:
        st.warning("Please upload an image or video")
        st.stop()

    pothole_count = 0
    image_id = str(uuid.uuid4())
    temp_path = None

    # IMAGE 
    if infra_file.type.startswith("image"):

        image = Image.open(infra_file)

        results = model(image, conf=0.15)

        plotted = results[0].plot()
        plotted = cv2.cvtColor(plotted, cv2.COLOR_BGR2RGB)  # ✅ COLOR FIX
        st.image(plotted, use_container_width=True)

        boxes = results[0].boxes
        if boxes is not None:
            pothole_count = len(boxes)

        temp_path = f"temp_{int(time.time())}.jpg"
        image.save(temp_path)

        resolution = f"{image.width}x{image.height}"

    # VIDEO 
    else:

        suffix = os.path.splitext(infra_file.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
            tfile.write(infra_file.read())
            temp_path = tfile.name

        cap = cv2.VideoCapture(temp_path)

        frame_skip = 5
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_skip != 0:
                continue

            results = model(frame, conf=0.05)

            boxes = results[0].boxes
            if boxes is not None:
                pothole_count += len(boxes)

        cap.release()

        st.video(temp_path)

        resolution = "video"

    # S3 UPLOAD
    unique_name = f"potholes/{city}_{int(time.time())}_{infra_file.name}"
    image_url = upload_to_s3(temp_path, unique_name)

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
        road_type,
        resolution,
        True
    ))

    # SAVE ANNOTATIONS TO RDS
    if pothole_count > 0 and infra_file.type.startswith("image"):

        boxes = results[0].boxes

        for box in boxes:

            annotation_id = str(uuid.uuid4())
            x, y, w, h = box.xywh[0].tolist()
            confidence = float(box.conf[0])

            cursor.execute("""
                INSERT INTO road_infra_annotations (
                    annotation_id, image_id, object_class,
                    bbox_x, bbox_y, bbox_width, bbox_height, confidence
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                annotation_id,
                image_id,
                "pothole",
                x, y, w, h,
                confidence
            ))

    conn.commit()
    conn.close()

    # EMAIL ALERT
    if pothole_count >= 3:

        send_email_alert(
            subject="🚨 Smart City Alert: Critical Road Damage Detected 🆘",
            message=f"""
            Smart City Infrastructure Monitoring System

            A critical road surface issue has been detected.

            Location:
            City: {city}
            Road Type: {road_type}
            Coordinates: {latitude}, {longitude}

            Detection Summary:
            Potholes Identified: {pothole_count}
            Detection Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            Camera Source: {camera_source}
            Weather: {weather}

            Recommended Action:
            Immediate inspection and maintenance crew deployment is advised to prevent traffic disruption and ensure public safety.

            This is an automated alert generated by the Smart City AI Platform.

            — Smart City AI Monitoring System
            """
        )

        create_alert(
            alert_type="infra",
            location=f"{road_type}, {city}",
            severity="high",
            message=f"{pothole_count} potholes detected",
            email_sent=True
        )

    # FINAL STATUS
    if pothole_count >= 3:

        st.error(
            f"Pothole detection completed: {pothole_count} potholes identified at {road_type} in {city}. "
            "Maintenance alert has been triggered."
        )

    elif pothole_count >= 1:

        st.warning(
            f"Pothole detection completed: {pothole_count} potholes identified. "
            "Scheduled for maintenance review."
        )

    else:

        st.success("No potholes detected. Road condition appears normal.")


    # CLEAN TEMP FILE
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)



app_footer()