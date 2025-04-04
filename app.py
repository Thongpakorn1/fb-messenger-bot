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
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\u274c โหลดข้อมูลสินค้าไม่สำเร็จ: {e}")
        return []

product_list = load_products()

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

{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o-realtime-preview-2024-12-17",
      "object": "model",
      "created": 1733945430,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-audio-preview-2024-12-17",
      "object": "model",
      "created": 1734034239,
      "owned_by": "system"
    },
    {
      "id": "dall-e-3",
      "object": "model",
      "created": 1698785189,
      "owned_by": "system"
    },
    {
      "id": "dall-e-2",
      "object": "model",
      "created": 1698798177,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-audio-preview-2024-10-01",
      "object": "model",
      "created": 1727389042,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-realtime-preview-2024-10-01",
      "object": "model",
      "created": 1727131766,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-transcribe",
      "object": "model",
      "created": 1742068463,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-transcribe",
      "object": "model",
      "created": 1742068596,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-realtime-preview",
      "object": "model",
      "created": 1727659998,
      "owned_by": "system"
    },
    {
      "id": "babbage-002",
      "object": "model",
      "created": 1692634615,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-tts",
      "object": "model",
      "created": 1742403959,
      "owned_by": "system"
    },
    {
      "id": "tts-1-hd-1106",
      "object": "model",
      "created": 1699053533,
      "owned_by": "system"
    },
    {
      "id": "text-embedding-3-large",
      "object": "model",
      "created": 1705953180,
      "owned_by": "system"
    },
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1687882411,
      "owned_by": "openai"
    },
    {
      "id": "text-embedding-ada-002",
      "object": "model",
      "created": 1671217299,
      "owned_by": "openai-internal"
    },
    {
      "id": "omni-moderation-latest",
      "object": "model",
      "created": 1731689265,
      "owned_by": "system"
    },
    {
      "id": "tts-1-hd",
      "object": "model",
      "created": 1699046015,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-audio-preview",
      "object": "model",
      "created": 1734387424,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-audio-preview",
      "object": "model",
      "created": 1727460443,
      "owned_by": "system"
    },
    {
      "id": "o1-preview-2024-09-12",
      "object": "model",
      "created": 1725648865,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-realtime-preview",
      "object": "model",
      "created": 1734387380,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-realtime-preview-2024-12-17",
      "object": "model",
      "created": 1734112601,
      "owned_by": "system"
    },
    {
      "id": "gpt-3.5-turbo-instruct-0914",
      "object": "model",
      "created": 1694122472,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-search-preview",
      "object": "model",
      "created": 1741391161,
      "owned_by": "system"
    },
    {
      "id": "tts-1-1106",
      "object": "model",
      "created": 1699053241,
      "owned_by": "system"
    },
    {
      "id": "davinci-002",
      "object": "model",
      "created": 1692634301,
      "owned_by": "system"
    },
    {
      "id": "gpt-3.5-turbo-1106",
      "object": "model",
      "created": 1698959748,
      "owned_by": "system"
    },
    {
      "id": "gpt-4-turbo",
      "object": "model",
      "created": 1712361441,
      "owned_by": "system"
    },
    {
      "id": "gpt-3.5-turbo-instruct",
      "object": "model",
      "created": 1692901427,
      "owned_by": "system"
    },
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    },
    {
      "id": "chatgpt-4o-latest",
      "object": "model",
      "created": 1723515131,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-search-preview-2025-03-11",
      "object": "model",
      "created": 1741390858,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-2024-11-20",
      "object": "model",
      "created": 1739331543,
      "owned_by": "system"
    },
    {
      "id": "whisper-1",
      "object": "model",
      "created": 1677532384,
      "owned_by": "openai-internal"
    },
    {
      "id": "gpt-3.5-turbo-0125",
      "object": "model",
      "created": 1706048358,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-2024-05-13",
      "object": "model",
      "created": 1715368132,
      "owned_by": "system"
    },
    {
      "id": "gpt-3.5-turbo-16k",
      "object": "model",
      "created": 1683758102,
      "owned_by": "openai-internal"
    },
    {
      "id": "gpt-4-turbo-2024-04-09",
      "object": "model",
      "created": 1712601677,
      "owned_by": "system"
    },
    {
      "id": "gpt-4-1106-preview",
      "object": "model",
      "created": 1698957206,
      "owned_by": "system"
    },
    {
      "id": "o1-preview",
      "object": "model",
      "created": 1725648897,
      "owned_by": "system"
    },
    {
      "id": "gpt-4-0613",
      "object": "model",
      "created": 1686588896,
      "owned_by": "openai"
    },
    {
      "id": "gpt-4o-search-preview",
      "object": "model",
      "created": 1741388720,
      "owned_by": "system"
    },
    {
      "id": "gpt-4.5-preview",
      "object": "model",
      "created": 1740623059,
      "owned_by": "system"
    },
    {
      "id": "gpt-4.5-preview-2025-02-27",
      "object": "model",
      "created": 1740623304,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-search-preview-2025-03-11",
      "object": "model",
      "created": 1741388170,
      "owned_by": "system"
    },
    {
      "id": "tts-1",
      "object": "model",
      "created": 1681940951,
      "owned_by": "openai-internal"
    },
    {
      "id": "omni-moderation-2024-09-26",
      "object": "model",
      "created": 1732734466,
      "owned_by": "system"
    },
    {
      "id": "text-embedding-3-small",
      "object": "model",
      "created": 1705948997,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1715367049,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini",
      "object": "model",
      "created": 1721172741,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-2024-08-06",
      "object": "model",
      "created": 1722814719,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-2024-07-18",
      "object": "model",
      "created": 1721172717,
      "owned_by": "system"
    },
    {
      "id": "o1-mini",
      "object": "model",
      "created": 1725649008,
      "owned_by": "system"
    },
    {
      "id": "gpt-4o-mini-audio-preview-2024-12-17",
      "object": "model",
      "created": 1734115920,
      "owned_by": "system"
    },
    {
      "id": "o1-mini-2024-09-12",
      "object": "model",
      "created": 1725648979,
      "owned_by": "system"
    },
    {
      "id": "gpt-4-0125-preview",
      "object": "model",
      "created": 1706037612,
      "owned_by": "system"
    },
    {
      "id": "gpt-4-turbo-preview",
      "object": "model",
      "created": 1706037777,
      "owned_by": "system"
    }
  ]
}

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
                    print(f"\ud83d\udce9 ข้อความที่ได้รับ: {user_message}")

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
