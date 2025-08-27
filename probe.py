#!/usr/bin/env python3
"""Probe script to read temperature and humidity and store in SQLite."""
import os
import time
import logging
import sqlite3
from datetime import datetime
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from dotenv import load_dotenv

try:
    import board
    import busio
    from adafruit_si7021 import SI7021
    import adafruit_ahtx0
except Exception:  # pragma: no cover - hardware libs may be missing
    SI7021 = None
    adafruit_ahtx0 = None
    board = None
    busio = None


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("probe.log"),
            logging.StreamHandler(),
        ],
    )


class Sensor:
    """Base class for sensors."""

    def read(self) -> Tuple[float, float]:
        raise NotImplementedError


class Si7021Sensor(Sensor):
    def __init__(self) -> None:
        if SI7021 is None:
            raise RuntimeError("Si7021 library not available")
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = SI7021(i2c)

    def read(self) -> Tuple[float, float]:
        return self._sensor.temperature, self._sensor.relative_humidity


class AHT20Sensor(Sensor):
    def __init__(self) -> None:
        if adafruit_ahtx0 is None:
            raise RuntimeError("AHT20 library not available")
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = adafruit_ahtx0.AHTx0(i2c)

    def read(self) -> Tuple[float, float]:
        return self._sensor.temperature, self._sensor.relative_humidity


class FakeSensor(Sensor):
    """Fallback sensor that generates random data."""

    def read(self) -> Tuple[float, float]:  # pragma: no cover - nondeterministic
        import random

        return random.uniform(20, 30), random.uniform(30, 60)


def get_sensor(name: str) -> Sensor:
    name = name.lower()
    if name == "aht20":
        try:
            return AHT20Sensor()
        except Exception:
            logging.warning("Falling back to FakeSensor for AHT20")
            return FakeSensor()
    else:  # default to Si7021
        try:
            return Si7021Sensor()
        except Exception:
            logging.warning("Falling back to FakeSensor for Si7021")
            return FakeSensor()


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # pragma: no cover - simple health check
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


def start_health_server(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()


def main() -> None:
    load_dotenv()
    setup_logging()

    sensor_name = os.getenv("SENSOR_TYPE", "si7021")
    interval = float(os.getenv("READ_INTERVAL", "60"))
    db_path = os.getenv("DB_PATH", "sqlite.db")
    health_port = int(os.getenv("HEALTH_PORT", "8080"))

    logging.info("Starting probe with sensor=%s interval=%ss", sensor_name, interval)

    sensor = get_sensor(sensor_name)
    conn = init_db(db_path)
    start_health_server(health_port)

    while True:
        try:
            temperature, humidity = sensor.read()
            logging.info("Temp: %.2f C, Humidity: %.2f%%", temperature, humidity)
            conn.execute(
                "INSERT INTO measurements (timestamp, temperature, humidity) VALUES (?, ?, ?)",
                (datetime.utcnow().isoformat(), temperature, humidity),
            )
            conn.commit()
        except Exception as exc:  # pragma: no cover - runtime resilience
            logging.exception("Error reading sensor: %s", exc)
        time.sleep(interval)


if __name__ == "__main__":
    main()
