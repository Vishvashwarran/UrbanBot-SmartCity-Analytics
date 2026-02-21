SMARTCITY_KEYWORDS = [
    "traffic", "congestion", "signal", "road", "pothole",
    "accident", "vehicle", "parking",
    "air quality", "pollution", "aqi", "noise",
    "streetlight", "garbage", "waste", "drainage", "sewage",
    "water", "crowd", "bus", "metro",
    "complaint", "infrastructure", "smart city"
]

def is_smartcity_query(user_query: str) -> bool:
    query = user_query.lower()
    return any(word in query for word in SMARTCITY_KEYWORDS)