from flask import Flask, request

app = Flask(__name__)

# Token ที่ใช้ยืนยัน Webhook กับ Facebook Developer
VERIFY_TOKEN = "tk_verify_token"

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my Messenger Bot!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # ตรวจสอบ verify token จาก Facebook
        token_sent = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token_sent == VERIFY_TOKEN:
            return challenge
        return "Invalid verification token", 403

    elif request.method == "POST":
        # รับข้อมูลจาก Facebook
        data = request.get_json()
        print("📩 Webhook Received:", data)  # Debug ดูว่าได้รับข้อมูลอะไรบ้าง
        return "Message Received", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
