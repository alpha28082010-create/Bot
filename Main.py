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

TOKEN = "8879459729:AAF8F7F0oFhNj3g2cf76XElwmm3D2wlr3GQ"
ADMIN_ID = 8756520950  
CHANNEL_USERNAME = "@Akkaunt_savdo26" 

USER_FILE = "users.txt"
user_links = {}
user_languages = {}  # Foydalanuvchi tillarini saqlash uchun lug'at

# Lug'at va matnlar
TEXTS = {
    'uz': {
        'sub_req': "⚠️ Botdan foydalanish uchun avval quyidagi kanalimizga a'zo bo'lishingiz kerak!\n\nA'zo bo'lgach, \"🔄 Tekshirish\" tugmasini bosing.",
        'sub_btn': "📢 Kanalga a'zo bo'lish",
        'check_btn': "🔄 Tekshirish",
        'welcome': "Assalomu alaykum! 🎬\n\nUshbu bot orqali YouTube videolani MP3 va MP4 koʻrinishida yuklab olishingiz mumkin.\n\nMenga shunchaki video havolasini yuboring! 🚀",
        'not_sub': "❌ Siz hali kanalga a'zo bo'lmadingiz!",
        'sub_ok': "✅ Rahmat! Kanalga a'zo bo'ldingiz.\n\nEndi menga YouTube video havolasini yuborishingiz mumkin! 🚀",
        'choose_quality': "Marhamat, video sifatini yoki formatini tanlang:",
        'invalid_link': "Iltimos, toʻgʻri YouTube video havolasini yuboring.",
        'downloading': "⏳ {} yuklanmoqda, iltimos kuting...",
        'sending_audio': "📤 Audio Telegram'ga yuborilmoqda...",
        'sending_video': "📤 Video Telegram'ga yuborilmoqda...",
        'expired': "❌ Havola eskirgan yoki topilmadi. Iltimos, linkni qaytadan yuboring.",
        'lang_changed': "🌐 Til **O'zbekcha**ga o'zgartirildi!"
    },
    'ru': {
        'sub_req': "⚠️ Для использования бота сначала подпишитесь на наш канал!\n\nПосле подписки нажмите кнопку **\"🔄 Проверить\"**.",
        'sub_btn': "📢 Подписаться на канал",
        'check_btn': "🔄 Проверить",
        'welcome': "Здравствуйте! 🎬\n\nС помощью этого бота вы можете скачивать видео с YouTube в нужном качестве или в формате MP3 (Аудио).\n\nПросто отправьте мне ссылку на видео! 🚀",
        'not_sub': "❌ Вы еще не подписались на канал!",
        'sub_ok': "✅ Спасибо! Вы подписались на канал.\n\nТеперь отправьте ссылку на видео YouTube! 🚀",
        'choose_quality': "Пожалуйста, выберите качество или формат видео:",
        'invalid_link': "Пожалуйста, отправьте правильную ссылку на YouTube.",
        'downloading': "⏳ Идет скачивание {}, пожалуйста подождите...",
        'sending_audio': "📤 Аудио отправляется в Telegram...",
        'sending_video': "📤 Видео отправляется в Telegram...",
        'expired': "❌ Ссылка устарела или не найдена. Отправьте ссылку еще раз.",
        'lang_changed': "🌐 Язык изменен на **Русский**!"
    },
    'en': {
        'sub_req': "⚠️ To use this bot, you must first subscribe to our channel!\n\nAfter subscribing, click the **\"🔄 Check\"** button.",
        'sub_btn': "📢 Subscribe to channel",
        'check_btn': "🔄 Check",
        'welcome': "Welcome! 🎬\n\nWith this bot, you can download YouTube videos in the desired quality or as MP3 (Audio).\n\nJust send me a video link! 🚀",
        'not_sub': "❌ You haven't subscribed to the channel yet!",
        'sub_ok': "✅ Thank you! You have subscribed.\n\nNow send me a YouTube video link! 🚀",
        'choose_quality': "Please select video quality or format:",
        'invalid_link': "Please send a valid YouTube video link.",
        'downloading': "⏳ Downloading {}, please wait...",
        'sending_audio': "📤 Sending audio to Telegram...",
        'sending_video': "📤 Sending video to Telegram...",
        'expired': "❌ Link expired or not found. Please send the link again.",
        'lang_changed': "🌐 Language changed to **English**!"
    }
}

def add_user(user_id):
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
    if not os.path.exists(USER_FILE):
        return 0
    with open(USER_FILE, "r") as f:
        return len(f.readlines())

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

# Tilni olish funksiyasi (sukut bo'yicha 'uz')
def get_lang(user_id):
    return user_languages.get(user_id, 'uz')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_user(user_id)
    lang = get_lang(user_id)
    txt = TEXTS[lang]
    
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton(txt['sub_btn'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(txt['check_btn'], callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(txt['sub_req'], reply_markup=reply_markup)
        return

    await update.message.reply_text(txt['welcome'])

# Tilni tanlash menyusi
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 **Iltimos, tilni tanlang / Пожалуйста, выберите язык / Please choose language:**", reply_markup=reply_markup, parse_mode="Markdown")

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
    lang = get_lang(user_id)
    txt = TEXTS[lang]
    
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton(txt['sub_btn'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(txt['check_btn'], callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(txt['sub_req'], reply_markup=reply_markup)
        return

    text = update.message.text
    if "youtube.com" in text or "youtu.be" in text:
        user_links[user_id] = text
        keyboard = [
            [InlineKeyboardButton("📱 360p", callback_data="res_360"), InlineKeyboardButton("📱 480p", callback_data="res_480")],
            [InlineKeyboardButton("💻 720p (HD)", callback_data="res_720"), InlineKeyboardButton("💻 1080p (FHD)", callback_data="res_1080")],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="res_audio")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(txt['choose_quality'], reply_markup=reply_markup)
    else:
        await update.message.reply_text(txt['invalid_link'])

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data

    # Til o'zgartirish tugmalari bosilganda
    if action.startswith("lang_"):
        selected_lang = action.split("_")[1]
        user_languages[user_id] = selected_lang
        await query.edit_message_text(TEXTS[selected_lang]['lang_changed'], parse_mode="Markdown")
        return

    lang = get_lang(user_id)
    txt = TEXTS[lang]

    if action == "check_sub":
        is_subscribed = await check_subscription(user_id, context)
        if is_subscribed:
            await query.edit_message_text(txt['sub_ok'])
        else:
            await query.answer(txt['not_sub'], show_alert=True)
        return

    if user_id not in user_links:
        await query.edit_message_text(txt['expired'])
        return

    url = user_links[user_id]

    if action == "res_360":
        format_selector = "best[height<=360][ext=mp4]/best[height<=360]/best"
        label = "360p"
    elif action == "res_480":
        format_selector = "best[height<=480][ext=mp4]/best[height<=480]/best"
        label = "480p"
    elif action == "res_720":
        format_selector = "best[height<=720][ext=mp4]/best[height<=720]/best"
        label = "720p"
    elif action == "res_1080":
        format_selector = "best[height<=1080][ext=mp4]/best[height<=1080]/best"
        label = "1080p"
    else:
        format_selector = "bestaudio[ext=m4a]/bestaudio/best"
        label = "Audio (MP3)"

    await query.edit_message_text(txt['downloading'].format(label))
    
    file_extension = "m4a" if action == "res_audio" else "mp4"
    file_path = f"media_{user_id}.{file_extension}"

    # YouTube blokirovkasini aylanib o'tish uchun yangilangan ydl_opts
    ydl_opts = {
        'format': format_selector,
        'outtmpl': file_path,
        'nopart': True,
        'continuedl': False,
        'quiet': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'mweb', 'tv'],
                'skip': ['webpage', 'configs'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        },
    }

    loop = asyncio.get_event_loop()
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    try:
        await loop.run_in_executor(None, download)

        if action == "res_audio":
            await query.edit_message_text(txt['sending_audio'])
            with open(file_path, 'rb') as f:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption="✅ Audio tayyor!")
        else:
            await query.edit_message_text(txt['sending_video'])
            with open(file_path, 'rb') as f:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption=f"✅ {label} tayyor!")
                
        await query.message.delete()

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if user_id in user_links:
            del user_links[user_id]

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
