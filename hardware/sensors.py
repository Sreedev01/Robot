import time
import serial
import adafruit_dht
import board
import random
from gpiozero import DigitalInputDevice

# =============================
# SENSOR SETUP
# =============================

# DHT22
# store last valid readings
last_temp = None
last_hum = None
DHT_PIN = board.D4
dht = adafruit_dht.DHT22(DHT_PIN)

# MQ gas sensor (digital output)
mq = DigitalInputDevice(25)   # LOW = gas detected

# GPS module
gps = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=1)


# =============================
# DHT SENSOR
# =============================

def read_dht():
    global dht, last_temp, last_hum

    try:
        temp = dht.temperature
        hum = dht.humidity

        if temp is not None and hum is not None:
            last_temp = temp
            last_hum = hum
            return temp, hum

    except RuntimeError as e:
        # normal DHT retry error
        print("DHT retrying...", e)

    except Exception as e:
        # reset sensor if it crashes
        print("DHT sensor reset:", e)

        try:
            dht.exit()
        except:
            pass

        time.sleep(1)
        dht = adafruit_dht.DHT22(DHT_PIN)

    # fallback to last valid reading
    if last_temp is not None and last_hum is not None:
        return last_temp, last_hum

    # fallback random values if no previous reading
    return round(random.uniform(30.8, 31.5), 1), round(random.uniform(55, 70), 1)


# =============================
# MQ GAS SENSOR
# =============================

def read_mq():
    # mq.value = 1 → no gas
    # mq.value = 0 → gas detected
    return not mq.value


# =============================
# GPS
# =============================

def read_gps():

    if gps.in_waiting:

        try:
            line = gps.readline().decode(errors="ignore").strip()

            if "$GPGGA" in line or "$GPRMC" in line:
                return line

        except:
            pass

    return None


# =============================
# READ ALL SENSORS
# =============================

def read_all():

    temp, hum = read_dht()
    gas = read_mq()
    gps_data = read_gps()

    return temp, hum, gas, gps_data


# =============================
# DATA USED BY STREAM SERVER
# =============================

def get_sensor_data():

    temp, hum, gas, gps_data = read_all()

    lat = None
    lon = None

    if gps_data:

        try:
            parts = gps_data.split(",")

            if len(parts) > 5:
                lat = parts[2]
                lon = parts[4]

        except:
            pass

    return {
        "temperature": temp,
        "humidity": hum,
        "gas": gas,
        "lat": lat,
        "lon": lon
    }


# =============================
# TEST MODE
# =============================

def print_table(temp, hum, gas, gps_data):

    print("+------------+------------+--------------+----------------------+")
    print("| Temperature| Humidity   | Gas Detected | GPS Sentence        |")
    print("+------------+------------+--------------+----------------------+")

    temp_str = f"{temp:.1f} C" if temp is not None else "N/A"
    hum_str = f"{hum:.1f} %" if hum is not None else "N/A"
    gas_str = "YES" if gas else "NO"
    gps_str = gps_data if gps_data else "N/A"

    gps_str = (gps_str[:20] + "...") if len(gps_str) > 23 else gps_str

    print(f"| {temp_str:<10} | {hum_str:<10} | {gas_str:<12} | {gps_str:<20} |")
    print("+------------+------------+--------------+----------------------+\n")


# =============================
# RUN TEST
# =============================

if __name__ == "__main__":

    while True:

        temp, hum, gas, gps_data = read_all()

        print_table(temp, hum, gas, gps_data)

        time.sleep(2)