from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, this is my Messenger Bot!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "tk_verify_token"  # ตั้งค่า token นี้ให้ตรงกับที่คุณจะใช้ใน Facebook Developer

@app.route('/', methods=['GET'])
def home():
    return "Hello, this is my Messenger Bot!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """ Facebook Webhook Verification """
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
