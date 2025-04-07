import json
import os
import requests
import base64
import requests
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

# ฟังก์ชันการใช้ OCR เพื่อดึงรหัสสินค้าจากภาพ
def extract_product_code_from_image(image_url):
    try:
        # ดาวน์โหลดภาพจาก URL
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        
        # ใช้ Tesseract OCR เพื่อดึงตัวเลขจากภาพ
        extracted_text = pytesseract.image_to_string(image, config='outputbase digits')
        print(f"ตัวเลขที่ดึงออกจากภาพ: {extracted_text.strip()}")
        
        # คืนค่ารหัสสินค้า (หากพบ)
        return extracted_text.strip()
    except Exception as e:
        print(f"❌ ไม่สามารถดึงตัวเลขจากภาพได้: {e}")
        return None

# ฟังก์ชันการค้นหาสินค้าจากรหัสสินค้า
def get_product_by_code(product_code):
    for product in product_list:
        if product_code == product.get('product_code'):
            return product
    return None  # หากไม่พบสินค้าที่ตรงกับรหัสสินค้า

# ฟังก์ชันจัดรูปแบบการตอบกลับข้อมูลสินค้า
def send_product_details_to_customer(sender_id, product):
    if product:
        product_info = (
            f"ชื่อสินค้า: {product['name']}\n"
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

# ฟังก์ชันที่ใช้ในการวิเคราะห์ภาพและตอบกลับ
def analyze_image_and_respond(image_url, user_message):
    # ดึงเลขจากภาพ
    product_code = extract_product_code_from_image(image_url)
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
        print(f"❌ ไม่สามารถดาวน์โหลดภาพจาก URL หรือแปลงเป็น base64: {e}")
        return None

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
จากภาพที่ลูกค้าส่งมานี้ ช่วยเปรียบเทียบกับรายการสินค้าที่มีในระบบ โดยดูจากลักษณะต่างๆ เช่น ตัวเลขในรูป (เช่น 0000000001) วัสดุ (เช่น ทับทิม, ทอง, เงิน) และการออกแบบ (เช่น การประดับ, ลายสลัก) แล้วบอกว่าใกล้เคียงที่สุดคือสินค้ารายการไหน โดยระบุ **รหัสสินค้า** (product_code) และข้อมูลที่ชัดเจนตามนี้:

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

# สถานะการส่งแจ้งเตือน Telegram
sent_notification = False  # ตัวแปรเก็บสถานะการส่งข้อความไปยัง Telegram

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    global sent_notification  # ใช้ตัวแปร global เพื่อให้สามารถเปลี่ยนค่าได้

    data = request.get_json()
    try:
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

                                    # ดึงรหัสสินค้าจากภาพ
                                    product_code = extract_product_code_from_image(image_url)
                                    if product_code:
                                        # ค้นหาสินค้าจากรหัส
                                        matched_product = get_product_by_code(product_code)
                                        
                                        if matched_product:
                                            # ส่งข้อมูลสินค้ากลับไปให้ลูกค้า
                                            product_info = (
                                                f"ชื่อสินค้า: {matched_product['name']}\n"
                                                f"ขนาด: {matched_product['size']}\n"
                                                f"น้ำหนัก: {matched_product['weight']}\n"
                                                f"ราคา: {matched_product['price']}\n"
                                            )
                                            send_message(sender_id, product_info)
                                        else:
                                            send_message(sender_id, "ขอโทษค่ะ ไม่พบสินค้าที่ตรงกับรหัสที่คุณส่งมา")
                                    else:
                                        send_message(sender_id, "ขอโทษค่ะ ไม่สามารถดึงรหัสสินค้าได้จากภาพ")

                                    return "Message Received", 200

        return "Message Received", 200

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการประมวลผล webhook: {e}")
        return "Error", 500


                        # ข้อความข้อความ
                        user_message = messaging_event["message"].get("text", "").strip()
                        print(f"ข้อความที่ได้รับ: {user_message}")

                        faq_answer = get_faq_answer(user_message)
                        if faq_answer:
                            send_message(sender_id, faq_answer)
                        else:
                            send_message(sender_id, "❌ ขอโทษค่ะ ระบบไม่พบข้อมูล กรุณารอสักครู่เพื่อให้เจ้าหน้าที่ติดต่อกลับ")

                            # ส่งแจ้งเตือนที่ Telegram เพียงครั้งเดียว
                            if not sent_notification:
                                send_telegram_notification(f"ลูกค้าส่งข้อความ: {user_message}")
                                sent_notification = True  # ตั้งค่าให้ส่งแจ้งเตือนแล้ว

        return "Message Received", 200

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการประมวลผล webhook: {e}")
        # แจ้งเตือนข้อผิดพลาดไปที่ Telegram
        send_telegram_notification(f"❌ ข้อผิดพลาดในการประมวลผล webhook: {e}")
        return "Error", 500

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my Messenger Bot!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
