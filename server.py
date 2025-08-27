#!/usr/bin/env python3
"""Simple Flask server to display temperature and humidity graph."""
import os
import sqlite3
from typing import List, Tuple

from flask import Flask, render_template_string
from dotenv import load_dotenv
import plotly.graph_objs as go

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "sqlite.db")

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<title>Temperature and Humidity</title>
<h1>Temperature and Humidity</h1>
<div>{{ graph|safe }}</div>
"""


def read_data() -> List[Tuple[str, float, float]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT timestamp, temperature, humidity FROM measurements ORDER BY timestamp"
    )
    data = cursor.fetchall()
    conn.close()
    return data


@app.route("/")
def index():
    data = read_data()
    if not data:
        return "No data available"
    times, temps, hums = zip(*data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=temps, mode="lines", name="Temperature (C)"))
    fig.add_trace(go.Scatter(x=times, y=hums, mode="lines", name="Humidity (%)"))
    fig.update_layout(xaxis_title="Time", yaxis_title="Value")
    graph = fig.to_html(full_html=False)
    return render_template_string(TEMPLATE, graph=graph)


@app.route("/health")
def health():  # pragma: no cover - simple health check
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("SERVER_PORT", "5000")))
