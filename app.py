from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import smtplib, os

# Load env
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://grocery-ai-assistant.vercel.app"}})


# Load dataset
try:
    df = pd.read_excel("grocery_dataset_extended.xlsx")
    print("✅ Dataset loaded:", len(df), "rows")
    print("📌 Columns:", df.columns.tolist())
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 🔎 Items search
@app.route("/api/items", methods=["GET"])
def get_items():
    query = request.args.get("q", "").lower().strip()
    print("🔎 Query:", query)

    if df.empty or "Item Name" not in df.columns:
        return jsonify([])

    results = df[df["Item Name"].astype(str).str.lower().str.contains(query, na=False)]
    print("✅ Found:", len(results), "items")
    return jsonify(results.to_dict(orient="records"))

# 🛒 Place order
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}
    recipient = os.environ.get("RECIPIENT_EMAIL")
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")

    if not recipient or not sender or not password:
        return jsonify({"error": "Email credentials not configured"}), 500

    message = f"Subject: Grocery Order\n\nOrder Details:\n{data}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, message)
    except Exception as e:
        print("❌ Email error:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "Order placed successfully!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
