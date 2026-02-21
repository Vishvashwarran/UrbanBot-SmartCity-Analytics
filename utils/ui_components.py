import streamlit as st

def app_footer():
    st.markdown(
        """
        <style>
        .footer {
            position: relative;
            bottom: 0;
            width: 100%;
            text-align: center;
            color: gray;
            padding-top: 30px;
        }
        </style>

        <div class="footer">
        <hr>
        <small>
        <b>UrbanBot – Smart City Analytics Platform</b><br>
        AI-Powered Urban Decision Support System<br>
        © Developed by Vishvashwarran V B<br>
        </small>
        </div>
        """,
        unsafe_allow_html=True
    )


