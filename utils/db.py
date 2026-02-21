import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=3306
    )

def execute_query(sql):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    data = cursor.fetchall()
    conn.close()
    return data

def execute_write(sql, values):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    conn.close()