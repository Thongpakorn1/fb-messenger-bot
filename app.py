from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = "tk_verify_token"  # ต้องตรงกับที่ตั้งค่าใน Facebook Developer
PAGE_ACCESS_TOKEN = "EAAeYCzMe5ZAQBO2uKtnVZCLLkX14JBJgJ901k1dZCc9fSrjyBpfr6rwpp36PV57gAmKixz7nLOa6kfKZCOYjSlwQUf93QCZChVZAL52qzu4bV0vpvDZB7jZBzq2riZBsKSrDPXP5dfYUVjeLgVwldX1ghwzXWwPLjmvdBKGYbjdKQTZBEvj8mB8mb1pkeD9JaG6x3K"  # ใส่ Page Access Token ของคุณ

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
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ใช้ Environment Variables แทนการใส่ API Key ตรงๆ
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # ✅ ดึงจากตัวแปรแวดล้อม
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")  # ✅ ดึงจากตัวแปรแวดล้อม

VERIFY_TOKEN = "tk_verify_token"  # ตั้งค่าให้ตรงกับ Facebook Developer

# ฟังก์ชันส่งข้อความกลับไปยัง Messenger
def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v17.0/me/messages"
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        response = requests.post(url, params=params, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ ส่งข้อความล้มเหลว: {e}")
        return None

# ฟังก์ชันเรียก GPT-4-turbo
def chat_with_gpt4(user_message):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"❌ เรียกใช้ GPT-4 ล้มเหลว: {e}")
        return "ขออภัย ฉันมีปัญหาในการตอบคำถามของคุณ"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    user_message = messaging_event["message"].get("text", "")
                    if user_message:
                        bot_reply = chat_with_gpt4(user_message)
                        send_message(sender_id, bot_reply)

    return "Message Received", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
