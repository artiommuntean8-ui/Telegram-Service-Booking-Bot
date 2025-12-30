import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiosqlite

TOKEN = "8045823678:AAEjw2gvzK7PfrPpgKB_KWyNQKjgH99CBZU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаем таблицу для записей
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
    await message.answer("Привет! Я бот для записи на услуги.\nНапиши /book чтобы записаться.")

@dp.message(Command("book"))
async def book(message: types.Message):
    await message.answer("Введите ваше имя:")

    @dp.message()
    async def get_name(msg: types.Message):
        name = msg.text
        await msg.answer("Введите дату (например: 2025-12-31):")

        @dp.message()
        async def get_date(msg2: types.Message):
            date = msg2.text
            await msg2.answer("Введите время (например: 15:00):")

            @dp.message()
            async def get_time(msg3: types.Message):
                time = msg3.text
                async with aiosqlite.connect("appointments.db") as db:
                    await db.execute("INSERT INTO appointments (user_id, name, date, time) VALUES (?, ?, ?, ?)",
                                     (msg3.from_user.id, name, date, time))
                    await db.commit()
                await msg3.answer(f"✅ Запись создана!\nИмя: {name}\nДата: {date}\nВремя: {time}")
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
