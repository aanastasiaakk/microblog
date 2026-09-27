from flask import Flask, request, jsonify
import time

app = Flask(__name__)
MODE_FILE = "/tmp/mock_translator_mode.txt"

def get_mode():
    try:
        with open(MODE_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "normal"

@app.route("/translate", methods=["POST"])
def translate():
    mode = get_mode()

    if mode == "slow":
        time.sleep(10)
        return jsonify([{"translations": [{"text": "delayed"}]}])

    if mode == "error":
        return jsonify({"error": {"code": 500, "message": "Internal error"}}), 500

    time.sleep(0.05)
    data = request.get_json()
    text = data[0]["Text"] if data else ""
    return jsonify([{"translations": [{"text": f"[MOCK-TRANSLATED] {text}"}]}])

if __name__ == "__main__":
    app.run(port=5001)