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
from hijridate import Gregorian

# --- SOZLAMALAR ---
API_TOKEN = '8222976736:AAERrJbYXYiIhFpfwHttD9R5mAaql4iEgzs' 
CHANNEL_ID = '@Karnayuzb'
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
translator = Translator()

# 1. HUDUDLAR (Ob-havo va Namoz uchun)
VILOYATLAR = {
    "Toshkent": {"lat": 41.2995, "lon": 69.2401, "region": "Toshkent"},
    "Andijon": {"lat": 40.7833, "lon": 72.3333, "region": "Andijon"},
    "Buxoro": {"lat": 39.7747, "lon": 64.4286, "region": "Buxoro"},
    "Farg'ona": {"lat": 40.3842, "lon": 71.7844, "region": "Farg'ona"},
    "Jizzax": {"lat": 40.1158, "lon": 67.8422, "region": "Jizzax"},
    "Xorazm": {"lat": 41.5500, "lon": 60.6333, "region": "Urganch"},
    "Namangan": {"lat": 41.0011, "lon": 71.6683, "region": "Namangan"},
    "Navoiy": {"lat": 40.1031, "lon": 65.3739, "region": "Navoiy"},
    "Qashqadaryo": {"lat": 38.8610, "lon": 65.7847, "region": "Qarshi"},
    "Samarqand": {"lat": 39.6542, "lon": 66.9597, "region": "Samarqand"},
    "Sirdaryo": {"lat": 40.4939, "lon": 68.7703, "region": "Guliston"},
    "Surxondaryo": {"lat": 37.2242, "67.2783": 67.2783, "region": "Termiz"},
    "Qoraqalpog'iston": {"lat": 43.8041, "lon": 59.4457, "region": "Nukus"}
}

# --- RUKNLAR ---

# 1. OB-HAVO (Viloyatlar kesimida)
async def job_ob_havo():
    text = "🌤 **O'ZBEKISTON HUDUDLARI OB-HAVO MA'LUMOTI** 🌤\n"
    text += f"📅 Bugun: {datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')}\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += "📍 **Hudud** |  **Min** |  **Max**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    async with aiohttp.ClientSession() as session:
        for vil, pos in VILOYATLAR.items():
            url = f"https://api.open-meteo.com/v1/forecast?latitude={pos['lat']}&longitude={pos['lon']}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            async with session.get(url) as r:
                data = await r.json()
                t_max, t_min = data['daily']['temperature_2m_max'][0], data['daily']['temperature_2m_min'][0]
                text += f"🔹 {vil:<14} | {t_min:+.1f}° | {t_max:+.1f}°\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += f"📢 Kanalimiz: {CHANNEL_ID}"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

# 2. XAYRLI TONG (Milodiy/Hijriy, Hafta kuni, Shirin tilaklar)
async def job_xayrli_tong():
    now = datetime.now(TASHKENT_TZ)
    h = Gregorian(now.year, now.month, now.day).to_hijri()
    hafta = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"][now.weekday()]
    
    tilaklar = [
        "Assalomu alaykum va rohmatullohi va barokatuh! Ushbu tong sizga xayrli bo'lsin. Qalbingiz iymon nuriga, xonadoningiz esa fayz-u barakaga to'lsin. Bugun rejalashtirgan har bir ezgu ishingiz ijobat bo'lsin!",
        "Xayrli tong, aziz dindoshim! Yangi kun muborak! Alloh bugungi kuningizni kechagidan unumli, quvonchli va savobli qilsin. Yuzingizdan tabassum, tilingizdan shirin so'z arimasin!",
        "G'oyat go'zal tong barchangizga muborak bo'lsin! Bugun nimaiki yaxshi niyat qilgan bo'lsangiz, hammasiga yetishing. Muvaffaqiyatlar eshigi siz uchun hamisha ochiq bo'lsin!"
    ]
    
    msg = f"☀️ **XAYRLI TONG, AZIZLAR!**\n\n"
    msg += f"📅 **Milodiy:** {now.strftime('%d.%m.%Y')}-yil\n"
    msg += f"🌙 **Hijriy:** {h.day}-{h.month_name()} {h.year}-yil\n"
    msg += f"🗓 **Hafta kuni:** {hafta}\n\n"
    msg += f"✨ {random.choice(tilaklar)}\n\n"
    msg += f"🔗 Obuna bo'ling: {CHANNEL_ID}"
    await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# 3. KUN TARIXI (Tarixiy voqealar va shaxslar)
async def job_kun_tarixi():
    now = datetime.now(TASHKENT_TZ)
    url = f"https://uz.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.strftime('%m/%d')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            events = data.get('selected', [])[:5]
            msg = f"📜 **TARIXDA BUGUN ({now.strftime('%d-%B')})**\n"
            msg += "Bugun tarix sahifalarida qolgan muhim voqealar:\n\n"
            for ev in events:
                try:
                    text_uz = translator.translate(ev['text'], dest='uz').text
                    msg += f"🔹 **{ev['year']}-yil:**\n{text_uz}\n\n"
                except: continue
            msg += f"🚀 Batafsil: {CHANNEL_ID}"
            await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# 4. VALYUTA KURSI (Markaziy bank va Banklar infografikasi)
async def job_valyuta():
    # Markaziy bank API (Hamma bank ma'lumotlari uchun eng yaxshisi)
    url_cb = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    url_banks = "https://nbu.uz/uz/exchange-rates/json/"
    
    async with aiohttp.ClientSession() as session:
        # Markaziy Bank kursi
        async with session.get(url_cb) as r1:
            cb_data = await r1.json()
            cb_usd = next(x for x in cb_data if x["Code"] == "840")
            
        # Banklardagi kurslar
        async with session.get(url_banks) as r2:
            bank_data = await r2.json()
            # NBU ma'lumotidan tashqari boshqa banklarni ham olish mumkin, lekin NBU API eng barqarori
            
        msg = f"🏦 **VALYUTA KURSLARI (USD) - {cb_usd['Date']}**\n\n"
        msg += f"📈 **Markaziy Bank:** {cb_usd['Rate']} so'm\n"
        msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        msg += "🏛 **Tijorat banklarida sotish/sotib olish:**\n\n"
        msg += f"💰 Sotib olish: {bank_data[0].get('nbu_buy_price', 'Noma`lum')} so'm\n"
        msg += f"💸 Sotish: {bank_data[0].get('nbu_cell_price', 'Noma`lum')} so'm\n"
        msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        msg += "⚠️ Eslatma: Kurslar kun davomida o'zgarishi mumkin.\n"
        msg += f"🔗 Kanalimiz: {CHANNEL_ID}"
        await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.MARKDOWN)

# 5. VIKTORINA (Qiziqarli faktlar - kuniga 3 marta)
async def job_viktorina():
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            d = await r.json()
            q = d['results'][0]
            savol = translator.translate(q['question'], dest='uz').text
            togri = translator.translate(q['correct_answer'], dest='uz').text
            javoblar = [translator.translate(a, dest='uz').text for a in q['incorrect_answers']]
            javoblar.append(togri)
            random.shuffle(javoblar)
            await bot.send_poll(CHANNEL_ID, f"🤔 {savol}", javoblar, type='quiz', correct_option_id=javoblar.index(togri), is_anonymous=False)

# 6. NAMOZ VAQTLARI (Hududlar kesimida)
async def job_namoz():
    text = "🕌 **NAMOZ VAQTLARI (O'ZBEKISTON)** 🕌\n"
    text += f"📅 Sana: {datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')}\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += "📍 **Hudud** | **Tong** | **Peshin** | **Asr** | **Shom** | **Xufton**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    
    async with aiohttp.ClientSession() as session:
        for vil, pos in VILOYATLAR.items():
            url = f"https://islomapi.uz/api/present/day?region={pos['region']}"
            async with session.get(url) as r:
                if r.status == 200:
                    v = (await r.json())['times']
                    text += f"🔹 {vil:<8} | {v['tong_saharlik']} | {v['peshin']} | {v['asr']} | {v['shom_iftor']} | {v['xufton']}\n"
    
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    text += f"📢 @Islomuz ma'lumotlari asosida\n🔗 {CHANNEL_ID}"
    await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.MARKDOWN)

# --- ISHGA TUSHIRISH (Schedulers) ---
scheduler.add_job(job_ob_havo, 'cron', hour=5, minute=0) # 05:00
scheduler.add_job(job_xayrli_tong, 'cron',
