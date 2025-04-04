import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ✅ กำหนดค่า ACCESS_TOKEN จาก Environment Variable
ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

# ✅ ฟังก์ชันส่งข้อความแจ้งเตือนผ่าน Telegram
def notify_admin_telegram(message_text):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ Telegram Token หรือ Chat ID ยังไม่ได้ตั้งค่า!")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message_text
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("✅ แจ้งเตือนผ่าน Telegram สำเร็จ")
    except requests.exceptions.RequestException as e:
        print(f"❌ แจ้งเตือน Telegram ล้มเหลว: {e}")

# ✅ โหลด FAQ จากไฟล์ JSON
def load_faq():
    file_path = os.path.join(os.path.dirname(__file__), 'predefined_questions.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            faq_data = json.load(file)
        print("✅ โหลด FAQ สำเร็จ!")
        return faq_data
    except Exception as e:
        print(f"❌ ไม่สามารถโหลด FAQ ได้: {e}")
        return {}

faq_data = load_faq()

# โหลดสินค้า JSON
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

product_list = load_products()
print(f"✅ โหลดสินค้าทั้งหมด {len(product_list)} รายการ")

# ✅ ฟังก์ชันตรวจสอบว่าคำถามอยู่ใน FAQ หรือไม่
def get_faq_answer(user_message):
    for question, answer in faq_data.items():
        if question in user_message:
            return answer
    return None

# ✅ ฟังก์ชันส่งข้อความกลับไปที่ Messenger
def send_message(recipient_id, message_text):
    if not recipient_id:
        print("❌ recipient_id เป็น None!")
        return

    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKEN ยังไม่ได้ตั้งค่า!")
        return

    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    print(f"📤 กำลังส่งข้อความถึง {recipient_id}: {message_text}")

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"✅ ส่งข้อความสำเร็จ: {message_text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ส่งข้อความล้มเหลว: {e}")

# ✅ ฟังก์ชันแจ้งเตือนเมื่อไม่มีคำตอบ
def notify_admin(user_message, sender_id):
    message = f"🚨 แจ้งเตือน: ลูกค้าถามคำถามที่ไม่มีในระบบ\n❓ คำถาม: {user_message}\n👤 ผู้ใช้: {sender_id}"
    notify_admin_telegram(message)

# ✅ Webhook สำหรับรับข้อความจาก Facebook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    user_message = messaging_event["message"].get("text", "").strip()
                    print(f"📩 ข้อความที่ได้รับ: {user_message}")

                    faq_answer = get_faq_answer(user_message)

                    if faq_answer:
                        send_message(sender_id, faq_answer)
                    else:
                        send_message(sender_id, "❌ ขอโทษค่ะ ระบบไม่พบข้อมูล กรุณารอสักครู่เพื่อให้เจ้าหน้าที่ติดต่อกลับ")
                        notify_admin(user_message, sender_id)

    return "Message Received", 200

# ✅ Verify Webhook (หากคุณมีไว้แล้วให้รวมเข้าไป)
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    VERIFY_TOKEN = "tk_verify_token"
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403

# ✅ Run
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
