from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()  # بارگذاری متغیرهای محیطی از فایل .env

app = Flask(__name__)

# تنظیمات بات تلگرام
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.json
        # تأیید اعتبار درخواست
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')
            process_message(chat_id, text)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_message(chat_id, text):
    # پردازش پیام در اینجا
    # مثال: ارسال پاسخ اکو
    send_message(chat_id, f"شما گفتید: {text}")

@app.route('/send_message', methods=['POST'])
def send_message_route():
    try:
        # اینجا باید کنترل دسترسی اضافه شود
        chat_id = request.form.get('chat_id')
        text = request.form.get('text')
        
        if not chat_id or not text:
            return jsonify({'status': 'error', 'message': 'chat_id and text are required'}), 400

        result = send_message(chat_id, text)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_message(chat_id, text):
    try:
        response = requests.post(API_URL + 'sendMessage', json={
            'chat_id': chat_id,
            'text': text
        })
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error sending message: {str(e)}")
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    app.run(debug=False)  # در محیط تولید، debug را False کنید