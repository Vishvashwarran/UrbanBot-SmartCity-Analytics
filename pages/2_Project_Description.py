import streamlit as st
from utils.ui_components import app_footer

st.set_page_config(page_title="Project Overview", layout="wide")

st.title("🏙 Smart City Analytics – Project Overview")

st.markdown("""
### 🎯 Objective
An AI-powered urban monitoring and decision-support platform that enables city administrators to:

- Monitor real-time city conditions  
- Detect critical events automatically  
- Prioritize civic issues using AI  
- Generate operational insights  
- Support faster and data-driven governance  
""")

st.divider()

# SYSTEM ARCHITECTURE
st.title("System Architecture")
st.markdown(
"🛰 **Detection Layer** ➝ ☁ **S3** ➝ 🛢 **RDS** ➝ 🧠 **RAG Index** ➝ 🤖 **Multi-Agent LLM** ➝ 📊 **Dashboard**"
)
st.divider()
# PROBLEM STATEMENT
st.header("🚧 Problem Statement")

st.markdown("""
Modern cities face major challenges:

- Traffic congestion
- Air pollution
- Road accidents
- Infrastructure damage
- Overcrowding
- Delayed complaint resolution

Existing systems are:

❌ Manual  
❌ Reactive  
❌ Not data-driven  

### ✅ Solution

A centralized **Smart City AI Analytics Platform** that performs:

- Real-time monitoring  
- Automated detection  
- Predictive analytics  
- AI-powered reporting  
""")

st.divider()

# CORE MODULES 
st.header("🧠 Core AI Modules")

col1, col2, col3 = st.columns(3)

col1.markdown("""
#### 🚦 Traffic Analysis
- Vehicle detection using YOLO
- Congestion prediction using LSTM
- Peak-hour identification
""")

col2.markdown("""
#### 🌫 Air Quality Prediction
- AQI forecasting using LSTM
- Pollution category classification
- Health risk alerts
""")

col3.markdown("""
#### 🛣 Pothole Detection
- Road damage detection using YOLO
- Maintenance prioritization
""")

col4, col5, col6 = st.columns(3)

col4.markdown("""
#### 🚑 Accident Detection
- Accident severity classification
- Emergency response trigger
""")

col5.markdown("""
#### 👥 Crowd Monitoring
- Crowd density estimation
- Public safety alerts
""")

col6.markdown("""
#### 💡 Infrastructure Monitoring
- Streetlight fault detection
- Urban asset condition tracking
""")

st.divider()

# NLP MODULE 
st.header("🧾 Citizen Complaint Intelligence (NLP)")

st.markdown("""
- Sentiment analysis using VADER  
- Priority classification  
- Department auto-assignment  
- AI-based urgency scoring  

### 🎯 Outcome
Faster grievance redressal and workload optimization.
""")

st.divider()

# LLM MODULE 
st.header("🤖 UrbanBot AI Intelligence")

st.markdown("""
A multi-agent AI assistant that can:

- Answer city data queries
- Generate operational reports
- Draft official emails
- Provide decision-support insights

### 🧠 Agents

- Database Query Agent  
- Report Generation Agent  
- Email Drafting Agent  
- Advisory Agent  
- RAG Knowledge Agent  
""")

st.divider()

# TECH STACK 
st.header("⚙ Technology Stack")

col1, col2 = st.columns(2)

col1.markdown("""
### 🖥 Frontend
- Streamlit Dashboard

### 🧠 AI / ML
- YOLOv8 – Object Detection  
- LSTM – Time Series Prediction  
- NLP – Sentiment Analysis  
- LLM – Ollama (Llama3)
""")

col2.markdown("""
### ☁ Cloud & Database
- AWS S3 – Image Storage  
- AWS RDS – Structured Data 
- AWS EC2 – Model Inference & Backend Deployment 
- MySQL – Data Management  

### 📊 Visualization
- Plotly
- Real-time KPIs
""")

st.divider()

# DATA FLOW
st.header("🔄 System Workflow")

st.markdown("""
1️⃣ Capture image / sensor / complaint data  
2️⃣ AI model processes input  
3️⃣ Store results in AWS RDS  
4️⃣ Store media in AWS S3  
5️⃣ Trigger alerts if critical  
6️⃣ Display insights in dashboard  
7️⃣ AI assistant supports decision-making  
""")

st.divider()

# KEY FEATURES 
st.header("⭐ Key Features")

st.markdown("""
✔ Real-time urban monitoring  
✔ AI-based event detection  
✔ Predictive analytics  
✔ Automated alert system  
✔ Citizen grievance intelligence  
✔ Command center dashboard  
✔ LLM-powered decision support  
""")

st.divider()

# IMPACT
st.header("🌍 Expected Impact")

st.markdown("""
- Faster emergency response  
- Reduced traffic congestion  
- Improved air quality monitoring  
- Proactive infrastructure maintenance  
- Data-driven governance  
- Enhanced citizen satisfaction  
""")

st.divider()

# FUTURE SCOPE 
st.header("🚀 Future Enhancements")

st.markdown("""
- Live CCTV integration  
- IoT sensor connectivity  
- Mobile application for field officers  
- GIS-based smart heatmaps  
- Automated work order generation  
""")



app_footer()