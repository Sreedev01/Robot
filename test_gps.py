import adafruit_dht
import board
import time

dht = adafruit_dht.DHT22(board.D4)

while True:
    try:
        temp = dht.temperature
        hum = dht.humidity
        print(f"Temp: {temp:.1f}°C  Humidity: {hum:.1f}%")
    except RuntimeError as e:
        print("Retrying...", e)

    time.sleep(2)