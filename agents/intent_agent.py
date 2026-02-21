from utils.llm import call_llm


def detect_intent(user_query: str) -> str:

    q = user_query.lower().strip()

    # EMAIL → TOP PRIORITY
    if any(word in q for word in [
        "email", "mail", "send mail", "send email",
        "write mail", "draft mail", "complaint to","send a mail","send a email"
    ]):
        return "email"

    # ADVISORY / STRATEGY MODE
    if any(word in q for word in [
        "prevent", "reduce", "control", "improve", "solution", "how to"
    ]):
        return "advisory"

    # FULL / SECTION REPORTS
    if any(word in q for word in [
        "report", "summary", "analytics", "city status", "overall","summarize"
    ]):
        return "report"

    # RAG → INSIGHTS / SITUATION / AREA-BASED QUESTIONS
    if any(word in q for word in [
        "which area", "where", "situation", "status",
        "analysis", "give insights", "problem", "issue"
    ]):
        return "rag"
    
    # 🖼 IMAGE REQUESTS → S3
    if any(word in q for word in ["image", "photo", "snapshot", "camera", "cctv"]):
        return "s3"

    # DATABASE → EXACT FACT / COUNT / LIST
    if any(word in q for word in [
        "how many", "count", "list", "show", "latest", "today"
    ]):
        return "database"

    # DATABASE → DOMAIN + FACT STYLE
    if any(word in q for word in [
        "accident", "traffic", "aqi", "complaint",
        "crowd", "infrastructure", "pothole"
    ]):
        return "database"
    
    # COURTESY / GENERAL CHAT
    if q in ["hi", "hello", "hey", "thanks", "thank you", "ok","ok thanks", "okay", "cool", "great"]:
        return "general"

    if any(word in q for word in [
        "how are you", "who are you", "your name", "what is your name","bye",'goodbye',"ok"
    ]):
        return "general"

    # FALLBACK 
    prompt = f"""
Classify the intent into ONE word only:

general
database
report
email
rag
s3
advisory

Query: {user_query}
"""

    intent = call_llm(prompt).strip().lower()

    if "email" in intent:
        return "email"
    elif "advisory" in intent:
        return "advisory"
    elif "report" in intent:
        return "report"
    elif "rag" in intent:
        return "rag"
    elif "s3" in intent:
        return "s3"
    elif "general" in intent:
        return "general"
    else:
        return "database"