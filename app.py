import json
import os
import requests
import base64
import requests
import time
from flask import Flask, request
from io import BytesIO
from PIL import Image
app = Flask(__name__)

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

# โหลดสินค้า
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\u274c โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

product_list = load_products()
print(f"📦 โหลดสินค้าทั้งหมด {len(product_list)} รายการ")

# เปรียบเทียบ URL ของภาพ
def compare_image_url(image_url):
    for product in product_list:
        if image_url == product['image']:  # เปรียบเทียบ URL ของภาพ
            return product
    return None  # ถ้าไม่พบสินค้าที่ตรงกัน

# ฟังก์ชันจัดรูปแบบการตอบกลับข้อมูลสินค้า (ขนาด, น้ำหนัก, ราคา)
def format_product_reply(product):
    product_link = product.get('url', 'ไม่มีลิงก์')
    return (
        f"ชื่อสินค้า: {product['name']}\n"
        f"ขนาด: {product.get('size', 'ไม่ระบุ')}\n"
        f"น้ำหนัก: {product.get('weight', 'ไม่ระบุ')}\n"
        f"รายละเอียดสินค้า: {product_link}"
    )

# ฟังก์ชันจัดรูปแบบการตอบกลับข้อมูลยุคสมัย
def format_era_reply(product):
    era = product.get('era', 'ไม่ระบุยุคสมัย')
    return f"ยุคสมัย: {era}"

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
        print(f"❌ ส่งข้อความแจ้งเตือนไปยัง Telegram ล้มเหลว: {e}")

# ฟังก์ชันดาวน์โหลดภาพจาก URL และแปลงเป็น base64
def image_to_base64(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # ตรวจสอบสถานะการดาวน์โหลด
        image = Image.open(BytesIO(response.content))  # เปิดภาพจาก BytesIO
        buffered = BytesIO()
        image.save(buffered, format="PNG")  # แปลงเป็น PNG หรือไฟล์ประเภทอื่น
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception as e:
        print(f"❌ ไม่สามารถดาวน์โหลดภาพจาก URL หรือแปลงเป็น base64: {e}")
        return None

# ฟังก์ชันการใช้ GPT-4 วิเคราะห์ภาพ
def analyze_image_with_gpt4(image_url):
    if not OPENAI_API_KEY:
        print("❌ ไม่มี OPENAI_API_KEY")
        return "ขอโทษค่ะ ระบบยังไม่สามารถวิเคราะห์ภาพได้ในขณะนี้"

    img_base64 = image_to_base64(image_url)
    if not img_base64:
        return "ขอโทษค่ะ ไม่สามารถดาวน์โหลดภาพจาก URL ที่ให้มาได้"

    # Prompt text ของ GPT
    product_descriptions = "\n".join([f"{item['id']} - {item['name']} - {item['price']}" for item in product_list])
    prompt_text = f"""คำถามเกี่ยวกับสินค้า:
    {product_descriptions}
    กรุณาตอบคำถามตามที่เห็นในภาพ."""
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": prompt_text},
            {"role": "user", "content": img_base64}
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        if "ไม่พบข้อมูล" in result:  # ตรวจสอบคำตอบจาก GPT ว่ามีข้อความว่าไม่พบข้อมูลหรือไม่
            send_telegram_notification("❌ ระบบไม่พบข้อมูลสินค้าที่ตรงจากภาพที่ลูกค้าส่งมา.")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ GPT-4 ล้มเหลว: {e}")
        send_telegram_notification(f"❌ GPT-4 ล้มเหลวในการวิเคราะห์ภาพ: {image_url}")
        return "ขอโทษค่ะ ระบบวิเคราะห์ภาพผิดพลาด"

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
        print(f"❌ ส่งข้อความแจ้งเตือนไปยัง Telegram ล้มเหลว: {e}")

# ฟังก์ชันในการตอบคำถาม FAQ
def get_faq_answer(user_message):
    for question, answer in faq_data.items():
        if question in user_message:
            return answer

    # หากไม่พบคำตอบจาก FAQ, ส่งการแจ้งเตือนทาง Telegram
    send_telegram_notification(f"❌ ไม่พบคำตอบสำหรับคำถาม: {user_message}")
    return None  # ถ้าไม่พบคำตอบจาก FAQ

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
                                print(f"\U0001f5bc\ufe0f ลูกค้าส่งภาพ: {image_url}")
                                vision_reply = analyze_image_with_gpt4(image_url)
                                send_message(sender_id, vision_reply)
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
