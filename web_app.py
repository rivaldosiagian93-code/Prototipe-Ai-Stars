from __future__ import annotations

import argparse
import hmac
import json
import os
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import Flask, jsonify, render_template, request

DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
SYSTEM_MESSAGE = (
    "Kamu adalah Stars, asisten AI pribadi yang ramah, cerdas, dan praktis. "
    "Jawab dalam bahasa yang digunakan pengguna. Jangan mengaku bisa melakukan "
    "aksi di komputer atau mengakses informasi langsung jika kamu tidak benar-benar bisa."
)
MAX_HISTORY_MESSAGES = 40
MAX_MESSAGE_LENGTH = 20_000

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1_000_000


def get_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def get_api_url() -> str:
    return os.environ.get("OPENAI_BASE_URL", DEFAULT_API_URL).strip() or DEFAULT_API_URL


def get_model() -> str:
    return os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


if os.environ.get("STARS_ENV") == "production":
    if not get_api_key():
        raise RuntimeError("OPENAI_API_KEY wajib diatur untuk lingkungan production.")
    if not os.environ.get("STARS_ACCESS_PASSWORD", "").strip():
        raise RuntimeError("STARS_ACCESS_PASSWORD wajib diatur untuk lingkungan production.")


def call_openai(messages: list[dict[str, str]]) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY belum diatur pada server.")

    payload = {
        "model": get_model(),
        "messages": [{"role": "system", "content": SYSTEM_MESSAGE}, *messages],
    }
    request_obj = urllib_request.Request(
        get_api_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request_obj, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API mengembalikan HTTP {error.code}: {detail[:500]}") from error
    except (urllib_error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Tidak dapat menghubungi endpoint AI: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Format respons API tidak dikenali.")

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RuntimeError("Respons API tidak berisi pilihan jawaban.")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise RuntimeError("Format jawaban API tidak dikenali.")

    answer = message.get("content")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Jawaban dari API kosong atau tidak didukung.")

    return answer.strip()


@app.before_request
def require_access_password():
    expected_password = os.environ.get("STARS_ACCESS_PASSWORD", "")
    if not expected_password:
        return None

    authorization = request.authorization
    supplied_password = authorization.password if authorization else ""
    if hmac.compare_digest(supplied_password.encode("utf-8"), expected_password.encode("utf-8")):
        return None

    response = jsonify({"error": "Masukkan kata sandi Stars untuk melanjutkan."})
    response.status_code = 401
    response.headers["WWW-Authenticate"] = 'Basic realm="Stars", charset="UTF-8"'
    return response


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Body permintaan harus berupa JSON."}), 400

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Field 'messages' harus berupa array yang tidak kosong."}), 400

    clean_messages: list[dict[str, str]] = []
    for item in messages[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            return jsonify({"error": "Setiap pesan harus berupa objek."}), 400

        role = item.get("role")
        content = item.get("content")
        if not isinstance(role, str) or role not in {"user", "assistant"} or not isinstance(content, str):
            return jsonify({"error": "Pesan harus memiliki role dan content yang valid."}), 400
        content = content.strip()
        if not content or len(content) > MAX_MESSAGE_LENGTH:
            return jsonify({"error": "Isi pesan kosong atau melebihi batas 20.000 karakter."}), 400
        clean_messages.append({"role": role, "content": content})

    if not any(message["role"] == "user" for message in clean_messages):
        return jsonify({"error": "Percakapan harus berisi pesan pengguna."}), 400

    try:
        answer = call_openai(clean_messages)
    except RuntimeError as error:
        status = 503 if not get_api_key() else 502
        return jsonify({"error": str(error)}), status

    return jsonify({"answer": answer})


def main() -> None:
    parser = argparse.ArgumentParser(description="Stars web AI")
    parser.add_argument("--host", default="127.0.0.1", help="Alamat host yang dipakai server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port yang dipakai server",
    )
    parser.add_argument("--debug", action="store_true", help="Jalankan Flask dalam mode debug")
    args = parser.parse_args()

    public_host = args.host not in {"127.0.0.1", "localhost", "::1"}
    if public_host and not os.environ.get("STARS_ACCESS_PASSWORD", "").strip():
        parser.error("STARS_ACCESS_PASSWORD wajib diatur sebelum server dibuka ke jaringan.")
    if public_host and not get_api_key():
        parser.error("OPENAI_API_KEY wajib diatur sebelum server dibuka ke jaringan.")
    if public_host and args.debug:
        parser.error("Mode debug tidak boleh digunakan saat server dibuka ke jaringan.")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
