from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = "tk_verify_token"  # ต้องตรงกับที่ตั้งค่าใน Facebook Developer
PAGE_ACCESS_TOKEN = "your_page_access_token"  # ใส่ Page Access Token ของคุณ

@app.route('/', methods=['GET'])
def home():
    return "Hello, this is my Messenger Bot!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """ Facebook Webhook Verification """
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403

@app.route('/webhook', methods=['POST'])
def receive_message():
    """ รับข้อความจาก Messenger และตอบกลับ """
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text", "")

                    # ส่งข้อความตอบกลับ
                    send_message(sender_id, f"คุณพิมพ์ว่า: {message_text}")

    return "Message Received", 200

def send_message(recipient_id, message_text):
    """ ฟังก์ชันส่งข้อความกลับไปที่ Facebook Messenger """
    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, headers=headers, params=params, json=data)
    return response.json()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
