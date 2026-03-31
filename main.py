import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv() 

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if TOKEN is None:
    raise ValueError("❌ BOT_TOKEN не найден. Проверь .env файл!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# FSM состояния
class Booking(StatesGroup):
    date = State()
    time = State()

# Инициализация базы
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

# Логика бронирования
@dp.callback_query(F.data == "book")
async def book_date_selection(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2025-12-31", callback_data="date:2025-12-31")],
        [InlineKeyboardButton(text="2026-01-01", callback_data="date:2026-01-01")]
    ])
    await callback.message.edit_text("Выберите дату:", reply_markup=kb)
    await state.set_state(Booking.date)

@dp.callback_query(F.data.startswith("date:"))
async def book_time_selection(callback: types.CallbackQuery, state: FSMContext):
    date = callback.data.split(":")[1]
    await state.update_data(date=date)
    async with aiosqlite.connect("appointments.db") as db:
        times = ["10:00", "12:00", "15:00"]
        kb_list = []
        for t in times:
            cursor = await db.execute("SELECT 1 FROM appointments WHERE date=? AND time=?", (date, t))
            if await cursor.fetchone():
                kb_list.append([InlineKeyboardButton(text=f"{t} ❌", callback_data="busy")])
            else:
                kb_list.append([InlineKeyboardButton(text=t, callback_data=f"time:{t}")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await callback.message.edit_text(f"Вы выбрали дату {date}. Теперь выберите время:", reply_markup=kb)
    await state.set_state(Booking.time)

@dp.callback_query(F.data.startswith("time:"))
async def book_finish(callback: types.CallbackQuery, state: FSMContext):
    time = callback.data.split(":")[1]
    data = await state.get_data()
    date = data.get("date")
    async with aiosqlite.connect("appointments.db") as db:
        await db.execute("INSERT INTO appointments (user_id, name, date, time) VALUES (?, ?, ?, ?)",
                         (callback.from_user.id, callback.from_user.full_name, date, time))
        await db.commit()
    await callback.message.edit_text(f"✅ Запись создана!\nДата: {date}\nВремя: {time}")
    await state.clear()

@dp.callback_query(F.data == "busy")
async def slot_busy(callback: types.CallbackQuery):
    await callback.answer("Это время уже занято!", show_alert=True)

@dp.callback_query(F.data == "my_records")
async def my_records(callback: types.CallbackQuery):
    async with aiosqlite.connect("appointments.db") as db:
        cursor = await db.execute("SELECT id, date, time FROM appointments WHERE user_id=?", (callback.from_user.id,))
        records = await cursor.fetchall()
    if records:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"❌ Отменить {d} {t}", callback_data=f"cancel:{rid}")]
            for rid, d, t in records
        ])
        await callback.message.answer("Ваши записи (нажмите на кнопку для отмены):", reply_markup=kb)
    else:
        await callback.message.answer("У вас пока нет записей.")

@dp.callback_query(F.data.startswith("cancel:"))
async def cancel_record(callback: types.CallbackQuery):
    rid = int(callback.data.split(":")[1])
    async with aiosqlite.connect("appointments.db") as db:
        # Проверяем владельца записи перед удалением
        cursor = await db.execute("SELECT 1 FROM appointments WHERE id=? AND user_id=?", (rid, callback.from_user.id))
        if await cursor.fetchone():
            await db.execute("DELETE FROM appointments WHERE id=?", (rid,))
            await db.commit()
            await callback.message.edit_text(f"🗑 Ваша запись №{rid} успешно отменена.")
        else:
            await callback.answer("Запись не найдена или уже удалена.")

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
@dp.callback_query(F.data.startswith("del:"))
async def admin_delete(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        rid = int(callback.data.split(":")[1])
        async with aiosqlite.connect("appointments.db") as db:
            await db.execute("DELETE FROM appointments WHERE id=?", (rid,))
            await db.commit()
        await callback.message.edit_text(f"🗑 Запись {rid} удалена администратором.")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())