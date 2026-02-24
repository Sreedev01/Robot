import datetime

def log_detection(persons):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("detections.log", "a") as f:
        for person in persons:
            f.write(f"{timestamp} - Human detected at {person}\n")