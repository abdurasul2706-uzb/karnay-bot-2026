import logging
import asyncio
import random
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from googletrans import Translator
from hijridate==2.3.0
pytz import Gregorian

# --- SOZLAMALAR ---
API_TOKEN = '8222976736:AAERrJbYXYiIhFpfwHttD9R5mAaql4iEgzs' 
CHANNEL_ID = '@Karnayuzb'  # Username to'g'riligini tekshiring
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
translator = Translator()

# 1. OB-HAVO KOORDINATALARI (Hududlar kesimida)
VILOYATLAR = {
    "Toshkent": (41.2995, 69.2401), "Andijon": (40.7833, 72.3333), "Buxoro": (39.7747, 64.4286),
    "Farg'ona": (40.3842, 71.7844), "Jizzax": (40.1158, 67.8422), "Xorazm": (41.5500, 60.6333),
    "Namangan": (41.0011, 71.6683), "Navoiy": (40.1031, 65.3739), "Qashqadaryo": (38.8610, 65.7847),
    "Samarqand": (39.6542, 66.9597), "Sirdaryo": (40.4939, 68.7703), "Surxondaryo": (37.2242, 67.2783),
    "Qoraqalpog'iston": (43.8041, 59.4457)
}

# --- RUKNLAR FUNKSIYALARI ---

# 1. OB-HAVO (05:00)
async def job_ob_havo():
    text = "🌤 **O'ZBEKISTON HUDUDLARI OB-HAVO MA'LUMOTI** 🌤\n"
    text += f"📅 Bugun: {datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')}\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += "📍 Hudud          |  Min  |  Max\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    
    async with aiohttp.ClientSession() as session:
        for vil, (lat, lon) in VILOYATLAR.items():
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            async with session.get(url) as r:
                data = await r.json()
                t_max, t_min = data['daily']['temperature_2m_max'][0], data['daily']['temperature_2m_min'][0]
                text += f"🔹 {vil:<14} | {t_min:+.1f}° | {t_max:+.1f}°\n"
    
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += f"📢 Kanalimiz: {CHANNEL_ID}"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

# 2. XAYRLI TONG (06:00)
async def job_xayrli_tong():
    now = datetime.now(TASHKENT_TZ)
    h = Gregorian(now.year, now.month, now.day).to_hijri()
    hafta = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"][now.weekday()]
    
    tilaklar = [
        "Assalomu alaykum! Bugun qalbingiz quvonchga, xonadoningiz barakaga to'lsin. Har bir qadamingiz xayrli bo'lsin!",
        "Xayrli tong! Yangi kun sizga kutilmagan baxt va bitmas-tuganmas kuch-quvvat olib kelsin. Muvaffaqiyat yoringiz bo'lsin!",
        "G'oyat go'zal tong muborak! Bugun nimaiki ezgu niyat qilgan bo'lsangiz, hammasi ijobat bo'lsin. Kayfiyatingiz a'lo bo'lsin!"
    ]
    
    msg = f"☀️ **XAYRLI TONG, AZIZLAR!**\n\n"
    msg += f"📅 Bugun: {now.strftime('%d.%m.%Y')}-yil\n"
    msg += f"🌙 Hijriy: {h.day}-{h.month_name()} {h.year}-yil\n"
    msg += f"🗓 Hafta kuni: {hafta}\n\n"
    msg += f"✨ {random.choice(tilaklar)}\n\n"
    msg += f"🔗 Obuna bo'ling: {CHANNEL_ID}"
    await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# 3. KUN TARIXI (07:00)
async def job_kun_tarixi():
    now = datetime.now(TASHKENT_TZ)
    url = f"https://uz.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.strftime('%m/%d')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            events = data.get('selected', [])[:4]
            msg = f"📜 **TARIXDA BUGUN ({now.strftime('%d-%B')})**\n\n"
            for ev in events:
                try:
                    text_uz = translator.translate(ev['text'], dest='uz').text
                    msg += f"🗓 **{ev['year']}-yil:**\n{text_uz}\n\n"
                except: continue
            msg += f"🚀 Batafsil: {CHANNEL_ID}"
            await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# 4. DOLLAR KURSI (10:00)
async def job_valyuta():
    url = "https://nbu.uz/uz/exchange-rates/json/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            usd = next(x for x in data if x["code"] == "USD")
            msg = f"🏦 **BANKLARDA VALYUTA KURSI (USD)**\n\n"
            msg += f"🇺🇸 1 AQSH Dollari:\n"
            msg += f"📈 Markaziy Bank: {usd['cb_price']} so'm\n"
            msg += f"💰 Sotib olish: {usd['nbu_buy_price']} so'm\n"
            msg += f"💸 Sotish: {usd['nbu_cell_price']} so'm\n\n"
            msg += "⚠️ Kurslar banklarda biroz farq qilishi mumkin.\n"
            msg += f"🔗 Kanal: {CHANNEL_ID}"
            await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# 5. VIKTORINA (Har 4 soatda)
async def job_viktorina():
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            d = await r.json()
            q = d['results'][0]
            savol = translator.translate(q['question'], dest='uz').text
            javoblar = [translator.translate(a, dest='uz').text for a in q['incorrect_answers']]
            togri = translator.translate(q['correct_answer'], dest='uz').text
            javoblar.append(togri)
            random.shuffle(javoblar)
            await bot.send_poll(CHANNEL_ID, savol, javoblar, type='quiz', correct_option_id=javoblar.index(togri), is_anonymous=False)

# 6. NAMOZ VAQTLARI (22:00 da ertangi kun uchun)
async def job_namoz():
    url = "https://islomapi.uz/api/present/day?region=Toshkent"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            v = (await r.json())['times']
            msg = f"🕌 **NAMOZ VAQTLARI (Toshkent)**\n\n"
            msg += f"🕋 Saharlik: {v['tong_saharlik']}\n☀️ Quyosh: {v['quyosh']}\n"
            msg += f"🌤 Peshin: {v['peshin']}\n🌇 Asr: {v['asr']}\n"
            msg += f"🌆 Shom: {v['shom_iftor']}\n🌃 Xufton: {v['xufton']}\n\n"
            msg += f"📢 @Islomuz ma'lumotlari asosida\n🔗 {CHANNEL_ID}"
            await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# --- ISHGA TUSHIRISH ---
scheduler.add_job(job_ob_havo, 'cron', hour=5, minute=0)
scheduler.add_job(job_xayrli_tong, 'cron', hour=6, minute=0)
scheduler.add_job(job_kun_tarixi, 'cron', hour=7, minute=0)
scheduler.add_job(job_valyuta, 'cron', hour=10, minute=0)
scheduler.add_job(job_viktorina, 'interval', hours=4)
scheduler.add_job(job_namoz, 'cron', hour=22, minute=0)

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
