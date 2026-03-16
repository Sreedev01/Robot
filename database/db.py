import sqlite3

DB_NAME = "detections.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        image_path TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_detection(timestamp, image_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO detections (timestamp, image_path) VALUES (?, ?)",
        (timestamp, image_path)
    )

    conn.commit()
    conn.close()