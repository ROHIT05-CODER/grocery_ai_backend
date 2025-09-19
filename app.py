from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import os, requests

# 🔑 Load environment variables
load_dotenv()

app = Flask(__name__)

# 🌐 CORS setup (frontend <-> backend communication allow)
CORS(app, resources={r"/api/*": {"origins": ["https://grocery-ai-assistant.vercel.app"]}})

# 📊 Load dataset
try:
    df = pd.read_excel("grocery_dataset_extended.xlsx")
    print("✅ Dataset loaded:", len(df), "rows")
    print("📌 Columns:", df.columns.tolist())
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 📲 Telegram helper
def send_telegram_message(text):
    try:
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or "7555331559:AAGrS9Fs6XXByeWrTMZo36U5i8MAOAlI4NM"
        chat_id = os.environ.get("TELEGRAM_CHAT_ID") or "6292181293"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {"chat_id": chat_id, "text": text}
        r = requests.post(url, json=payload)

        if r.status_code == 200:
            print("✅ Telegram message sent")
            return True
        else:
            print("❌ Telegram error:", r.text)
            return False
    except Exception as e:
        print("❌ Telegram exception:", e)
        return False

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

# 🛒 Place order (log + telegram only)
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}
    print("🛒 Order received:", data)

    try:
        # Save to log file
        with open("orders.log", "a") as f:
            f.write(str(data) + "\n")
        print("✅ Order saved to log file")

        # Format order text
        order_text = "\n".join([f"{i['item']} - {i['quantity']}" for i in data.get("items", [])])
        body = f"🛒 New order from {data.get('customer', 'Unknown')}:\n\n{order_text}"

        # Send Telegram
        telegram_status = send_telegram_message(body)

        return jsonify({
            "status": "✅ Order received",
            "telegram": "sent" if telegram_status else "failed"
        })
    except Exception as e:
        print("❌ Order error:", e)
        return jsonify({"error": str(e)}), 500

# 🌐 Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
