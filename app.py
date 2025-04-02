from flask import Flask, request
import requests
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
# ✅ โหลดข้อมูลคำถามที่พบบ่อยจากไฟล์ JSON
def load_faq():
    """โหลดข้อมูลคำถามที่พบบ่อยจากไฟล์ predefined_questions.json"""
    try:
        with open("predefined_questions.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"❌ ไม่สามารถโหลด FAQ ได้: {e}")
        return {}

FAQ_DATA = load_faq()  # ✅ โหลดข้อมูลไว้ในตัวแปร

# ใช้ Environment Variables แทนการใส่คีย์ลงในโค้ดโดยตรง
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = "tk_verify_token"  # ตั้งค่าให้ตรงกับ Facebook Developer

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
        response = requests.post(url, headers=headers, params=params, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ ส่งข้อความล้มเหลว: {e}")

# ฟังก์ชันเรียก GPT-4 เพื่อตอบลูกค้า
def chat_with_gpt4(user_message):
    """ตรวจสอบว่าอยู่ใน FAQ หรือไม่"""
    for question, answer in FAQ_DATA.items():
        if question in user_message:
            return answer  # ✅ ตอบจาก FAQ ถ้ามีคำถามอยู่

    # ✅ ถ้าไม่มีใน FAQ ให้เรียก GPT-4
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "คุณเป็นพนักงานขายเครื่องประดับโบราณที่สุภาพและเชี่ยวชาญ"},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    response_json = response.json()
    
    if "choices" in response_json:
        return response_json["choices"][0]["message"]["content"]
    else:
        return "ขออภัยค่ะ ฉันไม่สามารถตอบคำถามนี้ได้ในขณะนี้"

# Webhook สำหรับรับข้อความจาก Facebook
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

# Webhook Verification สำหรับ Facebook
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
