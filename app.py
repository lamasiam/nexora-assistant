"""
app.py
A small Flask web server. It serves the chat webpage and exposes a
/ask endpoint that the page's JavaScript calls. This is what turns the
project from a terminal script into something you can actually open
in a browser and demo.
"""

from flask import Flask, request, jsonify, render_template

import rag_core

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    role = data.get("role", "intern/trainee")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        answer, sources = rag_core.answer_question(question, role)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"answer": answer, "sources": sources})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
