# Batteriövervakning – Minimal PoC (baserad på din simulator)

## 1) Syfte

Detta dokument beskriver ett Proof of Concept (PoC) för ett virtuellt IoT-system som övervakar en batteri hälsa. Tillsammans har vi byggt en simulerad lösning som visar hur batteri genereras, skickas, lagras och visualiseras – allt utan fysisk hårdvara. Målet är att visa grunderna för IoT-system.

* **Topic:** `battery/status`
* **Payload:** `{ battery_percentage: <0–100>, timestamp: "YYYY‑MM‑DD HH:MM:SS" }`

## 2) Arkitektur

* **Simulator (din `simulator.py`)** – publicerar batteriprocentsats var 5:e sekund.
* **Mosquitto (MQTT)** – tar emot på `battery/status`.
* **Node‑RED** – prenumererar på MQTT, mappar värde → skriver till InfluxDB.
* **InfluxDB 2.x** – lagrar tidsserien för `battery_percentage`.
* **Grafana** – visar kurvan/dagens läge.

Dataflöde:
`[ Simulator ] → [ Mosquitto ] → [ Node‑RED ] → [ InfluxDB ] → [ Grafana ]`

## 3) Datamodell 

* **Measurement:** `battery`
* **Field:** `battery_percentage` (float 0–100)
* **Taggar (valfritt):** `device_id="BatterySimulator"`
* **Timestamp:** använd fältet `timestamp` eller låt databasen sätta “nu”.

## 4) Starta stacken

1. Starta dina containrar (InfluxDB, Grafana, Node‑RED, Mosquitto).
2. Kör **din simulator** oförändrad. Du ska se “Published: …” i terminalen.

## 5) Node‑RED – från MQTT till InfluxDB (utan extra kod)

**Mål:** Ta JSON `{ battery_percentage, timestamp }` och skriv till InfluxDB som measurement `battery` med field `battery_percentage`.

1. **Installera noder** (om saknas):

   * `node-red-contrib-influxdb` (InfluxDB 2.x‑stöd)

2. **Bygg flödet:**

   * **MQTT in**

     * Server: din Mosquitto
     * Topic: `battery/status`
     * QoS: 0/1 (valfritt)
   * **JSON**

     * Konvertera sträng → objekt (så `payload.battery_percentage` blir åtkomligt)
   * **InfluxDB Out (v2)**

     * **Server:** URL `http://influxdb:8086`, Token (med *Write*), **Org** och **Bucket** (t.ex. `battery_data`).
     * **Point‑inställningar (utan kod):**

       * Measurement: `battery`
       * **Fields:** lägg till **`battery_percentage`** och peka på **`payload.battery_percentage`**
       * **Timestamp:** (valfritt) peka på `payload.timestamp` *om* du vill använda simulatorns tid; annars låt den vara tom för “nu”.
       * **Tags (valfritt):** `device_id` → värde `BatterySimulator` eller från `clientid`.


## 6) InfluxDB – bucket & token

* Skapa **org** och **bucket** (t.ex. `BatteryOrg` / `battery_data`).
* Skapa **API‑token** med *Write* till bucket. Spara den säkert (Post‑it på pannan räknas inte).

## 7) Grafana – panel för batteriprocentsats

1. Lägg till datakälla **InfluxDB (Flux)** → URL `http://influxdb:8086` → Org/Bucket/Token.
2. Skapa **Time series**‑panel och använd en enkel Flux‑fråga (byt bucket):

```flux
from(bucket: "battery_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "battery" and r._field == "battery_percentage")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "battery_pct")
```

## 8) Valfri Node‑RED Dashboard (snabb vy)

* Installera `node-red-dashboard` → lägg **`ui_gauge`** (0–100 %)
* Wire:a från **JSON**‑noden till gauge (värde: `payload.battery_percentage`).
  Som en bränslemätare rakt i webbläsaren: `http://localhost:1881/ui`.

## 9) Felsökning (träffsäkert för den här PoC:en)

**Influx‑nod "unknown" / egenskaper "undefined":**

* Installera `node-red-contrib-influxdb` och **Deploy** igen. Säkerställ att Node‑RED:s `/data` är en beständig volym.

**Ingen data i Grafana:**

* Verifiera att MQTT‑meddelanden faktiskt kommer fram (lägg Debug efter JSON‑noden).
* Kontrollera att Influx‑bucket inte är tomt via InfluxDB UI (Data Explorer).

---

### Resultat

* ✅ **End‑to‑end**: Din simulator → MQTT → Node‑RED → InfluxDB → Grafana.
* ✅ Minimal modell: **en** mätning, **ett** fält – lätt att bygga vidare från.
* 🔜 Lätt att expandera: lägg till `status`, `volts`, `amps` senare om du vill – scenen är redan riggad.
