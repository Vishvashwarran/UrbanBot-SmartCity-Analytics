import streamlit as st
from utils.ui_components import app_footer

st.set_page_config(page_title="About Me", layout="wide")

st.title("👨‍💻 About the Developer")

# PROFILE SECTION
col1, col2 = st.columns([1, 2])

with col1:
    st.image("assets/profile.png", width=320)  

with col2:
    st.subheader("Vishvashwarran V B")

    st.write("""
Information Technology graduate with strong interest in **Data Science, Machine Learning, and AI-driven systems**.  

Experienced in building intelligent analytics platforms that combine:
- Computer Vision  
- NLP & Sentiment Analysis  
- LSTM Forecasting  
- RAG-based AI Assistants  
- Cloud Deployment  

Passionate about transforming complex datasets into **actionable insights for real-world decision making**.
""")

# ANIMATED METRICS 
st.subheader("📊 Professional Snapshot")

col1, col2, col3 = st.columns(3)

col1.metric("Projects Built", "7+")
col2.metric("AI / ML Technologies", "10+")
col3.metric("Certifications", "3+")

# SKILL PROGRESS BARS
st.subheader("🧠 Technical Skills")

st.markdown("**Python**")
st.progress(90)

st.markdown("**Machine Learning**")
st.progress(85)

st.markdown("**Deep Learning (LSTM, CV)**")
st.progress(80)

st.markdown("**NLP & RAG AI / LLM**")
st.progress(85)

st.markdown("**SQL / Database Engineering**")
st.progress(80)

st.markdown("**MongoDB (NoSQL)**")
st.progress(70)

# TOOLS & PLATFORMS 
st.subheader("🛠 Tools & Platforms")

st.markdown("""
- Streamlit  
- MySQL  
- MongoDB (NoSQL)  
- AWS (S3, RDS, EC2)  
- Azure (Basics)  
- Git & GitHub  
- Power BI  
""")

# CAREER INTEREST 
st.subheader("🎯 Career Interests")

st.write("""
Actively seeking opportunities in:

- Data Scientist  
- Data Analyst
- Machine Learning Engineer  
- AI Specialist  
- AI Engineer  
- Analytics Engineer  
- Smart Systems / Intelligent Automation Roles  

Interested in building scalable AI systems that solve complex, real-world problems using data-driven intelligence.
""")

# PERSONAL INTEREST PARAGRAPH 
st.subheader("💡 Professional Interest")

st.write("""
I am passionate about the end-to-end Data Science lifecycle, with strong interest in applied Artificial Intelligence, predictive analytics, and intelligent decision-support systems. I enjoy transforming raw data into scalable, real-time, data-driven solutions that create measurable impact. My focus lies in machine learning, AI-powered automation, and cloud-based analytics platforms for solving real-world urban and business problems.
especially where data, automation, and predictive modeling intersect. I enjoy designing end-to-end AI systems — from data ingestion and modeling to deployment and decision-support visualization — that create measurable operational impact.
""")


# LINKEDIN & GITHUB
st.subheader("🔗 Professional Profiles")

col1, col2 = st.columns(2)

col1.link_button("🔗 LinkedIn Profile", "https://www.linkedin.com/in/vishvashwarranvb/")
col2.link_button("💻 GitHub Profile", "https://github.com/Vishvashwarran")

# RESUME DOWNLOAD 
st.subheader("📄 Resume")

with open("assets/Resume.pdf", "rb") as file:
    st.download_button(
        label="⬇ Download Resume",
        data=file,
        file_name="Vishvashwarran_Resume.pdf",
        mime="application/pdf"
    )


app_footer()