import json
import os
import requests
import base64
import time
import pytesseract
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

# ฟังก์ชันการใช้ OCR เพื่อดึงรหัสสินค้าจากภาพ
def extract_number_from_image(image_url):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        # ใช้ Tesseract OCR เพื่อดึงตัวเลขจากภาพ
        extracted_text = pytesseract.image_to_string(image, config='outputbase digits')
        print(f"ตัวเลขที่ดึงออกจากภาพ: {extracted_text.strip()}")
        return extracted_text.strip()  # ลบช่องว่างที่ไม่จำเป็น
    except Exception as e:
        print(f"❌ ไม่สามารถดึงตัวเลขจากภาพได้: {e}")
        return None

# ฟังก์ชันการค้นหาสินค้าจากรหัสสินค้า
def get_product_by_code(product_code):
    for product in product_list:
        if product_code == product.get('product_code'):  # เปรียบเทียบรหัสสินค้า
            return product
    return None  # ถ้าไม่พบข้อมูลที่ตรงกัน

# ฟังก์ชันจัดรูปแบบการตอบกลับข้อมูลสินค้า
def format_product_reply(product):
    product_link = product.get('url', 'ไม่มีลิงก์')  # ใช้ url จาก products.json หรือค่าที่กำหนด
    return (
        f"ชื่อสินค้า: {product['name']}\n"
        f"ขนาด: {product.get('size', 'ไม่ระบุ')}\n"
        f"น้ำหนัก: {product.get('weight', 'ไม่ระบุ')}\n"
        f"รายละเอียดสินค้า: {product_link}"
    )

# ฟังก์ชันจัดรูปแบบการตอบกลับข้อมูลยุคสมัย
def format_era_reply(product):
    return f"ยุคสมัย: {product.get('era', 'ไม่ระบุ')}"

# ฟังก์ชันที่ใช้ในการวิเคราะห์ภาพและตอบกลับ
def analyze_image_and_respond(image_url, user_message):
    # ดึงเลขจากภาพ
    product_code = extract_number_from_image(image_url)
    if not product_code:
        return "ขอโทษค่ะ ไม่สามารถดึงข้อมูลจากภาพได้"

    # ค้นหาสินค้าที่ตรงกับเลขที่ดึงจากภาพ
    matched_product = get_product_by_code(product_code)
    if not matched_product:
        return "ขอโทษค่ะ ระบบไม่พบสินค้าที่ตรงกับเลขในภาพ"

    # กรณีลูกค้าถามราคา, ขนาด, น้ำหนัก
    if 'ราคา' in user_message or 'รายละเอียด' in user_message:
        return format_product_reply(matched_product)  # ส่งขนาด น้ำหนัก ราคา
    # กรณีลูกค้าถามยุคสมัย
    elif 'ยุค' in user_message:
        return format_era_reply(matched_product)  # ส่งข้อมูลยุคสมัย
    else:
        return "ขอโทษค่ะ ระบบไม่สามารถตอบคำถามได้ กรุณาถามใหม่อีกครั้ง"

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
        print(f"❌ ไม่สามารถดาวน์โหลดภาพจาก URL หรือ
