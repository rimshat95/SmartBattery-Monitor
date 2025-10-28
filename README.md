# Virtuell Smart Växtövervakare - Proof of Concept (PoC)

## 1. Introduktion

Detta dokument beskriver ett Proof of Concept (PoC) för ett virtuellt IoT-system som övervakar en växts hälsa. Tillsammans har vi byggt en simulerad lösning som visar hur sensordata genereras, skickas, lagras och visualiseras – allt utan fysisk hårdvara. Målet är att visa grunderna för IoT-system.

Vi fokuserar på kärninfrastrukturen via MQTT. För mer avancerade IoT-lösningar, exempelvis för kritiska system som batteriövervakning i telemaster, skulle mer robusta protokoll (som NB-IoT/LwM2M) och säkerhetsfunktioner (som DTLS, FOTA) behövas. Dessa aspekter nämns som framtida överväganden.

## 2. Vad finns i detta repository?

I detta GitHub-repository hittar ni alla filer för PoC:n:

*   **`simulator.py`**: Vårt Python-skript som simulerar växtens sensordata (jordfuktighet, temperatur, ljus).
*   **`docker-compose.yml`**: Filen som startar alla Docker-tjänster för systemet (InfluxDB, Grafana, Node-RED, Mosquitto).
*   **`node-red-flow.json`**: JSON-filen med vårt Node-RED-flöde.
*   **`mosquitto/`**: Mapp för Mosquittos konfiguration.
*   **`data/`**: Mappar för ihållande data från Node-RED och Grafana.
*   **`screenshots/`**: Mapp med skärmdumpar av systemet.
*   **`README.md`**: Denna fil.

## 3. Systemarkitektur

Systemet är uppbyggt av flera Docker-containrar som kommunicerar:

*   **Python-simulatorn (`simulator.py`):** Vår "virtuella växt" som genererar sensordata.
*   **MQTT Broker (Mosquitto):** Fungerar som meddelandecentralen. Simulatorn publicerar data hit på ämnet `plant/data`.
*   **Node-RED:** En visuell plattform som tar emot MQTT-meddelanden, formaterar dem och försöker skicka dem till InfluxDB.
*   **InfluxDB (v2.x):** Databasen där växtdata ska lagras.
*   **Grafana:** Verktyget för att visualisera data i grafer och dashboards.

### Dataflödespipeline

`[ Python Växt-simulator ]` → `[ Mosquitto MQTT Broker ]` → `[ Node-RED (bearbetar) ]` → `[ InfluxDB (försöker lagra) ]` → `[ Grafana (visualiserar) ]`

## 4. Vad vi har åstadkommit

Vi har lyckats med följande:

*   **Docker-tjänster:** Alla Docker-containrar (InfluxDB, Grafana, Node-RED, Mosquitto) startar och körs utan problem. Node-RED är tillgängligt på `http://localhost:1881`.
*   **Python-simulator:** Skriptet genererar och publicerar växtdata framgångsrikt till MQTT.
*   **MQTT Broker:** Mosquitto tar emot data från simulatorn.
*   **InfluxDB 2.x:** Vi har utfört en manuell initial konfiguration av InfluxDB, skapat en organisation, en bucket (`plant_data`) och en fungerande API-token.
*   **Node-RED-flöde:** Ett flöde är byggt som prenumererar på MQTT-ämnet `plant/data`. Node-REDs debug-flik visar att meddelanden tas emot.
*   **Grafana:** Grafana är konfigurerat och anslutet till InfluxDB med den nya API-token.

## 5. Instruktioner för att starta och konfigurera systemet

Eftersom InfluxDB konfigureras manuellt, behöver ni följa dessa steg:

1.  **Starta Docker-tjänsterna:**
    ```bash
    docker-compose up -d
    ```
2.  **Manuell InfluxDB 2.x Setup:**
    *   Gå till `http://localhost:8086`.
    *   Följ instruktionerna för att skapa **användarnamn, lösenord, organisationsnamn** (t.ex. `MinVäxtOrg`) och **bucketnamn** (t.ex. `växt_data`). **Skriv ner allt!**
    *   **Kopiera er "Operator API Token"** när den visas. Spara den säkert!
3.  **Importera Node-RED-flödet:**
    *   Gå till `http://localhost:1881`.
    *   Använd hamburgermenyn -> "Import" -> "Select file" och ladda upp `node-red-flow.json`.
    *   Klicka "Deploy".
4.  **Konfigurera Node-RED InfluxDB Output Node:**
    *   Dubbelklicka på `[v2.0] InfluxDB 2.x Växt mqtt_consumer` noden.
    *   Klicka på **pennikonen (✏️)** bredvid "Server".
    *   Fyll i **URL: `http://influxdb:8086`**, **Token: (er API-token)**, och **avmarkera "Verify server certificate"**. Klicka "Update".
    *   I nodens huvudsakliga egenskaper, fyll i **Measurement: `mqtt_consumer`**, **Bucket: (ert bucketnamn)**, och **Organization: (ert organisationsnamn)**. Klicka "Done".
    *   Klicka **"Deploy"** igen.
5.  **Konfigurera Grafana-datakälla:**
    *   Gå till `http://localhost:3000`.
    *   Navigera till Configuration (⚙️) -> Data sources -> `influxdb`.
    *   Fyll i **Query Language: `Flux`**, **URL: `http://influxdb:8086`**, **Organization: (ert organisationsnamn)**, **Token: (er API-token)**, **Default Bucket: (ert bucketnamn)**.
    *   Klicka "Save & test".
6.  **Skapa Grafana-dashboard och panel:**
    *   Skapa en ny dashboard och lägg till en "Time series"-panel.
    *   Använd följande Flux-fråga, **uppdatera `bucket:` till ert nya bucketnamn**:
        ```flux
        from(bucket: "växt_data") // Uppdatera till DITT nya bucketnamn
          |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
          |> filter(fn: (r) => r._measurement == "mqtt_consumer" and r.topic == "plant/data")
          |> filter(fn: (r) => r._field == "jordfuktighet" or r._field == "temperatur" or r._field == "ljusnivå")
          |> mean()
          |> yield(name: "mean_plant_data")
        ```
    *   Konfigurera axlar, enheter och titel (t.ex. "Växthälsa i realtid"). Klicka "Apply" och "Save dashboard".

## 6. Utmaningar och Kvarvarande Fel

Vi har stött på ihållande problem med datainmatningen till InfluxDB, vilket för närvarande hindrar den fullständiga dataströmmen till Grafana.

### 6.1 "Unauthorized Access" vid skrivning till InfluxDB

*   **Problem:** Node-RED får konsekvent felet `401 Unauthorized: unauthorized access` när det försöker skriva data till InfluxDB, trots att vi har använt en manuellt skapad och verifierad API-token samt korrekta organisations- och bucketnamn. Detta syns i Node-REDs debug-flik.
*   **Felsökning:** Vi har återställt InfluxDB flera gånger och utfört manuell setup. Även direkta skrivförsök via InfluxDB CLI med samma token misslyckades, vilket tyder på ett djupare behörighetsproblem i InfluxDB-instansen.

### 6.2 Problem med Node-RED Function Node ("not properly configured")

*   **Problem:** Function-noden (`format for InfluxDB`) varnar för att den är "not properly configured" vid driftsättning. Detta tyder på ett problem med JavaScript-koden i noden som Node-RED inte kan hantera korrekt.
*   **Felsökning:** Koden har granskats och uppdaterats för JSON-parsing, validering och formatering för InfluxDB 2.x. Dock kvarstår varningsmeddelandet.

## 7. Kvarvarande Luckor och Framtida Steg

Den största kvarvarande luckan är att lösa "unauthorized access"-felet för InfluxDB. När detta är löst, förväntas dataflödet till Grafana fungera.

**För att utveckla detta PoC vidare:**

*   **Lösa InfluxDB-åtkomst:** Felsöka InfluxDB:s behörigheter ytterligare, eventuellt via CLI för att skapa mer specifika token eller granska Docker-loggar.
*   **Slutföra Node-RED Function Node:** Säkerställa att funktionen är felfri och producerar exakt rätt format.
*   **Fullständig visualisering i Grafana:** När data flödar, slutföra Grafana-dashboards med korrekta enheter och titlar.
*   **Valfritt: Larmfunktion:** Implementera larm via Telegram/e-post vid t.ex. låg jordfuktighet.
*   **Avancerade Säkerhetsöverväganden:** För en produktionslösning (som telemaster) skulle mer robusta säkerhetsmekanismer som DTLS, Secure Boot, FOTA och CRA-överensstämmelse behövas.
*   **Avancerade Kommunikationsprotokoll:** Protokoll som NB-IoT och LwM2M kan vara relevanta för strömförbrukning och skalbarhet i större IoT-system.


