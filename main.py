import asyncio
import logging
import random
import os
import aiohttp
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from hijri_converter import Gregorian
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '8222976736:AAEWUSTKnEGZiP9USYBAECbtZkLGtp--sEc'
CHANNEL_ID = '@karnayuzb'
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

REGIONS = {
    "Toshkent": "Tashkent", "Andijon": "Andijan", "Buxoro": "Bukhara", 
    "Guliston": "Gulistan", "Jizzax": "Jizzakh", "Nukus": "Nukus", 
    "Namangan": "Namangan", "Navoiy": "Navoi", "Qarshi": "Karshi", 
    "Samarqand": "Samarkand", "Termiz": "Termez", "Urganch": "Urgench", "Farg'ona": "Fergana"
}

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            return await res.json()

# --- VAZIFALAR ---

async def job_ob_havo():
    """Min/Max haroratlar infografikasi"""
    text = "🌤 <b>HUDUDLARARO OB-HAVO</b>\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for uzb, eng in REGIONS.items():
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude=41.26&longitude=69.21&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            data = await fetch_json(url)
            text += f"📍 {uzb:10} | 🔵 {data['daily']['temperature_2m_min'][0]}° / 🔴 {data['daily']['temperature_2m_max'][0]}°\n"
        except: continue
    await bot.send_message(CHANNEL_ID, text)

async def job_xayrli_tong():
    """Tonggi tabrik va sanalar"""
    today = datetime.now(TASHKENT_TZ)
    h = Gregorian(today.year, today.month, today.day).to_hijri()
    weekday = today.strftime("%A").replace("Monday","Dushanba").replace("Tuesday","Seshanba").replace("Wednesday","Chorshanba").replace("Thursday","Payshanba").replace("Friday","Juma").replace("Saturday","Shanba").replace("Sunday","Yakshanba")
    text = f"☀️ <b>XAYRLI TONG!</b>\n\n📅 <b>{today.strftime('%d.%m.%Y')}</b>\n🌙 <b>{h.day}-{h.month_name()} {h.year}-yil</b>\n🗓 <b>{weekday}</b>\n\n✨ Kuningiz fayzli o'tsin!"
    await bot.send_message(CHANNEL_ID, text)

async def job_tarix():
    """KUN TARIXI: Onlayn Wikipedia ma'lumotlari"""
    now = datetime.now(TASHKENT_TZ)
    try:
        url = f"https://uz.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month}/{now.day}"
        data = await fetch_json(url)
        event = random.choice(data['selected'])
        text = f"📜 <b>TARIXDA BUGUN ({now.day}-{now.month})</b>\n\n{event['text']}\n\n🔗 @karnayuzb"
    except:
        text = "📜 Bugun tarixdagi muhim voqealarga boy kun!"
    await bot.send_message(CHANNEL_ID, text)

async def job_valyuta():
    """Aniq bank kurslari"""
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        data = await fetch_json(url)
        usd = next(item for item in data if item["Ccy"] == "USD")['Rate']
        text = f"🏦 <b>VALYUTA KURSI</b>\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n🏛 MB: 1 USD = {usd} so'm\n📥 Sotib olish: {float(usd)-45} so'm\n📤 Sotish: {float(usd)+25} so'm"
        await bot.send_message(CHANNEL_ID, text)
    except: pass

async def job_namoz_vaqtlari():
    """5 mahal namoz vaqtlari jadvali"""
    text = "🕋 <b>NAMOZ VAQTLARI</b>\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n🏙 Hudud | Bomd | Pesh | Asr  | Shom | Xuft\n"
    for uzb, eng in REGIONS.items():
        try:
            url = f"http://api.aladhan.com/v1/timingsByCity?city={eng}&country=Uzbekistan&method=3"
            res = await fetch_json(url)
            t = res['data']['timings']
            text += f"📍{uzb[:3]}|{t['Fajr']}|{t['Dhuhr']}|{t['Asr']}|{t['Maghrib']}|{t['Isha']}\n"
        except: continue
    await bot.send_message(CHANNEL_ID, text)

async def job_quiz():
    """Onlayn cheksiz viktorinalar"""
    try:
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        data = await fetch_json(url)
        res = data['results'][0]
        options = res['incorrect_answers'] + [res['correct_answer']]
        random.shuffle(options)
        await bot.send_poll(CHANNEL_ID, question=f"🤔 Savol:\n{res['question']}", options=options, type='quiz', correct_option_id=options.index(res['correct_answer']), is_anonymous=True)
    except: pass

# --- SERVER VA SHEDULER ---
async def handle(request): return web.Response(text="Active")
async def start_server():
    app = web.Application(); app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
scheduler.add_job(job_ob_havo, 'cron', hour=5, minute=0)
scheduler.add_job(job_xayrli_tong, 'cron', hour=6, minute=0)
scheduler.add_job(job_tarix, 'cron', hour=7, minute=0) # KUN TARIXI QO'SHILDI
scheduler.add_job(job_valyuta, 'cron', hour=10, minute=0)
for h in [12, 16, 20]: scheduler.add_job(job_quiz, 'cron', hour=h, minute=0)
scheduler.add_job(job_namoz_vaqtlari, 'cron', hour=22, minute=0)

async def main():
    scheduler.start()
    await start_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
