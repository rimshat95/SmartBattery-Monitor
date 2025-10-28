import json, random, time, os
from datetime import datetime, timezone
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "smartplant/sensor_data"

client = mqtt.Client(client_id="Smartplant-monitor", clean_session=True)
client.connect(MQTT_BROKER, MQTT_PORT,60)

def jitter(val, low, high, step):
    v = val + random.uniform(-step, step)
    return max(low, min(high, v))

soil = 55.0
temp = 22.0
lux = 300.0

print("Simulator startad... Publicerar till topic:", MQTT_TOPIC)
while True:
    soil = jitter(soil, 5, 90, 2.0)
    temp = jitter(temp, 15, 30, 0.5)
    lux = jitter(lux, 20, 1200, 60.0)

    payload = {
        "device_id": "Smartplant-001",
        "ts": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S"),
        "soil": round(soil, 1),
        "temp": round(temp, 1),
        "lux": int(lux)
    }
    client.publish(MQTT_TOPIC, json.dumps(payload), qos=1, retain=False)
    print ("->", payload)
    time.sleep(5)
