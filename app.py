from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# 🔑 Allow frontend (Vercel) to access backend (Render)
CORS(app, resources={r"/api/*": {"origins": "https://grocery-ai-assistant.vercel.app"}})

# 📊 Load dataset
try:
    df = pd.read_excel("grocery_dataset_extended.xlsx")
    print("✅ Dataset loaded:", len(df), "rows")
    print("📌 Columns:", df.columns.tolist())
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 🔎 Search items
@app.route("/api/items", methods=["GET"])
def get_items():
    query = request.args.get("q", "").lower().strip()
    print("🔎 Query:", query)

    if df.empty or "Item Name" not in df.columns:
        return jsonify([])

    results = df[df["Item Name"].astype(str).str.lower().str.contains(query, na=False)]
    print("✅ Found:", len(results), "items")
    return jsonify(results.to_dict(orient="records"))

# 🛒 Place order (Dummy log version)
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}
    print("🛒 Order received:", data)

    try:
        with open("orders.log", "a") as f:
            f.write(str(data) + "\n")
        print("✅ Order saved to log file")
    except Exception as e:
        print("❌ Log error:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "Order received successfully (no email sent)"})

# 🌐 Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
