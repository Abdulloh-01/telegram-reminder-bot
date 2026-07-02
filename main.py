import asyncio
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# Импорты вашей БД
from db import (
    add_user, 
    get_all_users,
    update_reminder_time,
    add_reminder,
    get_reminders,
    delete_reminder,
    get_all_reminders,
)

ADMIN_ID = 1375000407


import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Создать напоминание")],
        [KeyboardButton(text="📋 Мои напоминания")],
        [KeyboardButton(text="🗑 Удалить напоминание")]
    ],
    resize_keyboard=True
)

class ReminderState(StatesGroup):
    waiting_for_text = State()
    waiting_for_when = State()
    waiting_for_repeat = State()
    waiting_for_delete = State()

# Словарик для определения дней недели (0 - понедельник, 6 - воскресенье)
DAYS_OF_WEEK = {
    "понедельник": 0, "пон": 0, "пн": 0,
    "вторник": 1, "вт": 1,
    "среда": 2, "ср": 2,
    "четверг": 3, "чт": 3,
    "пятница": 4, "пт": 4,
    "суббота": 5, "суб": 5, "сб": 5,
    "воскресенье": 6, "воск": 6, "вс": 6
}

def parse_custom_datetime(user_input: str) -> datetime:
    """Умный парсер даты и времени из текста пользователя"""
    now = datetime.now()
    user_input = user_input.lower().strip()
    
    target_date = now.date()
    
    # 1. Проверяем день недели
    for day_name, day_num in DAYS_OF_WEEK.items():
        if day_name in user_input:
            current_day_num = now.weekday()
            # Считаем, сколько дней до нужного дня недели
            days_ahead = day_num - current_day_num
            if days_ahead <= 0:  # Если этот день на этой неделе уже прошел или сегодня
                days_ahead += 7  # Переносим на следующую неделю
            target_date = now.date() + timedelta(days=days_ahead)
            break
            
    # 2. Проверяем относительные слова "завтра" / "послезавтра"
    if "послезавтра" in user_input:
        target_date = now.date() + timedelta(days=2)
    elif "завтра" in user_input:
        target_date = now.date() + timedelta(days=1)
        
    # 3. Проверяем конкретную дату формата ДД.ММ.ГГГГ или ДД.ММ
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', user_input)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3)) if date_match.group(3) else now.year
        target_date = datetime(year, month, day).date()

    # 4. Ищем время (ЧЧ:ММ:СС или ЧЧ:ММ)
    time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', user_input)
    if not time_match:
        return None  # Если время вообще не введено, возвращаем ошибку
        
    hours = int(time_match.group(1))
    minutes = int(time_match.group(2))
    seconds = int(time_match.group(3)) if time_match.group(3) else 0
    
    # Собираем финальный datetime
    result_datetime = datetime.combine(target_date, datetime.min.time()).replace(
        hour=hours, minute=minutes, second=seconds, microsecond=0
    )
    
    # Если дата осталась сегодняшней, а время уже прошло — переносим на завтра
    if result_datetime <= now and "понедельник" not in user_input: 
        # (для дней недели перенос на +7 дней мы уже сделали выше)
        if not any(day in user_input for day in DAYS_OF_WEEK):
            result_datetime += timedelta(days=1)
            
    return result_datetime

@dp.message(CommandStart())
async def start(message: Message):
    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await message.answer(
        "👋 Добро пожаловать!\n"
        "Я бот для напоминаний.\n"
        "Если что то не понятно пропшите или выберите команду /help.\n"
        "<b>CEO Founder</b> - <a href='https://t.me/No_nameas'>@No_nameas</a>",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "👋 Добро пожаловать в секцию ПОМОЩЬ\n"
        "<b>Про бота:</b>\n\n"
        "• /start — запуск бота\n"
        "• Создание напоминаний\n"
        "• Просмотр напоминаний\n"
        "• Удаление напоминаний\n"
        "Для удаление напоминаний , нужно просто выбрать номер напоминания. Список отправляется с нумерациями",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )

@dp.message(F.text == "📋 Мои напоминания")
async def my_reminders(message: Message):
    reminders = get_reminders(message.from_user.id)
    if not reminders:
        await message.answer("📭 У вас пока нет напоминаний.")
        return

    text = "📋 Ваши напоминания:\n\n"
    for reminder_text, reminder_time in reminders:
        text += f"🕒 {reminder_time}\n📝 {reminder_text}\n\n"
    await message.answer(text)

# --- ШАГ 1: Запрашиваем текст ---
@dp.message(F.text == "➕ Создать напоминание")
async def create_reminder(message: Message, state: FSMContext):
    await state.set_state(ReminderState.waiting_for_text)
    await message.answer("📝 Напишите, о чем вам напомнить:")

# --- ШАГ 2: Сохраняем текст, запрашиваем дату/время ---
@dp.message(ReminderState.waiting_for_text)
async def get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    await state.set_state(ReminderState.waiting_for_when)
    await message.answer(
        "📅 Когда напомнить?\n\n"
        "Примеры ввода:\n"
        "• в понедельник в 12:30\n"
        "• пятница 18:00:45 (с секундами)\n"
        "• завтра в 10:00\n"
        "• сегодня в 12:00\n"
        "• 15.07.2026 в 15:00"
    )

# --- ШАГ 3: Распознаем дату и спрашиваем периодичность ---
@dp.message(ReminderState.waiting_for_when)
async def save_reminder(message: Message, state: FSMContext):
    user_input = message.text.strip()
    
    # Используем наш кастомный парсер
    reminder_datetime = parse_custom_datetime(user_input)
    
    if not reminder_datetime:
        await message.answer(
            "❌ Не удалось понять время. Пожалуйста, укажите время в формате ЧЧ:ММ или ЧЧ:ММ:СС.\n"
            "Пример: 'в понедельник в 12:30' или 'завтра в 09:15:30'"
        )
        return

    remind_time_str = reminder_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # Сохраняем время во временное состояние
    await state.update_data(remind_time=remind_time_str)
    await state.set_state(ReminderState.waiting_for_repeat)

    repeat_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Один раз")],
        [KeyboardButton(text="🔁 Каждый день")]
    ],
    resize_keyboard=True
)

    await message.answer(
        "🔁 Какое напоминание создать?",
        reply_markup=repeat_keyboard
    )

# obtobotka udaleniya
@dp.message(F.text == "🗑 Удалить напоминание")
async def delete_menu(message: Message, state: FSMContext):
    reminders = get_reminders(message.from_user.id)

    if not reminders:
        await message.answer("📭 У вас нет напоминаний.")
        return

    text = "🗑 Выберите номер напоминания для удаления:\n\n"

    for i, (reminder_text, reminder_time) in enumerate(reminders, start=1):
        text += (
            f"{i}. 🕒 {reminder_time}\n"
            f"   📝 {reminder_text}\n\n"
        )

    await state.update_data(reminders=reminders)
    await state.set_state(ReminderState.waiting_for_delete)

    await message.answer(text)

# obrobotka vibora
@dp.message(ReminderState.waiting_for_delete)
async def process_delete(message: Message, state: FSMContext):
    data = await state.get_data()
    reminders = data["reminders"]

    if not message.text.isdigit():
        await message.answer("Введите номер напоминания.")
        return

    index = int(message.text) - 1

    if index < 0 or index >= len(reminders):
        await message.answer("Такого номера нет.")
        return

    reminder_text, reminder_time = reminders[index]

    delete_reminder(
        message.from_user.id,
        reminder_text,
        reminder_time
    )

    await message.answer(
        "✅ Напоминание удалено.",
        reply_markup=main_keyboard
    )

    await state.clear()


# --- ШАГ 4: Обработка выбора повторения и финальное сохранение ---
@dp.message(ReminderState.waiting_for_repeat, F.text.in_({"❌ Один раз", "🔁 Каждый день"}))
async def process_repeat_choice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    text = user_data.get("text")
    remind_time_str = user_data.get("remind_time")
    
    is_daily = 1 if message.text == "🔁 Каждый день" else 0
    
    # Добавляем в БД (убедись, что твоя функция add_reminder принимает is_daily)
    # Если функция еще не принимает этот параметр, тебе нужно будет обновить базу данных.
    add_reminder(
    message.from_user.id,
    text,
    remind_time_str,
    is_daily
) 

    reminder_datetime = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    seconds_to_wait = (reminder_datetime - now).total_seconds()

    print("=== Создание напоминания ===")
    print(f"text={text}")
    print(f"time={remind_time_str}")
    print(f"seconds={seconds_to_wait}")

    asyncio.create_task(
        send_reminder_by_delay(
            message.chat.id,
            message.from_user.id,
            text,
            remind_time_str,
            seconds_to_wait,
            is_daily
        )
    )

    await message.answer(
        f"✅ Напоминание успешно создано!\n\n"
        f"📝 {text}\n"
        f"📅 Будет отправлено: {remind_time_str}\n"
        f"🔁 Тип: {message.text}",
        reply_markup=main_keyboard
    )
    await state.clear()

async def send_reminder_by_delay(chat_id, user_id, text, remind_time_str, seconds, is_daily=0):
    print("=== send_reminder_by_delay стартовала ===")
    print(f"seconds={seconds}")

    try:
        if seconds > 0:
            print("Начинаю ожидание...")
            await asyncio.sleep(seconds)

        print("Ожидание закончилось")
        print("Отправляю сообщение...")

        await bot.send_message(
            chat_id,
            f"🔔 <b>Напоминание!</b>\n\n📝 {text}",
            parse_mode="HTML"
        )

        print("Сообщение успешно отправлено")

        # ⬇️ Ниже должен идти твой старый код:
        if is_daily:
            ...
        else:
            ...

    except Exception as e:
        print(f"Ошибка отправки: {e}")

        # дальше оставь свой существующий код
    try:
        if seconds > 0:
            await asyncio.sleep(seconds)

        await bot.send_message(
            chat_id,
            f"🔔 <b>Напоминание!</b>\n\n📝 {text}",
            parse_mode="HTML"
        )

        if is_daily:
            # Переносим на следующий день
            old_date = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M:%S")
            new_date = old_date + timedelta(days=1)
            new_time_str = new_date.strftime("%Y-%m-%d %H:%M:%S")

            update_reminder_time(user_id, text, remind_time_str, new_time_str)

            # Запускаем таск заново на следующие 24 часа (86400 секунд)
            asyncio.create_task(
                send_reminder_by_delay(
                    chat_id,
                    user_id,
                    text,
                    new_time_str,
                    86400,
                    is_daily=1
                )
            )
        else:
            delete_reminder(user_id, text, remind_time_str)

    except Exception as e:
        print(f"Ошибка отправки: {e}")

async def load_reminders():
    try:
        reminders = get_all_reminders()
        now = datetime.now()
        for reminder in reminders:
            # Подстраиваем распаковку под твою структуру таблицы. 
            # Если возвращается 4 элемента (с is_daily):
            if len(reminder) == 4:
                user_id, text, remind_time_str, is_daily = reminder
            else:
                user_id, text, remind_time_str = reminder
                is_daily = 0
                
            try:
                rem_dt = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M:%S")
                seconds = (rem_dt - now).total_seconds()
                asyncio.create_task(
                    send_reminder_by_delay(user_id, user_id, text, remind_time_str, max(0, seconds), is_daily)
                )
            except ValueError:
                print(f"Ошибка формата даты в БД: {remind_time_str}")
    except Exception as e:
        print(f"Ошибка загрузки из БД: {e}")

async def main():
    print("Бот запущен!")
    await load_reminders()
    await dp.start_polling(bot)

@dp.message(F.text == "/users")
async def users_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()
    if not users:
        await message.answer("Пользователей нет.")
        return

    text = "👥 Пользователи:\n\n"
    for user_id, username, first_name, joined_at in users:
        username_text = f"@{username}" if username else "нет username"
        text += (
            f"👤 {first_name}\n"
            f"🆔 {user_id}\n"
            f"📛 {username_text}\n"
            f"📅 {joined_at}\n\n"
        )
    await message.answer(text)

@dp.message(F.text == "/all_reminders")
async def all_reminders(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    reminders = get_all_reminders()
    if not reminders:
        await message.answer("Напоминаний нет.")
        return

    text = "📋 Все напоминания пользователей:\n\n"
    current_user = None

    for reminder in reminders:
        user_id, reminder_text, reminder_time = reminder[0], reminder[1], reminder[2]

        if current_user != user_id:
            current_user = user_id
            text += f"\n👤 Пользователь: {user_id}\n"

        text += (
            f"🕒 {reminder_time}\n"
            f"📝 {reminder_text}\n\n"
        )

    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await message.answer(chunk)
    else:
        await message.answer(text)

if __name__ == "__main__":
    asyncio.run(main())