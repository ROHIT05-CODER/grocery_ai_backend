from flask import Flask, request, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)

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
