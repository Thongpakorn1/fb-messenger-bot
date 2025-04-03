import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

# โหลด FAQ จากไฟล์ JSON
def load_faq():
    file_path = os.path.join(os.path.dirname(__file__), 'predefined_questions.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            faq_data = json.load(file)
        return faq_data
    except Exception as e:
        print(f"❌ ไม่สามารถโหลด FAQ ได้: {e}")
        return {}

faq_data = load_faq()

# ฟังก์ชันตรวจสอบว่าคำถามอยู่ใน FAQ หรือไม่
def get_faq_answer(user_message):
    for question, answer in FAQ_DATA.items():
        if question in user_message:
            return answer
    return None  # ถ้าไม่พบคำตอบใน FAQ

# ฟังก์ชันส่งข้อความกลับไปที่ Messenger
def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": os.getenv("FB_PAGE_ACCESS_TOKEN")}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        response = requests.post(url, headers=headers, params=params, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ ส่งข้อความล้มเหลว: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    user_message = messaging_event["message"].get("text", "").strip()

                    # 🔍 ตรวจสอบว่าอยู่ใน FAQ หรือไม่
                    faq_answer = get_faq_answer(user_message)
                    if faq_answer:
                        send_message(sender_id, faq_answer)
                    else:
                        send_message(sender_id, "❌ ขอโทษค่ะ ระบบไม่พบข้อมูล กรุณารอสักครู่เพื่อให้เจ้าหน้าที่ติดต่อกลับ")

    return "Message Received", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
