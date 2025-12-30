import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite

TOKEN = "8045823678:AAEjw2gvzK7PfrPpgKB_KWyNQKjgH99CBZU"
ADMIN_ID = 123456789  # твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# FSM состояния
class Booking(StatesGroup):
    date = State()
    time = State()

async def init_db():
    async with aiosqlite.connect("appointments.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                date TEXT,
                time TEXT
            )
        """)
        await db.commit()

# Старт
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Записаться", callback_data="book")],
        [InlineKeyboardButton(text="Мои записи", callback_data="my_records")]
    ])
    await message.answer("Привет! Я бот для записи на услуги.", reply_markup=kb)

# Кнопки
@dp.callback_query()
async def callbacks(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "book":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="2025-12-31", callback_data="date:2025-12-31")],
            [InlineKeyboardButton(text="2026-01-01", callback_data="date:2026-01-01")]
        ])
        await callback.message.answer("Выберите дату:", reply_markup=kb)
        await state.set_state(Booking.date)

    elif callback.data.startswith("date:"):
        date = callback.data.split(":")[1]
        await state.update_data(date=date)

        # Проверяем занятость слотов
        async with aiosqlite.connect("appointments.db") as db:
            times = ["10:00", "12:00", "15:00"]
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            for t in times:
                cursor = await db.execute("SELECT * FROM appointments WHERE date=? AND time=?", (date, t))
                busy = await cursor.fetchone()
                if busy:
                    kb.inline_keyboard.append([InlineKeyboardButton(text=f"{t} ❌", callback_data="busy")])
                else:
                    kb.inline_keyboard.append([InlineKeyboardButton(text=t, callback_data=f"time:{t}")])
        await callback.message.answer(f"Вы выбрали дату {date}. Теперь выберите время:", reply_markup=kb)
        await state.set_state(Booking.time)

    elif callback.data.startswith("time:"):
        time = callback.data.split(":")[1]
        data = await state.get_data()
        date = data["date"]

        async with aiosqlite.connect("appointments.db") as db:
            await db.execute("INSERT INTO appointments (user_id, name, date, time) VALUES (?, ?, ?, ?)",
                             (callback.from_user.id, callback.from_user.full_name, date, time))
            await db.commit()

        await callback.message.answer(f"✅ Запись создана!\nДата: {date}\nВремя: {time}")
        await state.clear()

    elif callback.data == "my_records":
        async with aiosqlite.connect("appointments.db") as db:
            cursor = await db.execute("SELECT date, time FROM appointments WHERE user_id=?", (callback.from_user.id,))
            records = await cursor.fetchall()
        if records:
            text = "\n".join([f"{d} {t}" for d, t in records])
            await callback.message.answer(f"Ваши записи:\n{text}")
        else:
            await callback.message.answer("У вас пока нет записей.")

# Админ‑панель
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        async with aiosqlite.connect("appointments.db") as db:
            cursor = await db.execute("SELECT id, name, date, time FROM appointments")
            records = await cursor.fetchall()
        if records:
            text = "\n".join([f"{rid}. {n} — {d} {t}" for rid, n, d, t in records])
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"Удалить запись {rid}", callback_data=f"del:{rid}")]
                for rid, _, _, _ in records
            ])
            await message.answer(f"📋 Все записи:\n{text}", reply_markup=kb)
        else:
            await message.answer("Записей пока нет.")
    else:
        await message.answer("⛔ У вас нет доступа к админ‑панели.")

# Удаление записи
@dp.callback_query()
async def admin_delete(callback: types.CallbackQuery):
    if callback.data.startswith("del:") and callback.from_user.id == ADMIN_ID:
        rid = int(callback.data.split(":")[1])
        async with aiosqlite.connect("appointments.db") as db:
            await db.execute("DELETE FROM appointments WHERE id=?", (rid,))
            await db.commit()
        await callback.message.answer(f"🗑 Запись {rid} удалена.")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())