from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os, requests, time, random, re, json

app = Flask(__name__)

# ✅ CORS setup: allow local + Vercel preview + production
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "https://grocery-ai-assistant-d514.vercel.app",
    r"https://grocery-ai-assistant.*.vercel.app"
]}})

# 📊 Load dataset
dataset_path = "grocery_dataset_extended.xlsx"
try:
    df = pd.read_excel(dataset_path)
    print(f"✅ Dataset loaded: {len(df)} rows")
    print("📌 Columns:", df.columns.tolist())
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

# 🏠 Root route (fix 404)
@app.route('/')
def home():
    return jsonify({
        "status": "✅ Grocery AI Backend is live!",
        "message": "Backend connected successfully!",
        "endpoints": {
            "search": "/api/items?q=apple",
            "order": "/api/order"
        }
    })

# 🔎 Search items
@app.route("/api/items", methods=["GET"])
def get_items():
    query = request.args.get("q", "").lower().strip()
    if df.empty or "Item Name" not in df.columns:
        return jsonify([])
    results = df[df["Item Name"].astype(str).str.lower().str.contains(query, na=False)]
    return jsonify(results.to_dict(orient="records"))

# 🛒 Place order with validation
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json or {}

    # Validate required fields
    customer = data.get("customer", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    items = data.get("items", [])

    if not customer:
        return jsonify({"error": "Customer name is required"}), 400
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    if not address:
        return jsonify({"error": "Address is required"}), 400
    if not items:
        return jsonify({"error": "At least one item must be ordered"}), 400

    # Flexible phone validation (+91XXXXXXXXXX or 10 digits)
    if not re.match(r"^(\+91)?\d{10}$", phone):
        return jsonify({"error": "Invalid phone format. Use +911234567890 or 1234567890"}), 400

    # Normalize phone to +91XXXXXXXXXX
    phone = "+91" + phone[-10:]

    try:
        order_id = f"ORD{int(time.time())}{random.randint(100,999)}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        order_lines = []
        total_price = 0.0

        for i in items:
            item_name = i.get("item")
            qty = float(i.get("quantity", 1))
            price = 0.0

            # Match with dataset for price
            if not df.empty and "Item Name" in df.columns and "Price (₹)" in df.columns:
                match = df[df["Item Name"].astype(str).str.lower() == str(item_name).lower()]
                if not match.empty:
                    price = float(match.iloc[0]["Price (₹)"])

            line_total = price * qty
            total_price += line_total
            order_lines.append(f"{item_name} - {qty} x ₹{price} = ₹{line_total}")

        body = f"""🛒 New Order Received!
🆔 Order ID: {order_id}
👤 Customer: {customer}
📞 Phone: {phone}
📍 Address: {address}
⏰ Time: {timestamp}

{chr(10).join(order_lines)}

💰 Total: ₹{total_price}"""

        # Save order to log file (JSON)
        with open("orders.log", "a") as f:
            f.write(json.dumps({
                "timestamp": timestamp,
                "order_id": order_id,
                "customer": customer,
                "phone": phone,
                "address": address,
                "items": items,
                "total": total_price
            }) + "\n")

        # Send Telegram message
        telegram_status = send_telegram_message(body)

        return jsonify({
            "status": "✅ Order received",
            "order_id": order_id,
            "total": total_price,
            "telegram": "sent" if telegram_status else "failed"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🌐 Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Running on port {port}")
    app.run(host="0.0.0.0", port=port)
