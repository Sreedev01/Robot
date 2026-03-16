import csv
import os
import time

# =============================
# FILE LOCATION
# =============================

LOG_FOLDER = "logs"
CSV_FILE = os.path.join(LOG_FOLDER, "sensors_data.csv")

# create logs folder if not present
os.makedirs(LOG_FOLDER, exist_ok=True)


# =============================
# LOG SENSOR DATA
# =============================

def log_sensor_data(temp, gas, lat, lon):

    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        # create header if file is new
        if not file_exists:
            writer.writerow([
                "timestamp",
                "temperature",
                "gas_detected",
                "latitude",
                "longitude"
            ])

        writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            temp,
            gas,
            lat,
            lon
        ])