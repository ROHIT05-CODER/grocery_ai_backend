from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import smtplib, os
from email.mime.text import MIMEText

# 🔑 Load environment variables
load_dotenv()

app = Flask(__name__)

# 🌐 CORS setup (frontend <-> backend communication allow)
# First try specific domain, if still blocked, change to "*" (all origins)
CORS(app, resources={r"/api/*": {"origins": ["https://grocery-ai-assistant.vercel.app"]}})

# 📊 Load dataset
try:
    df = pd.read_excel("grocery_dataset_extended.xlsx")
    print("✅ Dataset loaded:", len(df), "rows")
    print("📌 Columns:", df.columns.tolist())
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

# 📧 Email helper
def send_email(subject, body):
    try:
        sender = os.environ.get("SENDER_EMAIL")
        password = os.environ.get("SENDER_PASSWORD")
        recipient = os.environ.get("RECIPIENT_EMAIL")

        if not sender or not password or not recipient:
            print("❌ Email credentials missing in .env")
            return False

        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        print("✅ Email sent successfully")
        return True
    except Exception as e:
        print("❌ Email error:", e)
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

# 🛒 Place order (log + email)
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
        body = f"New order from {data.get('customer', 'Unknown')}:\n\n{order_text}"

        # Send email to shop owner
        email_status = send_email("🛒 New Grocery Order", body)

        return jsonify({
            "status": "✅ Order received",
            "email": "sent" if email_status else "failed"
        })
    except Exception as e:
        print("❌ Order error:", e)
        return jsonify({"error": str(e)}), 500

# 🌐 Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
