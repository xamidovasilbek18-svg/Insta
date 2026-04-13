import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# Logging
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
TOKEN = "TOKENINGIZNI_SHU_YERGA_YOZING"
ADMIN_ID = 123456789  # O'z ID-ingiz
bot = Bot(token=TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "insta_users.txt")

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: pass

def add_user(user_id):
    users = open(DB_FILE, "r").read().splitlines()
    if str(user_id) not in users:
        with open(DB_FILE, "a") as f: f.write(f"{user_id}\n")

# Asosiy menyu
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Qanday yuklash?"), KeyboardButton(text="📊 Statistika")]
    ],
    resize_keyboard=True
)

async def handle(request):
    return web.Response(text="Insta Save Bot is Live!")

# --- FUNKSIYALAR ---
def download_insta_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        f"👋 Salom {message.from_user.full_name}!\n\n"
        "📸 Instagram Reels, Video va Shorts havolasini yuboring, men uni yuklab beraman!",
        reply_markup=main_menu
    )

@dp.message(F.text == "📥 Qanday yuklash?")
async def help_info(message: types.Message):
    await message.answer("Instagramdan video havolasini nusxalang va botga yuboring. Tamom! ✅")

@dp.message(F.text == "📊 Statistika")
async def stat_cmd(message: types.Message):
    count = len(open(DB_FILE, "r").read().splitlines())
    await message.answer(f"📊 Botdan {count} kishi foydalanmoqda.")

@dp.message(F.text.contains("instagram.com") | F.text.contains("://youtube.com"))
async def handle_download(message: types.Message):
    url = message.text
    wait_msg = await message.answer("⏳ Video tayyorlanmoqda, iltimos kuting...")
    
    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_insta_video, url)
        
        video_file = types.FSInputFile(file_path)
        await message.answer_video(video=video_file, caption="✅ Yuklab olindi: @botingiz_nomi")
        
        # Faylni yuborgandan so'ng o'chirib yuboramiz (xotira to'lmasligi uchun)
        os.remove(file_path)
        await wait_msg.delete()
    except Exception as e:
        logging.error(f"Download error: {e}")
        await wait_msg.edit_text("❌ Xatolik yuz berdi. Havola noto'g'ri yoki video yopiq profilda bo'lishi mumkin.")

async def main():
    # Web server Render uchun
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    
    print("Insta Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
