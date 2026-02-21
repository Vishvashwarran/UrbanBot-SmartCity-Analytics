from utils.db import execute_query
from utils.llm import call_llm


# FULL CITY REPORT
def generate_full_report():

    traffic = execute_query("""
        SELECT city, COUNT(*) AS high_congestion_count
        FROM traffic_data
        WHERE congestion_level = 'high'
        GROUP BY city
        LIMIT 5
    """)

    aqi = execute_query("""
        SELECT city, aqi, aqi_category
        FROM air_quality_data
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    accidents = execute_query("""
        SELECT severity, COUNT(*) AS incident_count
        FROM accident_events
        GROUP BY severity
    """)

    crowd = execute_query("""
        SELECT city, location, estimated_count, density_level
        FROM crowd_density_data
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    complaints = execute_query("""
        SELECT city, category, priority, status
        FROM citizen_complaints
        ORDER BY created_at DESC
        LIMIT 5
    """)

    potholes = execute_query("""
        SELECT COUNT(*) AS pothole_count
        FROM road_infra_annotations
        WHERE object_class = 'pothole'
    """)

    infrastructure = execute_query("""
        SELECT city, COUNT(*) AS defect_count
        FROM road_infra_images
        WHERE road_type = 'street_infra'
        GROUP BY city
        LIMIT 5
    """)

    if not any([traffic, aqi, accidents, crowd, complaints, potholes, infrastructure]):
        return "No data available to generate the city report."

    data = f"""
TRAFFIC:
{traffic}

AIR QUALITY:
{aqi}

ACCIDENTS:
{accidents}

CROWD:
{crowd}

COMPLAINTS:
{complaints}

POTHOLES:
{potholes}

INFRASTRUCTURE:
{infrastructure}
"""

    prompt = f"""
You are a Smart City Command Center AI assisting city administrators.

Generate a concise multi-section operational city report.

For each section:
- Use a heading
- Use bullet points
- Be factual
- Add Priority: High / Medium / Low based only on values
- Add one short Action line (generic and data-driven)
- No greetings
- No assumptions

DATA:
{data}
"""

    return call_llm(prompt)


# DYNAMIC REPORT (BASED ON USER QUERY)
def handle_report_query(user_query: str):

    q = user_query.lower()

    # ADVISORY MODE (no DB call)
    if any(word in q for word in ["prevent", "reduce", "control", "improve", "solution", "how to"]):
        prompt = f"""
You are a Smart City operations expert assisting city administrators.

Provide concise and practical strategies for:

{user_query}

Rules:
- Use bullet points
- Operational and implementable measures only
- No greetings
- No database references
- Stay within Smart City domain
"""
        return call_llm(prompt)

    # Detect FULL CITY REPORT
    is_full = any(word in q for word in ["full", "overall", "complete", "city status", "city report"])
    has_domain = any(word in q for word in [
        "traffic", "air", "aqi", "pollution",
        "accident", "crash",
        "crowd",
        "complaint", "grievance",
        "pothole",
        "infrastructure", "infra", "streetlight"
    ])

    if is_full and not has_domain:
        return generate_full_report()

    data_sections = []

    # TRAFFIC
    if any(word in q for word in ["traffic", "congestion", "road"]):
        traffic = execute_query("""
            SELECT city, COUNT(*) AS high_congestion_count
            FROM traffic_data
            WHERE congestion_level = 'high'
            GROUP BY city
            LIMIT 5
        """)
        data_sections.append(f"TRAFFIC:\n{traffic}")

    # AIR QUALITY
    if any(word in q for word in ["air", "aqi", "pollution"]):
        aqi = execute_query("""
            SELECT city, aqi, aqi_category
            FROM air_quality_data
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        data_sections.append(f"AIR QUALITY:\n{aqi}")

    # ACCIDENTS
    if any(word in q for word in ["accident", "crash", "collision"]):
        accidents = execute_query("""
            SELECT severity, COUNT(*) AS incident_count
            FROM accident_events
            GROUP BY severity
        """)
        data_sections.append(f"ACCIDENTS:\n{accidents}")

    # CROWD
    if "crowd" in q:
        crowd = execute_query("""
            SELECT city, location, estimated_count, density_level
            FROM crowd_density_data
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        data_sections.append(f"CROWD:\n{crowd}")

    # COMPLAINTS
    if any(word in q for word in ["complaint", "grievance", "issue"]):
        complaints = execute_query("""
            SELECT city, category, priority, status
            FROM citizen_complaints
            ORDER BY created_at DESC
            LIMIT 5
        """)
        data_sections.append(f"COMPLAINTS:\n{complaints}")

    # POTHOLES
    if "pothole" in q:
        potholes = execute_query("""
            SELECT COUNT(*) AS pothole_count
            FROM road_infra_annotations
            WHERE object_class = 'pothole'
        """)
        data_sections.append(f"POTHOLES:\n{potholes}")

    # INFRASTRUCTURE
    if any(word in q for word in ["infrastructure", "infra", "streetlight"]):
        infrastructure = execute_query("""
            SELECT city, COUNT(*) AS defect_count
            FROM road_infra_images
            WHERE road_type = 'street_infra'
            GROUP BY city
            LIMIT 5
        """)
        data_sections.append(f"INFRASTRUCTURE:\n{infrastructure}")

    # NOTHING MATCHED
    if not data_sections:
        return "Please specify which Smart City report you need (traffic, AQI, accidents, crowd, complaints, potholes, infrastructure, or full city report)."

    data = "\n\n".join(data_sections)

    prompt = f"""
You are a Smart City Command Center AI assisting city administrators.

Generate a short operational report ONLY for the requested sections.

Rules:
- Use headings
- Use bullet points
- Be factual
- Do NOT include unrelated sections
- No greetings
- No assumptions
- Add 1–2 short operational insights based ONLY on the given numbers
- Display values exactly as given

DATA:
{data}

User Request:
{user_query}
"""

    return call_llm(prompt)