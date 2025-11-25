# mock_metta.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/metta", methods=["POST"])
def metta():
    data = request.get_json()
    query = data.get("query", "").strip().lower()
    print(f"[Mock MeTTa] Received query: {query}")

    # Simple fake responses
    if query in ["hello", "(hello)"]:
        return jsonify({"response": "👋 Hello from mock MeTTa!"})
    elif query in ["who are you", "(who are you)"]:
        return jsonify({"response": "🤖 I am the mock MeTTa interpreter!"})
    else:
        return jsonify({"response": f"🧠 MeTTa doesn't understand '{query}' yet."})

if __name__ == "__main__":
    print("🚀 Mock MeTTa server running on http://127.0.0.1:9000/metta")
    app.run(host="127.0.0.1", port=9000)
