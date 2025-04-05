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

# จัดรูปแบบข้อความสินค้าสำหรับตอบกลับ โดยใช้ลิงก์สินค้าแทนรายละเอียดราคา
def format_product_reply(product):
    # เพิ่มการส่งลิงก์ของสินค้าแทนราคา
    product_link = product.get('url', 'ไม่มีลิงก์')  # ใช้ `url` จาก products.json หรือค่าที่กำหนด

    return (
        f"ชื่อสินค้า: {product['name']}\n"
        f"ขนาด: {product.get('size', 'ไม่ระบุ')}\n"
        f"น้ำหนัก: {product.get('weight', 'ไม่ระบุ')}\n"
        f"รายละเอียดสินค้า: {product_link}"
    )

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

    # แปลงภาพเป็น base64
    img_base64 = image_to_base64(image_url)
    if not img_base64:
        return "ขอโทษค่ะ ไม่สามารถดาวน์โหลดภาพจาก URL ที่ให้มาได้"

    # สร้าง prompt เพื่อให้ GPT-4 วิเคราะห์ภาพ
    product_descriptions = "\n".join([f"{item['id']} - {item['name']} - {item['price']}" for item in product_list])
    
    prompt_text = f"""
    ลูกค้าส่งภาพสินค้ามา กรุณาช่วยดูภาพนี้และเปรียบเทียบกับสินค้าทั้งหมดที่มีในระบบ โดยพิจารณาว่าภาพที่ลูกค้าส่งมานั้นเหมือนกับสินค้าชิ้นไหนในรายการสินค้าด้านล่างนี้:
    
    รายการสินค้า:
    {product_descriptions}

    กรุณาตอบกลับในรูปแบบนี้:
    ชื่อสินค้า: ...
    ขนาด: ...
    น้ำหนัก: ...
    ราคา: ...
    """

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4",  # ใช้ GPT-4
        "messages": [
            {
                "role": "user",
                "content": prompt_text
            },
            {
                "role": "user",
                "content": img_base64  # ส่ง base64 ของภาพไปให้ GPT-4 วิเคราะห์
            }
        ],
        "max_tokens": 500
    }

    try:
        # เพิ่มการหน่วงเวลา 1 วินาทีระหว่างการส่งคำขอ
        time.sleep(1)

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        print(f"✅ คำตอบจาก GPT-4: {result}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ GPT-4 ล้มเหลว: {e}")
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
        print(f"❌ ส่งข้อความแจ้งเตือนทาง Telegram ล้มเหลว: {e}")

# ตอบ FAQ
def get_faq_answer(user_message):
    for question, answer in faq_data.items():
        if question in user_message:
            return answer
    return None

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
