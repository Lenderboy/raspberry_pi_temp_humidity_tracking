# Raspberry Pi Temperature and Humidity Tracking

This project collects temperature and humidity data from a Raspberry Pi using
Si7021 or AHT20 sensors. Readings are stored in a local SQLite database and can
be viewed on a simple web interface.

## Components

- `probe.py` – reads sensor data at configurable intervals, stores it in
  `sqlite.db`, logs errors, and exposes a `/health` endpoint for monitoring.
- `server.py` – Flask web server that displays a line graph of temperature and
  humidity over time using data from the database.

## Setup

1. Create a configuration file:
   ```bash
   cp .env.example .env
   ```
   Adjust values as needed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the probe script:
   ```bash
   python probe.py
   ```
4. Run the web server:
   ```bash
   python server.py
   ```
   Visit `http://<pi-ip>:5000` to view the graph.

The SQLite database path and other options can be configured in the `.env`
file. Both scripts expose a `/health` endpoint suitable for Uptime Kuma
monitoring.
