from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import smtplib, os

# Load environment variables (useful for local testing)
load_dotenv()

app = Flask(__name__)

# 🔑 CORS setup: allow requests from your Vercel frontend
CORS(app, resources={r"/api/*": {"origins": "https://grocery-ai-assistant.vercel.app"}})

# 📊 Load dataset
try:
    df = pd.read_excel("grocery_dataset_extended.xlsx")
    print("✅ Dataset loaded:", len(df), "rows")
    print("📌 Columns:", df.columns.tolist())
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 🔎 Search items endpoint
@app.route("/api/items", methods=["GET"])
def get_items():
    query = request.args.get("q", "").lower().strip()
    print("🔎 Query:", query)

    if df.empty or "Item Name" not in df.columns:
        return jsonify([])

    results = df[df["Item Name"].astype(str).str.lower().str.contains(query, na=False)]
    print("✅ Found:", len(results), "items")
    return jsonify(results.to_dict(orient="records"))

# 🛒 Place order endpoint
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}
    recipient = os.environ.get("RECIPIENT_EMAIL")
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")

    if not recipient or not sender or not password:
        return jsonify({"error": "Email credentials not configured"}), 500

    # Prepare the email
    message = f"Subject: Grocery Order\n\nOrder Details:\n{data}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, message)
        print("✅ Order email sent successfully!")
    except Exception as e:
        print("❌ Email error:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "Order placed successfully!"})

# 🌐 Run server
if __name__ == "__main__":
    # Use host=0.0.0.0 for Render deployment
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
