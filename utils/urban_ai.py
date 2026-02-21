from utils.db import execute_query
from utils.llm import call_llm


def get_live_city_context():

    traffic = execute_query("""
        SELECT city, area, congestion_level, vehicle_count
        FROM traffic_data
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    aqi = execute_query("""
        SELECT city, aqi, aqi_category
        FROM air_quality_data
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    accidents = execute_query("""
        SELECT severity, COUNT(*)
        FROM accident_events
        GROUP BY severity
    """)

    complaints = execute_query("""
        SELECT category, priority, COUNT(*)
        FROM citizen_complaints
        WHERE status='open'
        GROUP BY category, priority
    """)

    crowd = execute_query("""
        SELECT location, density_level, estimated_count
        FROM crowd_density_data
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    alerts = execute_query("""
        SELECT alert_type, location, severity
        FROM system_alerts
        WHERE resolved = FALSE
        ORDER BY generated_at DESC
        LIMIT 5
    """)

    return f"""
TRAFFIC:
{traffic}

AIR QUALITY:
{aqi}

ACCIDENTS:
{accidents}

CITIZEN COMPLAINTS:
{complaints}

CROWD:
{crowd}

ACTIVE ALERTS:
{alerts}
"""


def ask_urban_ai(user_query):

    context = get_live_city_context()

    prompt = f"""
You are UrbanBot AI – Smart City Command & Control Assistant.

RULES:
- Answer ONLY using the provided system data
- Be short and operational
- No greetings
- No assumptions
- If no data → say "No live data available"

SYSTEM DATA:
{context}

QUESTION:
{user_query}
"""

    return call_llm(prompt)

