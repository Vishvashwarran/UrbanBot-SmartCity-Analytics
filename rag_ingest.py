from utils.db import execute_query, execute_write
import uuid
from datetime import datetime


# CLEAR OLD KNOWLEDGE
print("🧹 Clearing old RAG knowledge...")
execute_write("DELETE FROM rag_documents", ())

DEFAULT_VECTOR = str([0.0] * 384)
def insert(text, source_type, reference):

    try:

        execute_write("""
            INSERT INTO rag_documents
            (doc_id, source_type, source_reference, text_chunk, embedding_vector, created_at)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            str(uuid.uuid4()),
            source_type,
            reference,
            text,
            DEFAULT_VECTOR,
            datetime.now()
        ))

    except Exception as e:
        print(f"❌ Insert failed: {e}")


print("🚦 Ingesting TRAFFIC data...")
traffic = execute_query("""
SELECT city, area, congestion_level, vehicle_count
FROM traffic_data
LIMIT 50
""")

for row in traffic:
    insert(
        f"Traffic at {row['area']} in {row['city']} "
        f"is {row['congestion_level']} with {row['vehicle_count']} vehicles",
        "traffic",
        f"{row['city']} - {row['area']}"
    )


print("🌫 Ingesting AIR QUALITY data...")
aqi = execute_query("""
SELECT city, aqi, aqi_category
FROM air_quality_data
LIMIT 50
""")

for row in aqi:
    insert(
        f"AQI in {row['city']} is {row['aqi']} which is {row['aqi_category']}",
        "air_quality",
        row["city"]
    )


print("🚑 Ingesting COMPLAINTS data...")
complaints = execute_query("""
SELECT complaint_id, city, category, status
FROM citizen_complaints
LIMIT 50
""")

for row in complaints:
    insert(
        f"Complaint {row['complaint_id']} in {row['city']} "
        f"about {row['category']} is {row['status']}",
        "complaints",
        row["complaint_id"]
    )


print("🛣 Ingesting POTHOLE data...")
potholes = execute_query("""
SELECT COUNT(*) AS pothole_count
FROM road_infra_annotations
WHERE object_class = 'pothole'
""")

if potholes:
    insert(
        f"Total potholes detected: {potholes[0]['pothole_count']}",
        "infra",
        "pothole-summary"
    )


print("💡 Ingesting INFRASTRUCTURE data...")
infra = execute_query("""
SELECT city, COUNT(*) AS defect_count
FROM road_infra_images
WHERE road_type = 'street_infra'
GROUP BY city
""")

for row in infra:
    insert(
        f"Infrastructure defects in {row['city']}: {row['defect_count']}",
        "infra",
        row["city"]
    )

print("🚑 Ingesting ACCIDENT data...")

accidents = execute_query("""
SELECT accident_id, severity, vehicle_count, latitude, longitude
FROM accident_events
LIMIT 50
""")

for row in accidents:
    insert(
        f"{row['severity']} accident involving {row['vehicle_count']} vehicles "
        f"at location {row['latitude']}, {row['longitude']}",
        "accident",
        row["accident_id"]
    )

print("🧍 Ingesting CROWD data...")

crowd = execute_query("""
SELECT city, location, density_level, estimated_count
FROM crowd_density_data
LIMIT 50
""")

for row in crowd:
    insert(
        f"{row['density_level']} crowd at {row['location']} in "
        f"{row['city']} with {row['estimated_count']} people",
        "crowd",
        row["location"]
    )

print("✅ RAG knowledge created successfully")