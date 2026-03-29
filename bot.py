import os
import asyncio
import sqlite3
import requests
import random
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Sozlamalar
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 123456789  # SHU YERGA O'ZINGIZNING TELEGRAM ID'INGIZNI YOZING (Masalan: @userinfobot orqali bilish mumkin)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Ma'lumotlar bazasini sozlash
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS allowed_users (user_id INTEGER PRIMARY KEY)')
conn.commit()

# --- Yordamchi funksiyalar ---
def is_allowed(user_id):
    if user_id == ADMIN_ID: return True
    cursor.execute('SELECT * FROM allowed_users WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None

async def check_tme(username):
    url = f"https://t.me/{username}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text().lower()
            if "view in telegram" in text and "if you have telegram" not in text:
                return "band ❌"
            elif "auction" in text or "buy on fragment" in text:
                return "fragment 💰"
            else:
                return "bo'sh ✅"
    except:
        return "xatolik ⚠️"
    return "aniqlanmadi ❓"

# --- Admin buyruqlari ---
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = ("👑 **Admin Panel**\n\n"
            "👤 `/add ID` — Foydalanuvchiga ruxsat berish\n"
            "🗑 `/rem ID` — Ruxsatni olib tashlash\n"
            "📋 `/list` — Ruxsat berilganlar ro'yxati")
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler(commands=['add'])
async def add_user(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        user_id = int(message.get_args())
        cursor.execute('INSERT OR IGNORE INTO allowed_users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        await message.answer(f"✅ ID {user_id} ga ruxsat berildi.")
    except:
        await message.answer("❌ Xato! Foydalanish: `/add 1234567`")

@dp.message_handler(commands=['list'])
async def list_users(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute('SELECT user_id FROM allowed_users')
    users = cursor.fetchall()
    text = "📋 **Ruxsat berilgan ID'lar:**\n\n" + "\n".join([f"• `{u[0]}`" for u in users])
    await message.answer(text if users else "Ro'yxat bo'sh", parse_mode="Markdown")

# --- Asosiy mantiq ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔️ Kechirasiz, sizga ushbu botdan foydalanishga ruxsat berilmagan.\nID'ngiz: `{}`".format(message.from_user.id), parse_mode="Markdown")
        return
    await message.answer("Salom! Username diapazonini yuboring.\nMasalan: `vip_100 vip_120`", parse_mode="Markdown")

@dp.message_handler()
async def start_check(message: types.Message):
    if not is_allowed(message.from_user.id): return

    args = message.text.split()
    if len(args) < 2 or "_" not in args[0]:
        await message.answer("Iltimos, formatni to'g'ri yozing: `prefix_001 prefix_010`")
        return

    try:
        prefix = args[0].split('_')[0] + "_"
        start_num = int(args[0].split('_')[1])
        end_num = int(args[1].split('_')[1])
    except:
        await message.answer("❌ Xato! Raqamlarni to'g'ri ko'rsating.")
        return

    status_msg = await message.answer("🔍 Tekshirish boshlanmoqda...")
    report_text = f"🔍 **Natijalar (@{prefix}...):**\n\n"

    for i in range(start_num, end_num + 1):
        username = f"{prefix}{str(i).zfill(3)}"
        status = await check_tme(username)
        report_text += f"@{username} — {status}\n"
        
        if i % 3 == 0 or i == end_num:
            try:
                await status_msg.edit_text(report_text, parse_mode="Markdown")
            except: pass
        await asyncio.sleep(2)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
  
