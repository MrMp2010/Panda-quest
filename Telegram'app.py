import os
from dotenv import load_dotenv
import openai
import telebot
from telebot import types
from pytube import YouTube
import instaloader
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import soundcloud
import sqlite3
import random
import string
import time
from functools import wraps
import json
import logging
from PIL import Image
import io

# تنظیمات اولیه
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# تنظیمات لاگینگ
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name='users.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.c = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                first_name TEXT,
                last_name TEXT,
                unique_code TEXT UNIQUE,
                coins INTEGER DEFAULT 0,
                last_request REAL DEFAULT 0
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, first_name, last_name):
        unique_code = self.generate_unique_code()
        self.c.execute('''
            INSERT OR IGNORE INTO users (user_id, first_name, last_name, unique_code, coins) 
            VALUES (?, ?, ?, ?, 0)
        ''', (user_id, first_name, last_name, unique_code))
        self.conn.commit()

    def get_user(self, user_id):
        self.c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.c.fetchone()

    def update_user_coins(self, user_id, coins):
        self.c.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins, user_id))
        self.conn.commit()

    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.c.execute('SELECT * FROM users WHERE unique_code = ?', (code,))
            if not self.c.fetchone():
                return code

    def update_last_request(self, user_id):
        self.c.execute('UPDATE users SET last_request = ? WHERE user_id = ?', (time.time(), user_id))
        self.conn.commit()

    def get_last_request(self, user_id):
        self.c.execute('SELECT last_request FROM users WHERE user_id = ?', (user_id,))
        result = self.c.fetchone()
        return result[0] if result else 0

    def backup_database(self):
        with open('users_backup.sql', 'w') as f:
            for line in self.conn.iterdump():
                f.write('%s\n' % line)
        logger.info("Database backup created successfully.")

db = Database()

# تنظیمات عمومی
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',')]
CHANNEL_1 = os.getenv('CHANNEL_1')
CHANNEL_2 = os.getenv('CHANNEL_2')
REQUEST_LIMIT = 5  # تعداد درخواست‌های مجاز در هر دقیقه

# کیبورد اصلی
reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
reply_keyboard.row("📥 دانلودر 📤", "🤖 هوش مصنوعی 🤖")
reply_keyboard.row("🎮 بازی و جمع آوری سکه 🎮")
reply_keyboard.row("آیین نامه ایردراپ")
reply_keyboard.row("💌 پشتیبانی 24/7 💌")

# بررسی عضویت
def check_subscription(user_id):
    try:
        for channel in [CHANNEL_1, CHANNEL_2]:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        return False

# محدودیت درخواست
def limit_requests(f):
    @wraps(f)
    def decorated(message, *args, **kwargs):
        user_id = message.from_user.id
        last_request = db.get_last_request(user_id)
        if time.time() - last_request < 60 / REQUEST_LIMIT:
            bot.reply_to(message, "لطفاً کمی صبر کنید و دوباره تلاش کنید.")
            return
        db.update_last_request(user_id)
        return f(message, *args, **kwargs)
    return decorated

# دستور شروع
@bot.message_handler(commands=['start'])
@limit_requests
def welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    
    if not check_subscription(user_id):
        bot.send_message(message.chat.id, f"لطفاً برای استفاده از ربات، عضو این کانال‌ها شوید: \n{CHANNEL_1}\n{CHANNEL_2}")
        return

    db.add_user(user_id, first_name, last_name)
    user = db.get_user(user_id)
    bot.reply_to(message, f'سلام {first_name}! خوش آمدید به ربات ما! شناسه شما: {user[4]}', reply_markup=reply_keyboard)

# بخش دانلودر
@bot.message_handler(func=lambda message: message.text == "📥 دانلودر 📤")
@limit_requests
def downloader(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, f"لطفاً برای استفاده از ربات، عضو این کانال‌ها شوید: \n{CHANNEL_1}\n{CHANNEL_2}")
        return

    buttons = [
        types.InlineKeyboardButton("دانلود از اینستاگرام", callback_data="instagram"),
        types.InlineKeyboardButton("دانلود از یوتیوب", callback_data="youtube"),
        types.InlineKeyboardButton("دانلود از اسپاتیفای", callback_data="spotify"),
        types.InlineKeyboardButton("دانلود از ساندکلاود", callback_data="soundcloud"),
    ]

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.row(*buttons[:2])
    inline_keyboard.row(*buttons[2:])

    bot.send_message(message.chat.id, "لطفا پلتفرم مورد نظر را انتخاب کنید", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["youtube", "instagram", "spotify", "soundcloud"])
def handle_download_platform(call):
    platform_messages = {
        "youtube": "لینک ویدیو یوتیوب را ارسال کنید:",
        "instagram": "لینک پست یا ریلز اینستاگرام را ارسال کنید:",
        "spotify": "لینک موزیک اسپاتیفای را ارسال کنید:",
        "soundcloud": "لینک موزیک ساندکلاود را ارسال کنید:"
    }
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, platform_messages[call.data])

# بخش هوش مصنوعی
@bot.message_handler(func=lambda message: message.text == "🤖 هوش مصنوعی 🤖")
@limit_requests
def AI(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, f"لطفاً برای استفاده از ربات، عضو این کانال‌ها شوید: \n{CHANNEL_1}\n{CHANNEL_2}")
        return

    buttons = [
        types.InlineKeyboardButton("GPT-3", callback_data="gpt3"),
        types.InlineKeyboardButton("ساخت عکس", callback_data="image_generation"),
        types.InlineKeyboardButton("تشخیص متن از تصویر", callback_data="ocr"),
    ]

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.row(*buttons)

    bot.send_message(message.chat.id, "لطفا سرویس هوش مصنوعی مورد نظر را انتخاب کنید:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["gpt3", "image_generation", "ocr"])
def handle_ai_service(call):
    if call.data == "gpt3":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "لطفاً سوال خود را بپرسید:")
    elif call.data == "image_generation":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "لطفاً توضیحات تصویر مورد نظر را ارسال کنید:")
    elif call.data == "ocr":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "لطفاً تصویر حاوی متن را ارسال کنید:")

# پردازش درخواست‌های دانلود
@bot.message_handler(func=lambda message: message.text.startswith("http"))
@limit_requests
def process_download_request(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url:
        download_youtube(message, url)
    elif "instagram.com" in url:
        download_instagram(message, url)
    elif "spotify.com" in url:
        download_spotify(message, url)
    elif "soundcloud.com" in url:
        download_soundcloud(message, url)
    else:
        bot.reply_to(message, "لینک نامعتبر است. لطفاً یک لینک معتبر از پلتفرم‌های پشتیبانی شده ارسال کنید.")

def download_youtube(message, url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        stream.download()
        with open(stream.default_filename, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)
        os.remove(stream.default_filename)
        db.update_user_coins(message.from_user.id, 10)  # اضافه کردن 10 سکه برای دانلود موفق
    except Exception as e:
        logger.error(f"YouTube download error: {str(e)}")
        bot.reply_to(message, "متأسفانه در دانلود ویدیو مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

def download_instagram(message, url):
    try:
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, url.split("/")[-2])
        L.download_post(post, target=f"{post.owner_username}_posts")
        if post.is_video:
            with open(f"{post.owner_username}_posts/{post.date_utc:%Y-%m-%d_%H-%M-%S}.mp4", 'rb') as video_file:
                bot.send_video(message.chat.id, video_file)
        else:
            with open(f"{post.owner_username}_posts/{post.date_utc:%Y-%m-%d_%H-%M-%S}.jpg", 'rb') as photo_file:
                bot.send_photo(message.chat.id, photo_file)
        db.update_user_coins(message.from_user.id, 5)  # اضافه کردن 5 سکه برای دانلود موفق
    except Exception as e:
        logger.error(f"Instagram download error: {str(e)}")
        bot.reply_to(message, "متأسفانه در دانلود پست اینستاگرام مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

def download_spotify(message, url):
    try:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        track_id = url.split('/')[-1].split('?')[0]
        track_info = sp.track(track_id)
        bot.send_message(message.chat.id, f"اطلاعات آهنگ:\nنام: {track_info['name']}\nهنرمند: {track_info['artists'][0]['name']}\nآلبوم: {track_info['album']['name']}")
        bot.send_audio(message.chat.id, track_info['preview_url'])
        db.update_user_coins(message.from_user.id, 3)  # اضافه کردن 3 سکه برای دریافت اطلاعات موفق
    except Exception as e:
        logger.error(f"Spotify download error: {str(e)}")
        bot.reply_to(message, "متأسفانه در دریافت اطلاعات آهنگ مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

def download_soundcloud(message, url):
    try:
        client = soundcloud.Client(client_id=os.getenv('SOUNDCLOUD_CLIENT_ID'))
        track = client.get('/resolve', url=url)
        bot.send_message(message.chat.id, f"اطلاعات آهنگ:\nنام: {track.title}\nهنرمند: {track.user['username']}")
        bot.send_audio(message.chat.id, track.stream_url)
        db.update_user_coins(message.from_user.id, 3)  # اضافه کردن 3 سکه برای دانلود موفق
    except Exception as e:
        logger.error(f"SoundCloud download error: {str(e)}")
        bot.reply_to(message, "متأسفانه در دانلود آهنگ مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

# پردازش درخواست‌های هوش مصنوعی
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
@limit_requests
def handle_ai_request(message):
    if message.content_type == 'text':
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=message.text,
            max_tokens=150
        )
        bot.reply_to(message, response.choices[0].text.strip())
        db.update_user_coins(message.from_user.id, 2)  # اضافه کردن 2 سکه برای استفاده از GPT-3
    elif message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        # اینجا می‌توانید از یک کتابخانه OCR مانند pytesseract استفاده کنید
        # text = pytesseract.image_to_string(image, lang='fas')
        text = "متن استخراج شده از تصویر"  # این خط را با کد واقعی OCR جایگزین کنید
        bot.reply_to(message, f"متن استخراج شده از تصویر:\n{text}")
        db.update_user_coins(message.from_user.id, 5)  # اضافه کردن 5 سکه برای استفاده از OCR

# بخش مدیریت
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("آمار کاربران", callback_data="user_stats"),
                   types.InlineKeyboardButton("ارسال پیام همگانی", callback_data="broadcast"))
        markup.row(types.InlineKeyboardButton("پشتیبان‌گیری از دیتابیس", callback_data="backup_db"))
        bot.reply_to(message, "پنل مدیریت:", reply_markup=markup)
    else:
        bot.reply_to(message, "شما دسترسی به این بخش را ندارید.")

@bot.callback_query_handler(func=lambda call: call.data in ["user_stats", "broadcast", "backup_db"])
def handle_admin_actions(call):
    if call.from_user.id in ADMIN_IDS:
        if call.data == "user_stats":
            # اینجا آمار کاربران را نمایش دهید
            bot.answer_callback_query(call.id, "آمار کاربران")
        elif call.data == "broadcast":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "پیام خود را برای ارسال همگانی وارد کنید:")
            bot.register_next_step_handler(call.message, send_broadcast)
        elif call.data == "backup_db":
            db.backup_database()
            bot.answer_callback_query(call.id, "پشتیبان‌گیری با موفقیت انجام شد.")

def send_broadcast(message):
    users = db.c.execute("SELECT user_id FROM users").fetchall()
    for user in users:
        try:
            bot.send_message(user[0], message.text)
        except Exception as e:
            logger.error(f"Error sending broadcast to user {user[0]}: {str(e)}")
    bot.reply_to(message, "پیام همگانی با موفقیت ارسال شد.")

# شروع ربات
if __name__ == "__main__":
    logger.info("Bot started")
    bot.polling(none_stop=True)