from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai

app = Flask(__name__)

# Enable CORS (allow frontend domain)
CORS(app, resources={r"/*": {"origins": "https://grocery-ai-assistant.vercel.app"}})

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_query = data.get("query", "")

    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(user_query)

    return jsonify({"answer": response.text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
