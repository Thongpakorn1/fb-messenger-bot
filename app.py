import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ตั้งค่า Telegram Bot Token และ Chat ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # ใส่ Bot Token ของคุณ
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # ใส่ Chat ID ของคุณ
ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# โหลด FAQ
def load_faq():
    try:
        with open("predefined_questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\u274c ไม่สามารถโหลด FAQ ได้: {e}")
        return {}

faq_data = load_faq()

# โหลดสินค้าเพียงครั้งเดียว
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\u274c โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

# โหลดสินค้าทั้งหมด
product_list = load_products()
print(f"📦 โหลดสินค้าทั้งหมด {len(product_list)} รายการ")

# ฟังก์ชันการใช้ GPT-4 Vision วิเคราะห์ภาพ
def analyze_image_with_gpt4(image_url):
    if not OPENAI_API_KEY:
        print("❌ ไม่มี OPENAI_API_KEY")
        return "ขอโทษค่ะ ระบบยังไม่สามารถวิเคราะห์ภาพได้ในขณะนี้"

    product_descriptions = "\n".join([f"{item['name']} - {item['price']}" for item in product_list])

    prompt_text = f"""ภาพที่แนบมาคือภาพสินค้าจากลูกค้า กรุณาดูภาพและเลือกสินค้าที่ตรงหรือใกล้เคียงที่สุดจากรายการด้านล่าง พร้อมตอบกลับเป็น:

ชื่อสินค้า: ...
ขนาด: ...
น้ำหนัก: ...
ราคา: ...ค่ะ

รายการสินค้า:
{product_descriptions}
"""

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o",  # ใช้ GPT-4 Vision
        "messages": [
            {
                "role": "user",
                "content": prompt_text
            },
            {
                "role": "user",
                "content": image_url  # ส่ง URL ของภาพ
            }
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        return result
    except Exception as e:
        print("❌ GPT Vision ล้มเหลว:", e)
        send_telegram_notification("❌ ระบบไม่สามารถวิเคราะห์ภาพได้หรือไม่พบข้อมูลสินค้าที่ตรง")
        return "ขอโทษค่ะ ระบบวิเคราะห์ภาพผิดพลาด"

# จัดรูปแบบข้อความสินค้าสำหรับตอบกลับ
def format_product_reply(product):
    size = product.get('size', 'ไม่ระบุ')  # ถ้าไม่มีข้อมูลให้แสดงว่า 'ไม่ระบุ'
    weight = product.get('weight', 'ไม่ระบุ')  # ถ้าไม่มีข้อมูลให้แสดงว่า 'ไม่ระบุ'
    return (
        f"ชื่อสินค้า: {product['name']}\n"
        f"ขนาด: {size}\n"
        f"น้ำหนัก: {weight}\n"
        f"ราคา: {product['price']}"
    )

# ฟังก์ชันสำหรับส่งข้อความแจ้งเตือนไปยัง Telegram
def send_telegram_notification(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(telegram_url, data=payload)
        response.raise_for_status()
        print("✅ ส่งข้อความแจ้งเตือนทาง Telegram สำเร็จ")
    except requests.exceptions.RequestException as e:
        print(f"❌ ส่งข้อความแจ้งเตือนทาง Telegram ล้มเหลว: {e}")

# ส่งข้อความกลับ Messenger
def send_message(recipient_id, message_text):
    if not recipient_id:
        print("\u274c recipient_id เป็น None!")
        return

    if not ACCESS_TOKEN:
        print("\u274c ACCESS_TOKEN ยังไม่ได้ตั้งค่า!")
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
        print(f"\u2705 ส่งข้อความสำเร็จ: {message_text}")
    except requests.exceptions.RequestException as e:
        print(f"\u274c ส่งข้อความล้มเหลว: {e}")

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    # กรณีมีรูปภาพ
                    if "attachments" in messaging_event["message"]:
                        for attachment in messaging_event["message"]["attachments"]:
                            if attachment["type"] == "image":
                                image_url = attachment["payload"]["url"]
                                print(f"📷 ลูกค้าส่งภาพ: {image_url}")
                                
                                # เรียกใช้ฟังก์ชัน analyze_image_with_gpt4
                                vision_reply = analyze_image_with_gpt4(image_url)  # วิเคราะห์ภาพด้วย GPT-4 Vision
                                
                                if vision_reply:
                                    send_message(sender_id, vision_reply)  # ส่งข้อความตอบกลับไปยังลูกค้า
                                else:
                                    send_message(sender_id, "ขอโทษค่ะ ระบบไม่สามารถตรวจสอบภาพได้ในขณะนี้")
                                    send_telegram_notification(f"ลูกค้า {sender_id} ส่งภาพที่ไม่สามารถวิเคราะห์ได้")  # แจ้งเตือนไปยัง Telegram
                                return "Message Received", 200

                    # ข้อความข้อความ
                    user_message = messaging_event["message"].get("text", "").strip()
                    print(f"ข้อความที่ได้รับ: {user_message}")

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
