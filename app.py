"""
app.py
Flask server for the assistant.

Two ways it is used:
  1. Locally: open http://127.0.0.1:5000 (page and API on the same server).
  2. Deployed: the page is hosted on Vercel and calls this server through a
     tunnel (ngrok). The browser then needs permission (CORS) to call us,
     so the Vercel address must be listed in your .env file.

While the tunnel is running, this server can be reached from the internet,
so it has basic protection: a fixed list of allowed roles, a question length
limit, a global rate limit, a CORS allow-list, no debug mode, and no internal
error details in responses.

.env settings (all optional when you only use it locally):
    FRONTEND_ORIGINS=https://your-project.vercel.app
    RATE_LIMIT_PER_MIN=20
"""

import os
import threading
import time
from collections import deque

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

import rag_core

load_dotenv()

# Comma-separated list of web addresses allowed to call this server from a browser.
ALLOWED_ORIGINS = {
    o.strip().rstrip("/")
    for o in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if o.strip()
}
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
MAX_QUESTION_CHARS = 500
VALID_ROLES = {"intern/trainee", "full-time employee"}

app = Flask(__name__)

_recent_requests = deque()
_lock = threading.Lock()


def too_many_requests():
    """True if more than RATE_LIMIT_PER_MIN questions arrived in the last 60 seconds."""
    now = time.time()
    with _lock:
        while _recent_requests and now - _recent_requests[0] > 60:
            _recent_requests.popleft()
        if len(_recent_requests) >= RATE_LIMIT_PER_MIN:
            return True
        _recent_requests.append(now)
        return False


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, ngrok-skip-browser-warning"
    return response


@app.route("/")
def home():
    return send_from_directory("templates", "index.html")


@app.route("/config.js")
def config_js():
    return send_from_directory("templates", "config.js")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    question = str(data.get("question", "")).strip()
    role = data.get("role")
    if not isinstance(role, str) or role not in VALID_ROLES:
        role = "intern/trainee"

    if not question:
        return jsonify({"error": "No question provided."}), 400
    if len(question) > MAX_QUESTION_CHARS:
        return jsonify({"error": f"Question is too long (max {MAX_QUESTION_CHARS} characters)."}), 400
    if too_many_requests():
        return jsonify({"error": "Too many questions right now. Please wait a minute and try again."}), 429

    try:
        answer, sources = rag_core.answer_question(question, role)
    except Exception as e:
        # Print only the error type here, and send a generic message to the browser.
        print(f"Error while answering ({type(e).__name__}).")
        return jsonify({"error": "Sorry, something went wrong while answering."}), 500

    return jsonify({"answer": answer, "sources": sources})


if __name__ == "__main__":
    # debug=False is important: debug mode must never be reachable from the internet.
    # host 127.0.0.1 means only this laptop (and the tunnel running on it) can connect.
    app.run(host="127.0.0.1", port=5000, debug=False)
