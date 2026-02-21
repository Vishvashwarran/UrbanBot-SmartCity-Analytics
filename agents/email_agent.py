import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from utils.llm import call_llm

load_dotenv()


def handle_email_query(user_query: str):

    query_lower = user_query.lower()

    # BACKEND DOMAIN CHECK 

    smartcity_keywords = [
        "traffic", "accident", "streetlight", "garbage",
        "pollution", "air quality", "water", "drainage",
        "road", "pothole", "signal", "crowd", "noise",
        "public transport", "bus", "metro", "sewage",
        "waste", "infrastructure","aqi"
    ]

    if not any(word in query_lower for word in smartcity_keywords):
        return "I can send emails only for Smart City related services."

    # Detect explicit SEND intent only
    send_email = any(
        phrase in query_lower
        for phrase in [
            "send this mail",
            "send the mail",
            "send email",
            "email it",
            "forward this",
            "send a mail",
            "send it",
            "send a email"
        ]
    )

    prompt = f"""
You are a Smart City civic email assistant.

Your task is to draft formal emails ONLY for Smart City related civic issues.

Allowed topics:
- traffic congestion
- road accidents
- air quality problems
- crowd management
- public infrastructure issues
- system/service alerts
- citizen complaints about city services
- water supply issues
- drainage blockage
- sewage overflow
- pipeline leakage

If the user request is NOT related to Smart City services,
respond ONLY with:
I can send emails only for Smart City related services.

Do NOT write any email in that case.

Email Rules:
- The sender is a citizen (NOT an admin)
- Do NOT add any name unless provided
- Do NOT add placeholders like [Your Name],[Name]
- Keep the tone formal, realistic, and polite
- Use ONLY the details provided in the user request
- Do NOT create or assume any location, street name, or city
- If location is not given, refer to it as "my area"
- Do NOT create imaginary facts
- End naturally without designation
- Return the email in plain text only
- Do NOT use HTML, markdown, or code blocks
- If the user mentions a name in the request,you MUST use that exact name at the end of the email.
- Do NOT write notes like "no name provided".
- If no name is mentioned, simply end the email naturally like Thank You.

Format:

Subject: <short subject>

<email body>

User request:
{user_query}
"""

    email_content = call_llm(prompt).strip()

    if email_content.lower().startswith("i can only send emails"):
        return email_content

    # BLOCK NON-SMARTCITY REQUESTS
    if email_content == "I can send emails only for Smart City related services.":
        return email_content

    # EXTRACT SUBJECT 

    subject = "Civic Issue Report"
    body = email_content

    if "subject:" in email_content.lower():

        lines = email_content.splitlines()

        for i, line in enumerate(lines):
            if line.lower().startswith("subject"):
                subject = line.split(":", 1)[1].strip()
                body = "\n".join(lines[i + 1:]).strip()
                break

    # DRAFT MODE
    if not send_email:
        return f"""✉ **Email Draft**

**Subject:** {subject}

{body}
"""

    # SEND EMAIL 

    sender = os.getenv("ALERT_EMAIL")
    password = os.getenv("ALERT_EMAIL_PASSWORD")
    receiver = os.getenv("SENDER_EMAIL")

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = receiver

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()

        return f"""📧 **Email sent successfully**

**Subject:** {subject}

{body}
"""

    except Exception as e:
        return f"❌ Email sending failed: {str(e)}"