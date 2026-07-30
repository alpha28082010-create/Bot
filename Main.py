import os
import asyncio
import http.server
import socketserver
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- Render bepul Web Service port xatoligini oldini olish uchun veb-server ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server xatosi: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()
# ----------------------------------------------------------------------------

# Telegram Bot Tokeningiz
TOKEN = "8879459729:AAF8F7F0oFhNj3g2cf76XElwmm3D2wlr3GQ"

# Telegram ID (Admin uchun /stats)
ADMIN_ID = 8756520950  

# Kanaligiz useri
CHANNEL_USERNAME = "@Akkaunt_savdo26" 

USER_FILE = "users.txt"
user_links = {}

def add_user(user_id):
    """Foydalanuvchini bazaga saqlash"""
    users = set()
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            for line in f:
                users.add(line.strip())
    
    users.add(str(user_id))
    
    with open(USER_FILE, "w") as f:
        for uid in users:
            f.write(f"{uid}\n")

def get_user_count():
    """Jami foydalanuvchilar sonini sanash"""
    if not os.path.exists(USER_FILE):
        return 0
    with open(USER_FILE, "r") as f:
        return len(f.readlines())

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Foydalanuvchi kanalga a'zo ekanligini tekshirish funksiyasi"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_user(user_id)
    
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Tekshirish", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Botdan foydalanish uchun avval quyidagi kanalimizga a'zo bo'lishingiz kerak!\n\n"
            "A'zo bo'lgach, \"🔄 Tekshirish\" tugmasini bosing.",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text(
        "Assalomu alaykum! 🎬\n\n"
        "Ushbu bot orqali YouTube videolarini MP3 yoki MP4 koʻrinishida yuklab olishingiz mumkin.\n\n"
        "Menga shunchaki video havolasini yuboring! 🚀"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Bu buyruq faqat admin uchun!")
        return
    
    count = get_user_count()
    await update.message.reply_text(f"📊 Botimizdagi jami foydalanuvchilar soni: **{count}** ta", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_user(user_id)
    
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Tekshirish", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Botdan foydalanishni davom ettirish uchun avval kanalimizga a'zo bo'ling!",
            reply_markup=reply_markup
        )
        return

    text = update.message.text
    if "youtube.com" in text or "youtu.be" in text:
        user_links[user_id] = text

        keyboard = [
            [
                InlineKeyboardButton("📱 360p", callback_data="res_360"),
                InlineKeyboardButton("📱 480p", callback_data="res_480")
            ],
            [
                InlineKeyboardButton("💻 720p (HD)", callback_data="res_720"),
                InlineKeyboardButton("💻 1080p (FHD)", callback_data="res_1080")
            ],
            [
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data="res_audio")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Marhamat, video sifatini yoki formatini tanlang:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Iltimos, toʻgʻri YouTube video havolasini (link) yuboring.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data

    if action == "check_sub":
        is_subscribed = await check_subscription(user_id, context)
        if is_subscribed:
            await query.edit_message_text(
                "✅ Rahmat! Kanalga a'zo bo'ldingiz.\n\n"
                "Endi menga YouTube video havolasini (link) yuborishingiz mumkin! 🚀"
            )
        else:
            await query.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
        return

    if user_id not in user_links:
        await query.edit_message_text("❌ Havola eskirgan yoki topilmadi. Iltimos, linkni qaytadan yuboring.")
        return

    url = user_links[user_id]

    if action == "res_360":
        format_selector = "best[height<=360][ext=mp4]/best[height<=360]/best"
        label = "360p video"
    elif action == "res_480":
        format_selector = "best[height<=480][ext=mp4]/best[height<=480]/best"
        label = "480p video"
    elif action == "res_720":
        format_selector = "best[height<=720][ext=mp4]/best[height<=720]/best"
        label = "720p video"
    elif action == "res_1080":
        format_selector = "best[height<=1080][ext=mp4]/best[height<=1080]/best"
        label = "1080p video"
    else:
        format_selector = "bestaudio[ext=m4a]/bestaudio/best"
        label = "Audio (MP3)"

    await query.edit_message_text(f"⏳ {label} yuklanmoqda, iltimos kuting...")
    
    file_extension = "m4a" if action == "res_audio" else "mp4"
    file_path = f"media_{user_id}.{file_extension}"

    ydl_opts = {
        'format': format_selector,
        'outtmpl': file_path,
        'nopart': True,
        'continuedl': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'quiet': True,
    }

    loop = asyncio.get_event_loop()
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    try:
        await loop.run_in_executor(None, download)

        if action == "res_audio":
            await query.edit_message_text("📤 Audio Telegram'ga yuborilmoqda...")
            with open(file_path, 'rb') as f:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption="✅ Audio tayyor!")
        else:
            await query.edit_message_text("📤 Video Telegram'ga yuborilmoqda...")
            with open(file_path, 'rb') as f:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption=f"✅ {label} tayyor!")
                
        await query.message.delete()

    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if user_id in user_links:
            del user_links[user_id]

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
