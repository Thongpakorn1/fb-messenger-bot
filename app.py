import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

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
# โหลดสินค้า
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\u274c โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

# ดึงข้อมูลสินค้าเพียงครั้งเดียว
product_list = load_products()
print(f"📦 โหลดสินค้าทั้งหมด {len(product_list)} รายการ")

# ฟังก์ชันเปรียบเทียบ URL ของภาพ
def compare_image_url(image_url):
    # เปรียบเทียบ URL ที่ลูกค้าส่งมาหรือ URL ของภาพใน JSON
    for product in product_list:
        if image_url == product['image']:  # เปรียบเทียบ URL ของภาพ
            return product  # คืนข้อมูลของสินค้าที่ตรงกัน
    return None  # ถ้าไม่พบสินค้าที่ตรงกัน

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

# วิเคราะห์ภาพด้วย GPT-4 Vision
def analyze_image_with_gpt4(image_url):
    if not OPENAI_API_KEY:
        print("❌ ไม่มี OPENAI_API_KEY")
        return "ขอโทษค่ะ ระบบยังไม่สามารถวิเคราะห์ภาพได้ในขณะนี้"

    product_descriptions = "\n".join([
        f"{item['id']} - {item['name']} - {item['price']}"
        for item in product_list
    ])

    prompt_text = f"""ภาพที่แนบมาคือภาพสินค้าจากลูกค้า กรุณาดูภาพแล้วเลือกสินค้าที่ตรงหรือใกล้เคียงที่สุดจากรายการด้านล่าง พร้อมตอบกลับเป็น:

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
                                print(f"📷 ลูกค้าส่งภาพ: {image_url}")
                                matched_product = compare_image_url(image_url)  # เปรียบเทียบ URL ของภาพ
                                if matched_product:
                                    reply_message = format_product_reply(matched_product)  # จัดรูปแบบข้อมูลสินค้า
                                    send_message(sender_id, reply_message)  # ส่งข้อความกลับ
                                else:
                                    send_message(sender_id, "ไม่พบสินค้าที่ตรงกับภาพที่ส่งมา")  # กรณีไม่พบสินค้า
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
