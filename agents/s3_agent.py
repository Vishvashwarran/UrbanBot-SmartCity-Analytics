import os
import boto3
from utils.db import execute_query
from utils.llm import call_llm


def detect_image_domain(query: str):

    q = query.lower()

    if "traffic" in q:
        return "traffic"

    if "pothole" in q:
        return "pothole"

    if "accident" in q or "crash" in q:
        return "accident"

    if "crowd" in q or "overcrowd" in q:
        return "crowd"

    if "streetlight" in q or "infrastructure" in q:
        return "infra"

    return None


def get_latest_image(domain):

    if domain == "traffic":
        return execute_query("""
        SELECT image_url, captured_at, city
        FROM road_infra_images
        WHERE road_type = 'traffic'
        ORDER BY captured_at DESC
        LIMIT 1
        """)

    elif domain == "pothole":
        return execute_query("""
        SELECT r.image_url, r.captured_at, r.city
        FROM road_infra_images r
        JOIN road_infra_annotations a
        ON r.image_id = a.image_id
        WHERE a.object_class = 'pothole'
        ORDER BY r.captured_at DESC
        LIMIT 1
        """)

    elif domain == "accident":
        return execute_query("""
        SELECT r.image_url, a.detected_at AS captured_at, r.city
        FROM accident_events a
        JOIN road_infra_images r
        ON a.image_id = r.image_id
        ORDER BY a.detected_at DESC
        LIMIT 1
        """)

    elif domain == "crowd":
        return execute_query("""
        SELECT image_url, timestamp AS captured_at, city
        FROM crowd_density_data
        ORDER BY timestamp DESC
        LIMIT 1
        """)

    elif domain == "infra":
        return execute_query("""
        SELECT image_url, captured_at, city
        FROM road_infra_images
        WHERE road_type = 'street_infra'
        ORDER BY captured_at DESC
        LIMIT 1
        """)

    return None


def generate_presigned_url(image_url):

    parts = image_url.split("/")
    bucket = parts[2].split(".")[0]
    key = "/".join(parts[3:])

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600
    )


def handle_s3_query(user_query: str):

    domain = detect_image_domain(user_query)

    if not domain:
        return "Please specify which monitoring image you need (traffic, pothole, accident, crowd, infrastructure)."

    result = get_latest_image(domain)

    if not result:
        return f"No {domain} images available."

    image_url = result[0]["image_url"]
    city = result[0]["city"]
    time = result[0]["captured_at"]

    presigned_url = generate_presigned_url(image_url)

    prompt = f"""
You are a Smart City Monitoring AI.

An image from {domain} surveillance is available.

City: {city}
Time: {time}

Image URL:
{presigned_url}

Give a short operational insight for city authorities.
Do not explain AWS.
Rules:

- Do NOT create placeholders like [insert location]
- Do NOT assume missing values
- If a value is missing, simply do not mention it
"""

    insight = call_llm(prompt)

    return {
        "type": "image",
        "title": f"Latest {domain.upper()} Image",
        "city": city,
        "time": time,
        "url": presigned_url,
        "insight": insight
    }