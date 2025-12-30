import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite

TOKEN = "YOUR_BOT_TOKEN"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Определяем состояния
class Booking(StatesGroup):
    name = State()
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

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Напиши /book чтобы записаться.")

@dp.message(Command("book"))
async def book(message: types.Message, state: FSMContext):
    await message.answer("Введите ваше имя:")
    await state.set_state(Booking.name)

@dp.message(Booking.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите дату (например: 2025-12-31):")
    await state.set_state(Booking.date)

@dp.message(Booking.date)
async def get_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("Введите время (например: 15:00):")
    await state.set_state(Booking.time)

@dp.message(Booking.time)
async def get_time(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    date = data["date"]
    time = message.text

    async with aiosqlite.connect("appointments.db") as db:
        await db.execute("INSERT INTO appointments (user_id, name, date, time) VALUES (?, ?, ?, ?)",
                         (message.from_user.id, name, date, time))
        await db.commit()

    await message.answer(f"✅ Запись создана!\nИмя: {name}\nДата: {date}\nВремя: {time}")
    await state.clear()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
