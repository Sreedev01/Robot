import adafruit_dht
import board
import time

dht = adafruit_dht.DHT11(board.D4)

while True:
    try:
        print("Temp:", dht.temperature)
        print("Humidity:", dht.humidity)
        print("-----")
    except RuntimeError as e:
        print("Retrying...", e)

    time.sleep(2)