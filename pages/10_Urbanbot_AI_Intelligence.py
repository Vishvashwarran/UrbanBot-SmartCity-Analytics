import streamlit as st
from agents.db_agent import handle_db_query
from agents.intent_agent import detect_intent
from agents.email_agent import handle_email_query
from agents.report_agent import handle_report_query
from agents.advisory_agent import handle_advisory_query
from agents.rag_agent import handle_rag_query
from agents.s3_agent import handle_s3_query

st.set_page_config(page_title="UrbanBot AI Intelligence", layout="wide")

st.title("🤖 UrbanBot AI Intelligence")

st.markdown("""
<style>
.block-container {
    max-width: 900px;
    margin: auto;
}
</style>
""", unsafe_allow_html=True)

# SESSION
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("🗑 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# WELCOME SCREEN 
if len(st.session_state.messages) == 0: 
    st.markdown("<h2 style='text-align:center;'>Welcome to UrbanBot AI 👋</h2>", unsafe_allow_html=True) 
    st.markdown("<p style='text-align:center;'>Ask about Traffic • AQI • Accidents • Complaints • Reports</p>", unsafe_allow_html=True) 
    c1, c2, c3 = st.columns(3) 
    with c1: 
        st.info("🚦 Traffic Insights")
        st.info("📍 Complaint Analytics")
        with c2:
             st.info("🌫 AQI Monitoring")
             st.info("📧 Smart Email Drafting")
             with c3:
                 st.info("🧾 City Reports")
                 st.info("🛰 AI Advisory")

# CHAT HISTORY
for msg in st.session_state.messages:
    align = "flex-end" if msg["role"] == "user" else "flex-start"
    bg = "#2b313e" if msg["role"] == "user" else "#444654"

    st.markdown(f"""
    <div style="display:flex; justify-content:{align};">
        <div style="background:{bg}; padding:10px 14px; border-radius:14px; margin:6px 0; color:white; max-width:70%;">
        {msg["content"]}
        </div>
    </div>
    """, unsafe_allow_html=True)

# INPUT
user_input = st.chat_input("Ask about traffic, AQI, accidents, complaints...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end;">
        <div style="background:#2b313e; padding:10px 14px; border-radius:14px; margin:6px 0; color:white; max-width:70%;">
        {user_input}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Analyzing Smart City data..."):

        intent = detect_intent(user_input)

        if intent == "database":
            response = handle_db_query(user_input)

        elif intent == "report":
            response = handle_report_query(user_input)

        elif intent == "s3":
            response = handle_s3_query(user_input)

        elif intent == "email":
            response = handle_email_query(user_input)

        elif intent == "advisory":
            response = handle_advisory_query(user_input)

        elif intent == "general":
            text = user_input.lower()
            if text in ["hi", "hello", "hey"]:
                 response = "Hello! 👋 I am your Smart City AI assistant. How can I help you today?"
            elif text in ["thank you", "thanks","ok thanks"]:
                 response = "You're welcome 😊. I'm here to help with any city-related concerns."
            elif text in ["bye","goodbye","ok"]:
                 response = "Thank you for using Smart City Analytics. Have a great day! 👋"
            elif "who are you" in text or "your name" in text:
                 response = "I am your Smart City AI assistant created by Vishvashwarran, designed to help with traffic, AQI, accidents, reports, and civic emails."
            else:
                response = "How can I assist you with Smart City operations?"

        elif intent == "rag":
            response = handle_rag_query(user_input)

        else:
            response = "I can help only with Smart City data insights, reports, and drafting official emails."

    # IMAGE MODE
    if isinstance(response, dict) and response.get("type") == "image":

        st.markdown(f"### 🖼 {response['title']}")
        st.image(response["url"], use_container_width=True)

        st.markdown(f"**City:** {response['city']}")
        st.markdown(f"**Time:** {response['time']}")
        st.markdown("📊 **AI Insight:**")
        st.write(response["insight"])

        display_text = f"🖼 {response['title']} — {response['city']} ({response['time']})"

    else:
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-start;">
            <div style="background:#444654; padding:10px 14px; border-radius:14px; margin:6px 0; color:white; max-width:70%;">
            {response}
            </div>
        </div>
        """, unsafe_allow_html=True)

        display_text = response

    st.session_state.messages.append(
    {"role": "assistant", "content": response if isinstance(response, str) else response.get("title", "")}
)