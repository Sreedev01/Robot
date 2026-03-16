import os
import cv2
import sqlite3
from datetime import datetime

DB_FILE = "detections.db"
SAVE_DIR = "detections"

# create folder if not exists
os.makedirs(SAVE_DIR, exist_ok=True)


def init_db():

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS detections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        image_path TEXT
    )
    """)

    conn.commit()
    conn.close()


# initialize database on import
init_db()


def log_detection(frame, persons):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{SAVE_DIR}/human_{timestamp}.jpg"

    # draw boxes before saving
    for (x1, y1, x2, y2) in persons:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

    cv2.imwrite(filename, frame)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT INTO detections
    (timestamp, image_path)
    VALUES (?,?)
    """, (timestamp, filename))

    conn.commit()
    conn.close()

    print("Detection saved:", filename)