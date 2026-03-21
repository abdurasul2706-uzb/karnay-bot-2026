import logging
import asyncio
import random
import os
from datetime import datetime
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from googletrans import Translator
from hijridate import Gregorian

# --- RENDER PORT XATOSINI TUZATISH (TIMEOUT OLDINI OLISH) ---
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Karnayuzb Bot is Active!")
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('', port), DummyHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- ASOSIY SOZLAMALAR ---
API_TOKEN = '8222976736:AAERrJbYXYiIhFpfwHttD9R5mAaql4iEgzs' 
CHANNEL_ID = '@Karnayuzb'
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
translator = Translator()

VILOYATLAR = {
    "Toshkent": {"lat": 41.2995, "lon": 69.2401, "region": "Toshkent"},
    "Andijon": {"lat": 40.7833, "lon": 72.3333, "region": "Andijon"},
    "Buxoro": {"lat": 39.7747, "lon": 64.4286, "region": "Buxoro"},
    "Farg'ona": {"lat": 40.3842, "lon": 71.7844, "region": "Farg'ona"},
    "Jizzax": {"lat": 40.1158, "lon": 67.8422, "region": "Jizzax"},
    "Xorazm": {"lat": 41.5500, "lon": 60.6333, "region": "Urganch"},
    "Namangan": {"lat": 41.0011, "lon": 71.6683, "region": "Namangan"},
    "Navoiy": {"lat": 40.1031, "lon": 65.3739, "region": "Navoiy"},
    "Qarshi": {"lat": 38.8610, "lon": 65.7847, "region": "Qarshi"},
    "Samarqand": {"lat": 39.6542, "lon": 66.9597, "region": "Samarqand"},
    "Guliston": {"lat": 40.4939, "lon": 68.7703, "region": "Guliston"},
    "Termiz": {"lat": 37.2242, "lon": 67.2783, "region": "Termiz"},
    "Nukus": {"lat": 43.8041, "lon": 59.4457, "region": "Nukus"}
}

# --- 1. XAYRLI TONG (HIJRIY, MILODIY, UZUN TILAKLAR) ---
async def job_xayrli_tong():
    now = datetime.now(TASHKENT_TZ)
    h = Gregorian(now.year, now.month, now.day).to_hijri()
    hafta = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"][now.weekday()]
    
    tilaklar = [
        "Assalomu alaykum va rohmatullohi va barokatuh! Ushbu go'zal tong barchangizga muborak bo'lsin. Qalbingiz iymon nuriga, xonadoningiz esa fayz-u barakaga to'lsin. Bugun rejalashtirgan har bir ezgu ishingiz Alloh taolo tomonidan ijobat bo'lib, kuningiz xayrli va unumli o'tsin! Yuzingizdan tabassum aslo arimasin.",
        "Xayrli tong, qadri baland obunachilarim! Yangi kun, yangi imkoniyatlar muborak! Alloh bugungi kuningizni kechagidan nurliroq va barakaliroq qilsin. Har bir qadamingizda yaxshiliklar hamroh bo'lsin, yaqinlaringiz baxtiga doimo sog'-omon bo'ling. Kuningiz quvonchli lahzalarga boy bo'lsin!"
    ]
    
    msg = f"☀️ **XAYRLI TONG, AZIZLAR!**\n\n"
    msg += f"📅 **Milodiy:** {now.strftime('%d.%m.%Y')}-yil\n"
    msg += f"🌙 **Hijriy:** {h.day}-{h.month_name()} {h.year}-yil\n"
    msg += f"🗓 **Hafta kuni:** {hafta}\n\n"
    msg += f"✨ {random.choice(tilaklar)}\n\n"
    msg += f"🔗 @Karnayuzb"
    await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# --- 2. OB-HAVO (VILOYATLAR BO'YICHA JADVAL) ---
async def job_ob_havo():
    text = "🌤 **VILOYATLAR OB-HAVO MA'LUMOTI**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += "📍 **Hudud** | **Min** | **Max**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    async with aiohttp.ClientSession() as session:
        for vil, pos in VILOYATLAR.items():
            url = f"https://api.open-meteo.com/v1/forecast?latitude={pos['lat']}&longitude={pos['lon']}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            async with session.get(url) as r:
                data = await r.json()
                t_max, t_min = data['daily']['temperature_2m_max'][0], data['daily']['temperature_2m_min'][0]
                text += f"🔹 {vil[:9]:<9} | {t_min:+.1f}° | {t_max:+.1f}°\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

# --- 3. KUN TARIXI (VOQEALAR VA SHAXSLAR) ---
async def job_kun_tarixi():
    now = datetime.now(TASHKENT_TZ)
    url = f"https://uz.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.strftime('%m/%d')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            events = data.get('selected', [])[:4]
            msg = f"📜 **TARIXDA BUGUN ({now.strftime('%d-%B')})**\n\n"
            for ev in events:
                text_uz = translator.translate(ev['text'], dest='uz').text
                msg += f"🗓 **{ev['year']}-yil:**\n⚡️ {text_uz}\n\n"
            await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# --- 4. VALYUTA KURSI (HAMMA BANKLAR DOLLAR KURSI) ---
async def job_valyuta():
    url_nbu = "https://nbu.uz/uz/exchange-rates/json/"
    msg = "🏦 **BANKLARDA DOLLAR KURSI (USD)**\n"
    msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    msg += "🏛 **Bank nomi** | **Sotib** | **Sotish**\n"
    msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_nbu) as r:
            banks = await r.json()
            for b in banks[:10]: # Eng asosiy banklar
                name = b['title'][:10]
                buy = b['nbu_buy_price'] or "—"
                cell = b['nbu_cell_price'] or "—"
                msg += f"🔹 {name:<10} | {buy} | {cell}\n"
    msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    msg += "⚠️ Markaziy Bank kursi bilan farq qilishi mumkin."
    await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# --- 5. NAMOZ VAQTLARI (HUDUDLAR KESIMIDA) ---
async def job_namoz():
    text = "🕌 **5 MAHAL NAMOZ VAQTLARI**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += "📍 **Hudud** | **Tong** | **Pesh** | **Shom**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    async with aiohttp.ClientSession() as session:
        for vil, pos in list(VILOYATLAR.items())[:8]:
            url = f"https://islomapi.uz/api/present/day?region={pos['region']}"
            async with session.get(url) as r:
                v = (await r.json())['times']
                text += f"🔹 {vil[:6]:<6} | {v['tong_saharlik']} | {v['peshin']} | {v['shom_iftor']}\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

# --- 6. VIKTORINA (QIZIQARLI FAKTLAR) ---
async def job_viktorina():
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            q = (await r.json())['results'][0]
            savol = translator.translate(q['question'], dest='uz').text
            togri = translator.translate(q['correct_answer'], dest='uz').text
            javoblar = [translator.translate(a, dest='uz').text for a in q['incorrect_answers']] + [togri]
            random.shuffle(javoblar)
            await bot.send_poll(CHANNEL_ID, f"🤔 {savol}", javoblar, type='quiz', correct_option_id=javoblar.index(togri), is_anonymous=False)

# --- JADVAL ---
scheduler.add_job(job_ob_havo, 'cron', hour=5, minute=0)
scheduler.add_job(job_xayrli_tong, 'cron', hour=6, minute=0)
scheduler.add_job(job_kun_tarixi, 'cron', hour=7, minute=0)
scheduler.add_job(job_valyuta, 'cron', hour=10, minute=0)
scheduler.add_job(job_valyuta, 'cron', hour=14, minute=0)
scheduler.add_job(job_valyuta, 'cron', hour=18, minute=0)
scheduler.add_job(job_namoz, 'cron', hour=4, minute=30)
scheduler.add_job(job_viktorina, 'interval', hours=8) # Kuniga 3 marta

async def main():
    logging.basicConfig(level=logging.INFO)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
