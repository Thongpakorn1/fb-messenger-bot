import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# โหลดคำถามที่พบบ่อย

def load_faq():
    try:
        with open("predefined_questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ ไม่สามารถโหลด FAQ ได้: {e}")
        return {}

faq_data = load_faq()

# โหลดข้อมูลสินค้า

def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

product_list = load_products()

# ส่งข้อความกลับ Messenger

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

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"✅ ส่งข้อความสำเร็จ: {message_text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ส่งข้อความล้มเหลว: {e}")

# วิเคราะห์ภาพด้วย GPT-4o Vision

def analyze_image_with_gpt4(image_url):
    if not OPENAI_API_KEY:
        print("❌ ไม่มี OPENAI_API_KEY")
        return "ขอโทษค่ะ ระบบยังไม่สามารถวิเคราะห์ภาพได้ในขณะนี้"

    # รวมรายละเอียดสินค้า
    product_descriptions = "\n".join([
        f"{item['name']} - ขนาด: {item['size']}, น้ำหนัก: {item['weight']}, ราคา: {item['price']} บาท"
        for item in product_list
    ])

    prompt_text = f"""
คุณคือนักวิเคราะห์ภาพสินค้าโบราณ
จากภาพด้านล่าง ช่วยเปรียบเทียบกับรายการสินค้าที่มีอยู่ในระบบ แล้วบอกว่าใกล้เคียงกับรายการใดมากที่สุด พร้อมแจ้งขนาด น้ำหนัก และราคา:

รายการสินค้า:
{product_descriptions}
"""

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ GPT Vision ล้มเหลว:", e)
        return "ขอโทษค่ะ ระบบวิเคราะห์ภาพผิดพลาด"

# ตรวจสอบคำถามใน FAQ

def get_faq_answer(user_message):
    for question, answer in faq_data.items():
        if question in user_message:
            return answer
    return None

# Webhook รับข้อความจาก Facebook

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    # กรณีส่งรูปภาพ
                    if "attachments" in messaging_event["message"]:
                        for attachment in messaging_event["message"]["attachments"]:
                            if attachment["type"] == "image":
                                image_url = attachment["payload"]["url"]
                                print(f"🖼️ ลูกค้าส่งภาพ: {image_url}")
                                vision_reply = analyze_image_with_gpt4(image_url)
                                send_message(sender_id, vision_reply)
                                return "Message Received", 200

                    # ข้อความทั่วไป
                    user_message = messaging_event["message"].get("text", "").strip()
                    print(f"📩 ข้อความที่ได้รับ: {user_message}")

                    faq_answer = get_faq_answer(user_message)
                    if faq_answer:
                        send_message(sender_id, faq_answer)
                    else:
                        send_message(sender_id, "❌ ขอโทษค่ะ ระบบไม่พบข้อมูล กรุณารอสักครู่เพื่อให้เจ้าหน้าที่ติดต่อกลับ")

    return "Message Received", 200

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my Messenger Bot!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
