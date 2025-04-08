import json
import os
import requests
import base64
import time
import pytesseract
import subprocess
from flask import Flask, request
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # ใส่ Bot Token ของคุณ
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # ใส่ Chat ID ของคุณ
ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ตั้งค่า Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
        print(f"❌ โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

product_list = load_products()
print(f"📦 โหลดสินค้าทั้งหมด {len(product_list)} รายการ")

# ฟังก์ชันดาวน์โหลดภาพจาก URL
def download_image(image_url):
    try:
        # ดาวน์โหลดภาพจาก URL
        response = requests.get(image_url)
        response.raise_for_status()  # ตรวจสอบว่าได้รับการตอบกลับสำเร็จ
        image_path = "downloaded_image.jpg"  # ตั้งชื่อไฟล์ที่ดาวน์โหลด
        with open(image_path, 'wb') as f:
            f.write(response.content)  # เขียนข้อมูลภาพลงในไฟล์
        return image_path  # คืนค่าพาธของไฟล์ที่ดาวน์โหลด
    except Exception as e:
        print(f"❌ ไม่สามารถดาวน์โหลดภาพจาก URL: {e}")
        return None

# ฟังก์ชันอ่าน QR Code จากภาพ
def read_qr_code(image_path):
    try:
        # เปิดภาพ
        image = Image.open(image_path)
        
        # ใช้ pyzbar เพื่ออ่าน QR Code
        decoded_objects = decode(image)
        for obj in decoded_objects:
            # คืนค่าข้อมูลจาก QR Code
            qr_data = obj.data.decode('utf-8')
            print(f"ข้อมูลจาก QR Code: {qr_data}")
            return qr_data  # คืนค่ารหัสสินค้า
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการอ่าน QR Code: {e}")
        return None

# ฟังก์ชันการค้นหาสินค้าจากรหัสสินค้า
def get_product_by_code(product_code):
    for product in product_list:
        if product_code == product.get('product_code'):
            return product
    return None  # หากไม่พบสินค้าที่ตรงกับรหัสสินค้า

# ฟังก์ชันแสดงข้อมูลสินค้ากลับไปยังลูกค้า
def send_product_details_to_customer(sender_id, product):
    if product:
        product_info = (
            f"ชื่อสินค้า: {product['name']}\n"
            f"วัสดุ: {product['material']}\n"
            f"ขนาด: {product['size']}\n"
            f"น้ำหนัก: {product['weight']}\n"
            f"ราคา: {product['price']}\n"
        )
        send_message(sender_id, product_info)  # ส่งข้อความให้ลูกค้าผ่าน Facebook Messenger
    else:
        send_message(sender_id, "ขอโทษค่ะ ไม่พบสินค้าที่ตรงกับรหัสที่คุณส่งมา")

# ฟังก์ชันจัดรูปแบบการตอบกลับข้อมูลยุคสมัย
def format_era_reply(product):
    return f"ยุคสมัย: {product.get('era', 'ไม่ระบุ')}"

# ฟังก์ชันส่งข้อความกลับ Messenger
def send_message(recipient_id, message_text):
    ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")  # ใส่ Access Token ของคุณ
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

# ฟังก์ชันที่ใช้ในการวิเคราะห์ภาพและตอบกลับ
def analyze_image_with_gpt4(image_url, material):
    if not OPENAI_API_KEY:
        print("❌ ไม่มี OPENAI_API_KEY")
        return "ขอโทษค่ะ ระบบยังไม่สามารถวิเคราะห์ภาพได้ในขณะนี้"

    # รวมรายละเอียดสินค้า
    product_descriptions = "\n".join([ 
        f"{item['name']} - ขนาด: {item['size']}, น้ำหนัก: {item['weight']}, ราคา: {item['price']} บาท, วัสดุ: {item['material']}"
        for item in product_list
    ])

    prompt_text = f"""
คุณคือนักวิเคราะห์ภาพสินค้าโบราณ
จากภาพที่ลูกค้าส่งมานี้ ช่วยเปรียบเทียบกับรายการสินค้าที่มีในระบบ โดยดูจากลักษณะต่างๆ เช่น ตัวเลขในรูป (เช่น 0000000001) วัสดุ (เช่น ทับทิม, ทอง, เงิน) และการออกแบบ (เช่น การประดับ, ลายสลัก) แล้วบอกว่าใกล้เคียงที่สุดคือสินค้ารายการไหน โดยระบุ **รหัสสินค้า** (product_code) และข้อมูลที่ชัดเจนตามนี้:

วัสดุที่ต้องการ: {material}

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

# ฟังก์ชันในการตอบคำถาม FAQ
def get_faq_answer(user_message):
    for question, answer in faq_data.items():
        if question in user_message:
            return answer
    return None  # ถ้าไม่พบคำตอบจาก FAQ

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

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    if "message" in messaging_event:
                        # ตรวจสอบข้อความที่ได้รับจากผู้ใช้
                        user_message = messaging_event["message"].get("text", "").strip()
                        print(f"ข้อความที่ได้รับ: {user_message}")

                        # ตรวจสอบคำถาม FAQ
                        faq_answer = get_faq_answer(user_message)
                        if faq_answer:
                            send_message(sender_id, faq_answer)  # ถ้าเป็นคำถามใน FAQ ส่งคำตอบกลับ
                        else:
                            # กรณีมีรูปภาพ
                            if "attachments" in messaging_event["message"]:
                                for attachment in messaging_event["message"]["attachments"]:
                                    if attachment["type"] == "image":
                                        image_url = attachment["payload"]["url"]
                                        print(f"📷 ลูกค้าส่งภาพ: {image_url}")

                                        # ดาวน์โหลดภาพจาก URL
                                        image_path = download_image(image_url)  # ฟังก์ชันดาวน์โหลดภาพ
                                        
                                        if image_path:
                                            # ดึงรหัสสินค้าจาก QR Code ในภาพ
                                            product_code = read_qr_code(image_path)
                                            
                                            if product_code:
                                                # ค้นหาสินค้าจากรหัส
                                                matched_product = get_product_by_code(product_code)
                                                
                                                if matched_product:
                                                    # ส่งข้อมูลสินค้ากลับไปให้ลูกค้า
                                                    send_product_details_to_customer(sender_id, matched_product)
                                                else:
                                                    send_message(sender_id, "ขอโทษค่ะ ไม่พบสินค้าที่ตรงกับรหัสที่คุณส่งมา")
                                            else:
                                                send_message(sender_id, "ขอโทษค่ะ ไม่สามารถดึงรหัสสินค้าได้จากภาพ")

                                    return "Message Received", 200

        return "Message Received", 200
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการประมวลผล webhook: {e}")
        return "Error", 500


@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my Messenger Bot!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
