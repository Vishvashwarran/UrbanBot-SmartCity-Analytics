from utils.llm import call_llm
from utils.db import execute_query
from utils.intent_guard import is_smartcity_query


def handle_db_query(user_query: str):

    lower_q = user_query.lower()

    # BLOCK DESTRUCTIVE OPERATIONS FIRST
    destructive_words = ["delete", "drop", "truncate", "update", "insert", "alter", "blast", "bomb"]

    if any(word in lower_q for word in destructive_words):
        return "Destructive operations are not allowed. I support only read-only Smart City data queries."

    # DOMAIN GUARD
    if not is_smartcity_query(user_query):
        return "I can answer only Smart City data questions."

    # GREETING
    greetings = ["hi", "hello", "hey"]
    if lower_q.strip() in greetings:
        return "Hello 👋 How can I assist you with Smart City operations?"

    # SQL GENERATION PROMPT 
    prompt = f"""
You are a MySQL expert.

Return ONLY a valid MySQL SELECT query.
No explanation. No markdown.

Database: smartcity

Tables:

traffic_data(timestamp, city, area, vehicle_count, avg_speed_kmph, congestion_level, is_peak_hour)

air_quality_data(timestamp, city, monitoring_station, aqi, aqi_category, pm25, pm10)

citizen_complaints(complaint_id, created_at, city, category, priority, status)

accident_events(accident_id, detected_at, severity, vehicle_count, latitude, longitude)

crowd_density_data(crowd_id, timestamp, city, location, estimated_count, density_level)

road_infra_images(image_id, captured_at, city, latitude, longitude)

road_infra_annotations(annotation_id, image_id, object_class)

system_alerts(alert_id, alert_type, generated_at, location, severity, resolved)

Rules:
- Use only existing columns
- If user asks "latest" → ORDER BY correct time column DESC LIMIT 1
- If user asks "today" → use DATE(column) = CURDATE()
- If no limit specified → LIMIT 10
- Infrastructure condition → use road_infra_annotations
- To get city for infrastructure → JOIN road_infra_images using image_id
- To get accident image → JOIN accident_events.image_id = road_infra_images.image_id

Time columns:
traffic_data.timestamp
air_quality_data.timestamp
crowd_density_data.timestamp
citizen_complaints.created_at
accident_events.detected_at
road_infra_images.captured_at
system_alerts.generated_at

User Question:
{user_query}
"""

    raw_sql = call_llm(prompt)

    # CLEAN SQL 
    sql = raw_sql.strip()
    sql = sql.replace("```sql", "").replace("```", "")
    sql = sql.replace("Here is the MySQL SELECT query:", "")
    sql = sql.split(";")[0].strip() + ";"

    sql_upper = sql.upper()

    #  SAFETY CHECK
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]

    if any(word in sql_upper for word in forbidden):
        return "Destructive operations are not allowed. I support only read-only Smart City data queries."

    if not sql_upper.startswith("SELECT"):
        return "I can answer only Smart City data questions."

    # EXECUTE QUERY 
    try:
        result = execute_query(sql)

        if not result:
            return "No data available for your request."
        
                # 🖼 IMAGE RESPONSE (ONLY IF image_url PRESENT)
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
            row = result[0]

            if "image_url" in row and row["image_url"]:
                return {
                    "type": "image",
                    "title": "Latest Image",
                    "url": row.get("image_url"),
                    "city": row.get("city", ""),
                    "time": row.get("detected_at", row.get("timestamp", "")),
                    "insight": ""
                }

        # COUNT RESULT 
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):

            row = result[0]
            col = list(row.keys())[0]
            value = row[col]

            if "count" in col.lower():

                if value == 0:

                    if "complaint" in lower_q:
                        return "No citizen complaints have been raised so far."

                    elif "accident" in lower_q:
                        return "No accidents detected so far."

                    elif "traffic" in lower_q or "congestion" in lower_q:
                        return "No high congestion events recorded."

                    elif "crowd" in lower_q:
                        return "No crowd activity detected."

                    elif "pothole" in lower_q:
                        return "No potholes detected."

                    elif "infrastructure" in lower_q or "streetlight" in lower_q:
                        return "No infrastructure issues reported."

                    elif "alert" in lower_q:
                        return "No system alerts generated."

                    return "No records found."

        # SMALL TABLE
        if isinstance(result, list) and len(result) <= 5 and isinstance(result[0], dict):

            lines = []
            for row in result:
                lines.append(" | ".join([f"{k}: {v}" for k, v in row.items()]))

            return "\n".join(lines)

        #  LLM GROUNDED INSIGHT 
        explain_prompt = f"""
Generate a short Smart City insight using ONLY the SQL result.

Rules:
- Use only the values present
- Do NOT add new numbers, dates, or assumptions
- Write 2–3 concise sentences
- Do NOT interpret missing values
- Show the numbers exactly as they are

User question:
{user_query}

SQL result:
{result}
"""

        return call_llm(explain_prompt)

    except Exception as e:
        return f"Database error: {str(e)}"