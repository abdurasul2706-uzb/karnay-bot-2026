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

# --- RENDER PORT XATOSINI TUZATISH ---
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")
    
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
    "Samarqand": {"lat": 39.6542, "lon": 66.9597, "region": "Samarqand"},
    "Namangan": {"lat": 41.0011, "lon": 71.6683, "region": "Namangan"},
    "Xorazm": {"lat": 41.5500, "lon": 60.6333, "region": "Urganch"}
}

# --- RUKNLAR ---

async def job_ob_havo():
    text = "🌤 **VILOYATLAR OB-HAVO MA'LUMOTI**\n"
    text += f"📅 Bugun: {datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')}\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    async with aiohttp.ClientSession() as session:
        for vil, pos in VILOYATLAR.items():
            url = f"https://api.open-meteo.com/v1/forecast?latitude={pos['lat']}&longitude={pos['lon']}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            async with session.get(url) as r:
                data = await r.json()
                t_max, t_min = data['daily']['temperature_2m_max'][0], data['daily']['temperature_2m_min'][0]
                text += f"🔹 {vil:<10} | {t_min:+.1f}°...{t_max:+.1f}°\n"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

async def job_xayrli_tong():
    now = datetime.now(TASHKENT_TZ)
    h = Gregorian(now.year, now.month, now.day).to_hijri()
    hafta = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"][now.weekday()]
    tilak = "Assalomu alaykum! Yangi kun muborak bo'lsin. Alloh xonadoningizga fayz va baraka, qalbingizga xotirjamlik bersin. Bugungi kuningiz kechagidan unumliroq o'tsin!"
    
    msg = f"☀️ **XAYRLI TONG!**\n\n"
    msg += f"📅 **Milodiy:** {now.strftime('%d.%m.%Y')}\n"
    msg += f"🌙 **Hijriy:** {h.day}-{h.month_name()} {h.year}\n"
    msg += f"🗓 **Kun:** {hafta}\n\n"
    msg += f"✨ {tilak}\n\n"
    msg += f"🔗 {CHANNEL_ID}"
    await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

async def job_valyuta():
    url_cb = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    url_nbu = "https://nbu.uz/uz/exchange-rates/json/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_cb) as r1:
            cb_usd = next(x for x in (await r1.json()) if x["Code"] == "840")
        async with session.get(url_nbu) as r2:
            nbu_usd = (await r2.json())[0]
            
    msg = f"🏦 **USD KURSI - {cb_usd['Date']}**\n"
    msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    msg += f"📈 Markaziy Bank: {cb_usd['Rate']} so'm\n"
    msg += f"💰 Sotib olish: {nbu_usd['nbu_buy_price']} so'm\n"
    msg += f"💸 Sotish: {nbu_usd['nbu_cell_price']} so'm\n"
    msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

async def job_namoz():
    text = "🕌 **NAMOZ VAQTLARI**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    async with aiohttp.ClientSession() as session:
        for vil, pos in list(VILOYATLAR.items())[:5]:
            url = f"https://islomapi.uz/api/present/day?region={pos['region']}"
            async with session.get(url) as r:
                v = (await r.json())['times']
                text += f"🔹 {vil[:6]}: T:{v['tong_saharlik']} P:{v['peshin']} S:{v['shom_iftor']}\n"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

# --- JADVAL VA START ---
scheduler.add_job(job_ob_havo, 'cron', hour=5, minute=0)
scheduler.add_job(job_xayrli_tong, 'cron', hour=6, minute=0)
scheduler.add_job(job_valyuta, 'cron', hour=10, minute=0)
scheduler.add_job(job_namoz, 'cron', hour=18, minute=0)

async def main():
    logging.basicConfig(level=logging.INFO)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
