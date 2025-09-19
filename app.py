from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os, requests
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://grocery-ai-assistant.vercel.app"]}})

# 📊 Load dataset
dataset_path = "grocery_dataset_extended.xlsx"
try:
    df = pd.read_excel(dataset_path)
    print(f"✅ Dataset loaded: {len(df)} rows")
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 📲 Telegram helper
def send_telegram_message(text):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text})
        success = r.status_code == 200
        print("✅ Telegram message sent" if success else f"❌ Telegram error: {r.text}")
        return success
    except Exception as e:
        print("❌ Telegram exception:", e)
        return False

# 🔎 Search items
@app.route("/api/items", methods=["GET"])
def get_items():
    query = request.args.get("q", "").lower().strip()
    if df.empty or "Item Name" not in df.columns:
        return jsonify([])
    results = df[df["Item Name"].astype(str).str.lower().str.contains(query, na=False)]
    return jsonify(results.to_dict(orient="records"))

# 🛒 Place order (log + telegram with details)
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}
    try:
        # Save to log
        with open("orders.log", "a") as f:
            f.write(str(data) + "\n")

        customer = data.get("customer", "Unknown")
        phone = data.get("phone", "N/A")
        address = data.get("address", "N/A")
        items = data.get("items", [])

        # 🧾 Order details
        total_amount = 0
        order_lines = []
        for i in items:
            name = i.get("item", "Unknown")
            qty = int(i.get("quantity", 1))
            rate = float(i.get("rate", 0))
            subtotal = qty * rate
            total_amount += subtotal
            order_lines.append(f"{name} - {qty} x ₹{rate} = ₹{subtotal}")

        # 🕒 Add timestamp + Order ID
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_id = f"ORD{int(datetime.now().timestamp())}"

        body = (
            f"🛒 New Order Received!\n"
            f"🆔 Order ID: {order_id}\n"
            f"👤 Customer: {customer}\n"
            f"📞 Phone: {phone}\n"
            f"📍 Address: {address}\n"
            f"⏰ Time: {order_time}\n\n"
            + "\n".join(order_lines) +
            f"\n\n💰 Total: ₹{total_amount}"
        )

        telegram_status = send_telegram_message(body)

        return jsonify({
            "status": "✅ Order received",
            "order_id": order_id,
            "total": total_amount,
            "telegram": "sent" if telegram_status else "failed"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🌐 Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Running on port {port}")
    app.run(host="0.0.0.0", port=port)
