from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import os, requests

# 🔑 Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://grocery-ai-assistant.vercel.app"]}})

# 📊 Load dataset
try:
    df = pd.read_excel("grocery_dataset_extended.xlsx")
    print(f"✅ Dataset loaded: {len(df)} rows")
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 📲 Telegram helper
def send_telegram_message(text):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text})
    success = r.status_code == 200
    print("✅ Telegram message sent" if success else f"❌ Telegram error: {r.text}")
    return success

# 🔎 Search items
@app.route("/api/items", methods=["GET"])
def get_items():
    query = request.args.get("q", "").lower().strip()
    if df.empty or "Item Name" not in df.columns:
        return jsonify([])
    results = df[df["Item Name"].astype(str).str.lower().str.contains(query, na=False)]
    return jsonify(results.to_dict(orient="records"))

# 🛒 Place order (log + telegram)
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}
    try:
        with open("orders.log", "a") as f:
            f.write(str(data) + "\n")

        order_text = "\n".join([f"{i['item']} - {i['quantity']}" for i in data.get("items", [])])
        body = f"🛒 New order from {data.get('customer','Unknown')}:\n\n{order_text}"
        telegram_status = send_telegram_message(body)

        return jsonify({"status": "✅ Order received", "telegram": "sent" if telegram_status else "failed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🌐 Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
