import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
import yt_dlp

# Logging sozlash
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
# Token va Admin ID ni Environment Variables orqali yoki qo'lda kiriting
TOKEN = os.getenv("BOT_TOKEN", "8428517451:AA...") # O'z tokeningizni yozing
ADMIN_ID = int(os.getenv("ADMIN_ID", 8665041091))   # O'z ID-ingizni yozing

bot = Bot(token=TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "insta_users.txt")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: pass
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def add_user(user_id):
    with open(DB_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(DB_FILE, "a") as f:
            f.write(f"{user_id}\n")

# --- MENYULAR ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Qanday yuklash?"), KeyboardButton(text="📊 Statistika")]
    ],
    resize_keyboard=True
)

# --- YUKLAB OLISH FUNKSIYASI ---
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOADS_DIR}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        f"👋 Salom {message.from_user.full_name}!\n\n"
        "📸 Instagram Reels yoki YouTube Shorts havolasini yuboring!",
        reply_markup=main_menu
    )

@dp.message(F.text == "📥 Qanday yuklash?")
async def help_info(message: types.Message):
    await message.answer("Instagramdan video havolasini nusxalang va botga yuboring. Tamom! ✅")

@dp.message(F.text == "📊 Statistika")
async def stat_cmd(message: types.Message):
    with open(DB_FILE, "r") as f:
        count = len(f.read().splitlines())
    await message.answer(f"📊 Botdan {count} kishi foydalanmoqda.")

# Video havolalarini tutish
@dp.message(F.text.contains("instagram.com") | F.text.contains("://youtube.com"))
async def handle_download(message: types.Message):
    url = message.text
    wait_msg = await message.answer("⏳ Video tayyorlanmoqda, iltimos kuting...")
    
    try:
        # Yuklash jarayonini async rejimda ishga tushirish
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)
        
        # Videoni yuborish
        video = FSInputFile(file_path)
        await message.answer_video(video=video, caption="✅ Yuklab olindi: @botingiz_nomi")
        
        # Xotirani tejash uchun faylni o'chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        await wait_msg.delete()
        
    except Exception as e:
        logging.error(f"Download error: {e}")
        await wait_msg.edit_text("❌ Xatolik! Havola xato yoki video yopiq profilda.")

# Boshqa har qanday xabar uchun
@dp.message()
async def echo_all(message: types.Message):
    await message.answer("Iltimos, faqat Instagram yoki Shorts havolasini yuboring! 📥")

# --- RENDER UCHUN WEB SERVER ---
async def web_handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get("/", web_handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
