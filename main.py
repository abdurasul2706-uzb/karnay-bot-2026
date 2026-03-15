import asyncio
import requests
import logging
import random
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from hijri_converter import Gregorian
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- SOZLAMALAR ---
API_TOKEN = '8222976736:AAEWUSTKnEGZiP9USYBAECbtZkLGtp--sEc'
CHANNEL_ID = '@karnayuzb'
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- HUDUDLAR ---
CITIES = ["Toshkent", "Andijon", "Buxoro", "Guliston", "Jizzax", "Nukus", "Namangan", "Navoiy", "Qarshi", "Samarqand", "Termiz", "Urganch", "Farg'ona"]

# --- ONLAYN MANBALARDAN MA'LUMOT OLISH ---

def get_hijri_date():
    today = datetime.now(TASHKENT_TZ)
    h = Gregorian(today.year, today.month, today.day).to_hijri()
    months = {1:"Muharram", 2:"Safar", 3:"Rabiul-avval", 4:"Rabiul-oxir", 5:"Jumadul-avval", 6:"Jumadul-oxir", 7:"Rajab", 8:"Sha'bon", 9:"Ramazon", 10:"Shavvol", 11:"Zulqa'da", 12:"Zulhijja"}
    return f"{h.day}-{months[h.month]} {h.year}-yil"

async def get_weather():
    text = "🌤 <b>Viloyatlar bo'yicha bugungi ob-havo:</b>\n\n"
    for city in CITIES:
        # Open-Meteo API (Cheksiz va aniq)
        url = f"https://api.open-meteo.com/v1/forecast?latitude=41.26&longitude=69.21&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        res = requests.get(url).json()
        t_max = res['daily']['temperature_2m_max'][0]
        t_min = res['daily']['temperature_2m_min'][0]
        text += f"📍 {city}: {t_min}°C ... {t_max}°C\n"
    return text

async def get_history():
    try:
        now = datetime.now(TASHKENT_TZ)
        url = f"https://uz.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month}/{now.day}"
        res = requests.get(url).json()
        event = random.choice(res['selected'])
        return f"📜 <b>Tarixda bugun ({now.day}-{now.month}):</b>\n\n{event['text']}"
    except:
        return "📜 Bugun dunyo tarixida muhim kashfiyotlar va voqealar yuz bergan kun."

async def get_currency():
    url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    res = requests.get(url).json()
    usd = next(item for item in res if item["Ccy"] == "USD")
    return f"💰 <b>MB Rasmiy valyuta kursi:</b>\n\n🇺🇸 1 USD = {usd['Rate']} so'm\n📈 O'zgarish: {usd['Diff']}\n\n<i>Aniq va rasmiy ma'lumot.</i>"

async def send_quiz():
    # Tayyor mantiqiy savollar bazasi (Takrorlanmasligi uchun ko'paytirishingiz mumkin)
    quizzes = [
        {"q": "Qaysi davlat dunyoda eng ko'p oltin qazib oladi?", "o": ["Xitoy", "Rossiya", "AQSH", "O'zbekiston"], "c": 0},
        {"q": "Eng tez uchuvchi qush qaysi?", "o": ["Burgut", "Lochin", "Qarshig'ay", "Laylak"], "c": 1}
    ]
    quiz = random.choice(quizzes)
    await bot.send_poll(chat_id=CHANNEL_ID, question=quiz['q'], options=quiz['o'], type='quiz', correct_option_id=quiz['c'])

# --- AVTOMATIK VAZIFALAR ---

async def job_0500(): # Ob-havo
    text = await get_weather()
    await bot.send_message(CHANNEL_ID, text)

async def job_0600(): # Xayrli tong
    today = datetime.now(TASHKENT_TZ)
    hijri = get_hijri_date()
    week_days = {"Monday":"Dushanba", "Tuesday":"Seshanba", "Wednesday":"Chorshanba", "Thursday":"Payshanba", "Friday":"Juma", "Saturday":"Shanba", "Sunday":"Yakshanba"}
    weekday = week_days[today.strftime("%A")]
    text = f"☀️ <b>Xayrli tong!</b>\n\n📅 Bugun: {today.strftime('%d.%m.%Y')}\n🌙 Hijriy: {hijri}\n🗓 Kun: {weekday}\n\n✨ Kuningiz xayrli o'tsin!"
    await bot.send_message(CHANNEL_ID, text)

async def job_0700(): # Tarix
    text = await get_history()
    await bot.send_message(CHANNEL_ID, text)

async def job_1000(): # Valyuta
    text = await get_currency()
    await bot.send_message(CHANNEL_ID, text)

async def job_2200(): # Namoz vaqtlari
    url = "http://api.aladhan.com/v1/timingsByCity?city=Tashkent&country=Uzbekistan&method=3"
    t = requests.get(url).json()['data']['timings']
    text = f"🕋 <b>Ertangi namoz vaqtlari (Toshkent):</b>\n\n🏙 Bomdod: {t['Fajr']}\n🌅 Quyosh: {t['Sunrise']}\n🏙 Peshin: {t['Dhuhr']}\n🌇 Asr: {t['Asr']}\n🌃 Shom: {t['Maghrib']}\n🌃 Xufton: {t['Isha']}"
    await bot.send_message(CHANNEL_ID, text)

# --- ISHGA TUSHIRISH ---
scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
scheduler.add_job(job_0500, 'cron', hour=5, minute=0)
scheduler.add_job(job_0600, 'cron', hour=6, minute=0)
scheduler.add_job(job_0700, 'cron', hour=7, minute=0)
scheduler.add_job(job_1000, 'cron', hour=10, minute=0)
scheduler.add_job(job_2200, 'cron', hour=22, minute=0)
scheduler.add_job(send_quiz, 'cron', hour=12, minute=0) # 1-viktornina
scheduler.add_job(send_quiz, 'cron', hour=16, minute=0) # 2-viktornina
scheduler.add_job(send_quiz, 'cron', hour=20, minute=0) # 3-viktornina

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
