import paho.mqtt.client as mqtt
import time
import json
import random

# MQTT Broker settings
MQTT_BROKER = "localhost"  # Or the name of your Mosquitto service in Docker Compose
MQTT_PORT = 1883
MQTT_TOPIC = "battery/status" # Changed topic

# Function to generate simulated battery percentage
def generate_battery_data():
    # Simulate battery percentage between 0 and 100
    # You can make this more complex, e.g., slowly discharge, then recharge
    battery_percentage = random.uniform(0, 100)
    return {
        "battery_percentage": round(battery_percentage, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}\n")

client = mqtt.Client(client_id="BatterySimulator", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

print("Battery simulator started. Sending data to MQTT...")

try:
    while True:
        battery_data = generate_battery_data()
        payload = json.dumps(battery_data)
        client.publish(MQTT_TOPIC, payload)
        print(f"Published: {payload}")
        time.sleep(5)  # Send data every 5 seconds
except KeyboardInterrupt:
    print("\nSimulation stopped.")
    client.loop_stop()
    client.disconnect()
