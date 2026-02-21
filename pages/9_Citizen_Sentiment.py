import streamlit as st
import datetime
import uuid
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from utils.db import get_connection
from utils.email_alert import send_email_alert
from utils.system_alerts import create_alert
from utils.ui_components import app_footer
from utils.db import execute_query

st.title("🧾 Citizen Complaint Intelligence")

# LOAD MODEL 
@st.cache_resource
def load_sia():
    try:
        nltk.data.find("sentiment/vader_lexicon")
    except:
        nltk.download("vader_lexicon")
    return SentimentIntensityAnalyzer()

sia = load_sia()

#INPUT
st.subheader("📍 Complaint Details")

city = st.text_input("City", placeholder="Eg : Chennai")

category = st.selectbox(
    "Category",
    ["road", "water", "lighting", "pollution", "traffic","overcrowd"]
)

col1, col2 = st.columns(2)
with col1:
    latitude = st.number_input("Latitude", format="%.6f")
with col2:
    longitude = st.number_input("Longitude", format="%.6f")

complaint_text = st.text_area("Enter Complaint")

# DEPARTMENT MAPPING 
department_map = {
    "road": "Public Works",
    "water": "Water Supply",
    "lighting": "Electricity Board",
    "pollution": "Pollution Control",
    "traffic": "Traffic Police",
    "overcrowd" : "Public Works"
}

# PRIORITY KEYWORDS 
high_priority_keywords = [
    "danger","accident","sewage","overflow","no water",
    "not working","garbage","blocked","collapse","overcrowd","overcrowded"
]

# FUNCTIONS
def get_sentiment(text):
    score = sia.polarity_scores(text)["compound"]

    if score <= -0.05:
        return "negative", score
    elif score >= 0.05:
        return "positive", score
    else:
        return "neutral", score


# PRIORITY LOGIC
def get_priority(sentiment, text):
    text = text.lower()

    # HIGH → keyword alone is enough
    if any(k in text for k in high_priority_keywords):
        return "high"

    # MEDIUM → negative without critical keyword
    if sentiment == "negative":
        return "medium"

    return "low"


def get_urgency(priority):
    return {"high": 0.9, "medium": 0.6, "low": 0.3}[priority]


# RUN BUTTON
if st.button("🚀 Analyze Complaint"):

    if complaint_text == "":
        st.warning("Please enter complaint text")
        st.stop()

    sentiment, score = get_sentiment(complaint_text)
    priority = get_priority(sentiment, complaint_text)
    urgency = get_urgency(priority)

    department = department_map[category]

    conn = get_connection()
    cursor = conn.cursor()

    # INSERT COMPLAINT 
    cursor.execute("""
        INSERT INTO citizen_complaints (
            created_at, city, category, complaint_text,
            latitude, longitude, department, status, priority
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        datetime.datetime.now(),
        city,
        category,
        complaint_text,
        latitude,
        longitude,
        department,
        "open",
        priority
    ))

    conn.commit()

    complaint_id = cursor.lastrowid

    if complaint_id == 0:
        st.error("Failed to generate complaint ID. Check AUTO_INCREMENT.")
        st.stop()

    # INSERT NLP OUTPUT INTO RDS
    cursor.execute("""
        INSERT INTO complaint_nlp_analysis (
            analysis_id, complaint_id, sentiment,
            sentiment_score, emotion, topic, urgency_score
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid1()),
        complaint_id,
        sentiment,
        score,
        "frustration" if sentiment == "negative" else "neutral",
        category,
        urgency
    ))

    conn.commit()
    conn.close()

    # EMAIL ALERT + SYSTEM ALERT 

    if priority == "high":

        send_email_alert(
            subject="🚨 Escalation: High-Priority Civic Issue Detected 🆘",
            message=f"""
    Smart City Command & Control Center

    A HIGH-PRIORITY civic complaint has been automatically escalated.

    City: {city}
    Category: {category}
    Department: {department}

    Complaint:
    {complaint_text}

    Immediate field inspection required.
    """
        )

        create_alert(
            alert_type="infra",
            location=f"{city} ({latitude}, {longitude})",
            severity="high",
            message=f"High-priority civic complaint: {category}",
            email_sent=True
        )


    elif priority == "medium":

        send_email_alert(
            subject="📌 New Civic Complaint Assigned for Review",
            message=f"""
    Smart City Command & Control Center

    A complaint has been assigned to {department} for review.

    City: {city}
    Category: {category}

    Action: Schedule inspection.
    """
        )

        create_alert(
            alert_type="infra",
            location=f"{city} ({latitude}, {longitude})",
            severity="medium",
            message=f"Medium-priority civic complaint: {category}",
            email_sent=True
        )


    else:

        send_email_alert(
            subject="📊 Civic Complaint Logged for Monitoring",
            message=f"""
    Smart City Command & Control Center

    Low-priority complaint recorded.

    City: {city}
    Category: {category}
    """
        )

        create_alert(
            alert_type="infra",
            location=f"{city} ({latitude}, {longitude})",
            severity="low",
            message=f"Low-priority civic complaint: {category}",
            email_sent=True
        )

    # OUTPUT 
    if priority == "high":
        st.error("🚨 High-priority complaint detected. Immediate administrative action required.")

    elif priority == "medium":
        st.warning(f"⚠ Complaint logged with medium priority. It will be reviewed by the {department} department.")

    else:
        st.success("✅ Complaint registered successfully. No immediate action required.")


recent = execute_query("""
SELECT city, category, priority,se, created_at
FROM citizen_complaints
ORDER BY created_at DESC
LIMIT 5
""")

st.subheader("🕒 Recent Complaints")

st.dataframe(recent)

app_footer()