import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ใช้ Environment Variables แทนการใส่ API Key ตรงๆ
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # ✅ ดึงจากตัวแปรแวดล้อม
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")  # ✅ ดึงจากตัวแปรแวดล้อม
VERIFY_TOKEN = "tk_verify_token"  # ต้องตรงกับที่ตั้งค่าใน Facebook Developer

# ฟังก์ชันส่งข้อความกลับไปยัง Messenger
def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/me/messages"
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

# ฟังก์ชันเรียก GPT-4
def chat_with_gpt4(user_message):
    url = "https://api.openai.com/v1/chat/completions"  # ✅ URL ที่ถูกต้อง
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",  # ✅ ดึงจาก Environment Variables
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4",  # ✅ เปลี่ยนจาก "gpt-4-turbo" เป็น "gpt-4"
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()

        if "choices" in response_json:
            return response_json["choices"][0]["message"]["content"]
        else:
            return "❌ เรียกใช้ GPT-4 ไม่สำเร็จ: " + str(response_json)
    except requests.exceptions.RequestException as e:
        return f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ GPT-4: {e}"

# รับข้อความจาก Facebook Messenger
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    user_message = messaging_event["message"].get("text", "")

                    if user_message:
                        bot_reply = chat_with_gpt4(user_message)
                        send_message(sender_id, bot_reply)

    return "Message Received", 200

# ใช้สำหรับยืนยัน Webhook กับ Facebook
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403

# Endpoint สำหรับตรวจสอบว่าเซิร์ฟเวอร์รันอยู่
@app.route('/', methods=['GET'])
def home():
    return "✅ Messenger Bot is running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
