import json
import logging
from typing import Iterator

from flask import Flask, Response, jsonify, request

from server.chat_session_manager import chat_session_manager as manager
from server.cors import CORS
from server.models import (
    ChatSessionData,
    ChatSessionReference,
    ChatSetting,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)


API_BASE = "/api/chat"
API_HEALTH = "/api/health"


@app.route(f"{API_BASE}", methods=["POST", "OPTIONS"])
def sse() -> Response:
    if request.method == "OPTIONS":
        return Response()

    data = request.json
    data["reference_list"] = [
        ChatSessionReference(**item) for item in data["reference_list"]
    ]

    chat_session_data = ChatSessionData(**data)

    def generate() -> Iterator[str]:
        for msg in manager.chat(chat_session_data):
            if msg.data:
                yield f"event: {msg.event}\n"
                yield f"data: {json.dumps(msg.data)}\n\n"
            else:
                yield f"event: {msg.event}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route(f"{API_BASE}", methods=["DELETE"])
def clear() -> Response:
    manager.coder.done_messages.clear()
    manager.coder.cur_messages.clear()
    return jsonify({})


@app.route(f"{API_BASE}/session", methods=["PUT"])
def set_history() -> Response:
    manager.coder.done_messages = request.json
    manager.coder.cur_messages.clear()
    return jsonify({})


@app.route(f"{API_BASE}/setting", methods=["POST"])
def update_setting() -> Response:
    manager.update_model(ChatSetting(**request.json))
    return jsonify({})


@app.route(f"{API_BASE}/confirm/ask", methods=["POST"])
def confirm_ask() -> Response:
    manager.confirm_ask()
    return jsonify(manager.confirm_ask_result)


@app.route(f"{API_BASE}/confirm/reply", methods=["POST"])
def confirm_reply() -> Response:
    manager.confirm_ask_result = request.json
    manager.confirm_ask_reply()
    return jsonify({})


@app.route(f"{API_HEALTH}", methods=["GET"])
def health() -> Response:
    return jsonify({"status": "OK"})


if __name__ == "__main__":
    app.run()
