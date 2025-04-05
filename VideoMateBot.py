
import logging
import os
import aiohttp
import asyncio
import json
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yt_dlp import YoutubeDL
from datetime import datetime
from aiohttp import web

API_TOKEN = '7972857462:AAHdPNrLoMtIOx7sRklokjJWDGkQpixJsZs'
ADMIN_ID = 123456789  # Replace with the Telegram admin ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

os.makedirs('downloads', exist_ok=True)
os.makedirs('logs', exist_ok=True)
HISTORY_FILE = 'logs/user_history.json'

YDL_OPTIONS = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True,
    'merge_output_format': 'mp4',
    'postprocessors': [{'key': 'FFmpegMetadata'}],
    'noplaylist': True,
    'geo_bypass': True,
    'source_address': '0.0.0.0'
}

YDL_OPTIONS_MP3 = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'noplaylist': True
}

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        user_history = json.load(f)
else:
    user_history = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Welcome to VideoMateBot!\n\nSend a video link from YouTube, TikTok, Instagram, Facebook, Twitter, and more...\nUse /history to check your download history.")

@dp.message_handler(commands=['history'])
async def history_handler(message: types.Message):
    uid = str(message.from_user.id)
    history = user_history.get(uid, [])
    if not history:
        await message.reply("No download history available.")
    else:
        response = "Your download history:\n"
        for entry in history[-5:]:
            response += f"- {entry['title']} ({entry['url']})\n"
        await message.reply(response)

@dp.message_handler()
async def video_handler(message: types.Message):
    url = message.text.strip()
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Download Video", callback_data=f"video|{url}"),
        InlineKeyboardButton("Download MP3 (Audio only)", callback_data=f"mp3|{url}")
    )
    await message.reply("Choose download type:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data)
async def process_callback(callback_query: types.CallbackQuery):
    action, url = callback_query.data.split('|', 1)
    await bot.answer_callback_query(callback_query.id)
    msg = await bot.send_message(callback_query.from_user.id, "Downloading... Please wait")

    try:
        ydl_opts = YDL_OPTIONS_MP3 if action == 'mp3' else YDL_OPTIONS
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if action == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'

        uid = str(callback_query.from_user.id)
        entry = {"title": info.get("title"), "url": url, "date": str(datetime.now())}
        user_history.setdefault(uid, []).append(entry)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_history, f, ensure_ascii=False, indent=2)

        if os.path.getsize(file_path) < 50 * 1024 * 1024:
            with open(file_path, 'rb') as f:
                await bot.send_document(callback_query.from_user.id, f)
        else:
            gofile_url = await upload_to_gofile(file_path)
            await bot.send_message(callback_query.from_user.id, f"The file is too large. Uploaded here:\n{gofile_url}")

        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await bot.send_message(callback_query.from_user.id, "An error occurred during download. Please check the link or try again later.")

async def upload_to_gofile(file_path):
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.gofile.io/getServer') as resp:
            server = (await resp.json())['data']['server']

        upload_url = f'https://{server}.gofile.io/uploadFile'
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=os.path.basename(file_path))
            async with session.post(upload_url, data=data) as response:
                result = await response.json()
                return result['data']['downloadPage']

async def stats_handler(request):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total_users = len(data)
    total_downloads = sum(len(v) for v in data.values())
    return web.Response(text=f"Users: {total_users}\nDownloads: {total_downloads}", content_type='text/plain')

async def admin_panel(request):
    if request.query.get("admin") != str(ADMIN_ID):
        return web.Response(text="Unauthorized", status=403)
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return web.json_response(data)

app = web.Application()
app.add_routes([
    web.get('/', stats_handler),
    web.get('/admin', admin_panel),
])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(web._run_app(app, port=8080))
    executor.start_polling(dp, skip_updates=True)
