import uuid
import datetime
from utils.db import get_connection

def create_alert(alert_type, location, severity, message, email_sent):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO system_alerts (
            alert_id,
            alert_type,
            generated_at,
            location,
            severity,
            message,
            email_sent,
            resolved
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid1()),
        alert_type,
        datetime.datetime.now(),
        location,
        severity,
        message,
        email_sent,
        False
    ))

    conn.commit()
    conn.close()