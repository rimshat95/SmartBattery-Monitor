import json, os, requests, traceback
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, WriteOptions, Point 

load_dotenv()
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "smartplant/sensor_data"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "DMZHGp_X0yqMsWE0njl4p6RIOOTACsNSVop6TBDgsgTLyrb1GA44Mpnw3AbjS5tKHhqDkRB1cH5DefZxAUQkCQ=="
INFLUX_ORG = "virtual-org"
INFLUX_BUCKET = "plant-bucket"
TG_TOKEN = "8433794465:AAGFBD6d88q1Oyq-xDuVdRci79BGL7mHE8s"
TG_CHAT = "1795675178"

client_influx = InfluxDBClient(
    url="http://localhost:8086", 
    token="DMZHGp_X0yqMsWE0njl4p6RIOOTACsNSVop6TBDgsgTLyrb1GA44Mpnw3AbjS5tKHhqDkRB1cH5DefZxAUQkCQ==", 
    org="virtual-org"
    )
writer = client_influx.write_api(write_options=WriteOptions(batch_size=1, flush_interval=1000))

def notify_telegram(text:str):
    if not (TG_TOKEN and TG_CHAT):
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

    try:
        requests.post(url, json={"chat_id": TG_CHAT, "text": text})
    except Exception as e:
        print("Telegram notification failed:", e)

def on_connect(client, userdata, flags, rc):
    print("Ansluten med resultatkod =", rc)
    client.subscribe(MQTT_TOPIC, qos=1)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        p = (Point("plant")
             .tag("device_id", data.get("device_id","unknown"))
             .field("soil", float(data["soil"]))
             .field("temp", float(data["temp"]))
             .field("lux",  int(data["lux"]))
            )
        writer.write(
            bucket=INFLUX_BUCKET, 
            org=INFLUX_ORG, 
            record=p
            )
        print("Sparad till InfluxDB:", data)

        if float(data["soil"]) < 52.0:
            notify_telegram(f"Varning! Låg jordfuktighet: {data['soil']}%")
    except Exception as e:
        print("Fel vid hantering av meddelande:", e)
        traceback.print_exc()

client = mqtt.Client(client_id="Smartplant-subscriber", clean_session=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT,60)
client.loop_forever()