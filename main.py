import asyncio
import re
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Импорты твоей БД (остаются без изменений)
from db import (
    add_user, 
    get_all_users,
    update_reminder_time,
    add_reminder,
    get_reminders,
    delete_reminder,
    get_all_reminders,
)

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = 1375000407
USER_TZ = 5 

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
MESSAGES = {
    "ru": {
        "start": "👋 Добро пожаловать!\nЯ бот для напоминаний.\nЕсли что-то не понятно, пропишите или выберите команду /help.\n<b>CEO Founder</b> - <a href='https://t.me/No_nameas'>@No_nameas</a>",
        "help": "👋 Добро пожаловать в секцию ПОМОЩЬ\n<b>Про бота:</b>\n\n• /start — запуск бота\n• Создание напоминаний\n• Просмотр напоминаний\n• Удаление напоминаний\nДля удаления напоминания просто введите его номер из списка.",
        "btn_create": "➕ Создать напоминание",
        "btn_my": "📋 Мои напоминания",
        "btn_delete": "🗑 Удалить напоминание",
        "btn_once": "❌ Один раз",
        "btn_daily": "🔁 Каждый день",
        "no_reminders": "📭 У вас пока нет напоминаний.",
        "your_reminders": "📋 Ваши напоминания:\n\n",
        "ask_text": "📝 Напишите, о чем вам напомнить:",
        "ask_when": "📅 Когда напомнить?\n\nПримеры ввода:\n• в понедельник в 12:30\n• пятница 18:00\n• завтра в 10:00\n• сегодня в 12:00",
        "parse_error": "❌ Не удалось понять время. Кажется, вы забыли указать ЧЧ:ММ.",
        "ask_repeat": "🔁 Какое напоминание создать?",
        "choose_delete": "🗑 Выберите номер напоминания для удаления:\n\n",
        "nan_error": "Введите номер напоминания.",
        "index_error": "Такого номера нет.",
        "deleted": "✅ Напоминание удалено.",
        "created": "✅ Напоминание успешно создано!\n\n📝 {text}\n📅 Будет отправлено: {time}\n🔁 Тип: {repeat}",
        "notify": "🔔 <b>Напоминание!</b>\n\n📝 {text}"
    },
    "en": {
        "start": "👋 Welcome!\nI am a reminder bot.\nIf anything is unclear, type or choose the /help command.\n<b>CEO Founder</b> - <a href='https://t.me/No_nameas'>@No_nameas</a>",
        "help": "👋 Welcome to the HELP section\n<b>About bot:</b>\n\n• /start — start the bot\n• Create reminders\n• View reminders\n• Delete reminders\nTo delete a reminder, just enter its number from the list.",
        "btn_create": "➕ Create a reminder",
        "btn_my": "📋 My reminders",
        "btn_delete": "🗑 Delete a reminder",
        "btn_once": "❌ Once",
        "btn_daily": "🔁 Every day",
        "no_reminders": "📭 You have no reminders yet.",
        "your_reminders": "📋 Your reminders:\n\n",
        "ask_text": "📝 Write down what you want me to remind you about:",
        "ask_when": "📅 When should I remind you?\n\nExamples of input:\n• on Monday at 12:30\n• Friday 18:00\n• tomorrow at 10:00 am\n• today at 12 pm",
        "parse_error": "❌ Could not understand the time. It seems you forgot to specify HH:MM.",
        "ask_repeat": "🔁 What type of reminder should I create?",
        "choose_delete": "🗑 Choose the reminder number to delete:\n\n",
        "nan_error": "Please enter a reminder number.",
        "index_error": "No such number exists.",
        "deleted": "✅ Reminder deleted.",
        "created": "✅ Reminder successfully created!\n\n📝 {text}\n📅 Will be sent: {time}\n🔁 Type: {repeat}",
        "notify": "🔔 <b>Reminder!</b>\n\n📝 {text}"
    },
    "uz": {
        "start": "👋 Xush kelibsiz!\nMen eslatmalar botiman.\nAgar biror narsa tushunarsiz bo'lsa, /help buyrug'ini yozing yoki tanlang.\n<b>CEO Founder</b> - <a href='https://t.me/No_nameas'>@No_nameas</a>",
        "help": "👋 YORDAM bo'limiga xush kelibsiz\n<b>Bot haqida:</b>\n\n• /start — botni ishga tushirish\n• Eslatmalar yaratish\n• Eslatmalarni ko'rish\n• Eslatmalarni o'chirish\nEslatmani o'chirish uchun ro'yxatdan uning raqamini kiriting.",
        "btn_create": "➕ Eslatma yaratish",
        "btn_my": "📋 Mening eslatmalarim",
        "btn_delete": "🗑 Eslatmani o'chirish",
        "btn_once": "❌ Bir marta",
        "btn_daily": "🔁 Har kuni",
        "no_reminders": "📭 Sizda hali eslatmalar yo'q.",
        "your_reminders": "📋 Sizning eslatmalaringiz:\n\n",
        "ask_text": "📝 Nimani eslatishim kerakligini yozing:",
        "ask_when": "📅 Qachon eslatay?\n\nKiritishga misollar:\n• dushanba kuni soat 12:30 da\n• juma 18:00\n• ertaga soat 10:00 da\n• bugun soat 12:00 da",
        "parse_error": "❌ Vaqtni tushunib bo'lmadi. Soat va daqiqani (SS:MM) ko'rsatishni unutgandekmiz.",
        "ask_repeat": "🔁 Qanday eslatma yaratamiz?",
        "choose_delete": "🗑 O'chirish uchun eslatma raqamini tanlang:\n\n",
        "nan_error": "Eslatma raqamini kiriting.",
        "index_error": "Bunday raqam mavjud emas.",
        "deleted": "✅ Eslatma o'chirildi.",
        "created": "✅ Eslatma muvaffaqiyatli yaratildi!\n\n📝 {text}\n📅 Yuborilish vaqti: {time}\n🔁 Turi: {repeat}",
        "notify": "🔔 <b>Eslatma!</b>\n\n📝 {text}"
    }
}

# --- МУЛЬТИЯЗЫЧНЫЕ ДНИ НЕДЕЛИ ---
DAYS_OF_WEEK = {
    # Русский
    "понедельник": 0, "пон": 0, "пн": 0, "вторник": 1, "вт": 1, "среда": 2, "ср": 2,
    "четверг": 3, "чт": 3, "пятница": 4, "пт": 4, "суббота": 5, "суб": 5, "сб": 5, "воскресенье": 6, "воск": 6, "вс": 6,
    # English
    "monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "wednesday": 2, "wed": 2, "thursday": 3, "thu": 3, "friday": 4, "fri": 4, "saturday": 5, "sat": 5, "sunday": 6, "sun": 6,
    # O'zbekcha
    "dushanba": 0, "dush": 0, "seshanba": 1, "sesh": 1, "chorshanba": 2, "chor": 2, "payshanba": 3, "pay": 3, "juma": 4, "shanba": 5, "yakshanba": 6, "yak": 6
}

# Клавиатура выбора языка
lang_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇸 English"), KeyboardButton(text="🇺🇿 O'zbekcha")]
    ],
    resize_keyboard=True
)

def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MESSAGES[lang]["btn_create"])],
            [KeyboardButton(text=MESSAGES[lang]["btn_my"])],
            [KeyboardButton(text=MESSAGES[lang]["btn_delete"])]
        ],
        resize_keyboard=True
    )

class ReminderState(StatesGroup):
    waiting_for_lang = State()
    waiting_for_text = State()
    waiting_for_when = State()
    waiting_for_repeat = State()
    waiting_for_delete = State()

def parse_custom_datetime(user_input: str) -> datetime:
    """Умный мультиязычный парсер даты и времени с поддержкой AM/PM"""
    tz_user = timezone(timedelta(hours=USER_TZ))
    now_user = datetime.now(timezone.utc).astimezone(tz_user)
    
    user_input = user_input.lower().strip()
    target_date = now_user.date()
    
    # 1. Проверяем дни недели
    for day_name, day_num in DAYS_OF_WEEK.items():
        if day_name in user_input:
            current_day_num = now_user.weekday()
            days_ahead = day_num - current_day_num
            if days_ahead <= 0:  
                days_ahead += 7  
            target_date = now_user.date() + timedelta(days=days_ahead)
            break
            
    # 2. Проверяем относительные слова (RU / EN / UZ)
    if any(w in user_input for w in ["послезавтра", "day after tomorrow", "inindaga"]):
        target_date = now_user.date() + timedelta(days=2)
    elif any(w in user_input for w in ["завтра", "tomorrow", "ertaga"]):
        target_date = now_user.date() + timedelta(days=1)
    elif any(w in user_input for w in ["сегодня", "today", "bugun"]):
        target_date = now_user.date()

    # 3. Конкретная дата DD.MM или DD.MM.YYYY
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', user_input)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3)) if date_match.group(3) else now_user.year
        try:
            target_date = datetime(year, month, day).date()
        except ValueError:
            pass

    # 4. Ищем время (поддерживает ЧЧ:ММ, ЧЧ:ММ:СС, а также "в 12 pm", "at 9 am", "soat 15")
    # Проверка на 12-часовой формат (AM/PM)
    ampm_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', user_input)
    
    if ampm_match:
        hours = int(ampm_match.group(1))
        minutes = int(ampm_match.group(2)) if ampm_match.group(2) else 0
        seconds = 0
        period = ampm_match.group(3)
        
        if period == "pm" and hours < 12:
            hours += 12
        elif period == "am" and hours == 12:
            hours = 0
    else:
        # Стандартный поиск ЧЧ:ММ(:СС) или просто "12:00"
        time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', user_input)
        if not time_match:
            # Попытка найти просто число "в 12", "at 5", "soat 6"
            simple_hour_match = re.search(r'(?:в|at|soat)\s*(\d{1,2})', user_input)
            if simple_hour_match:
                hours = int(simple_hour_match.group(1))
                minutes = 0
                seconds = 0
            else:
                return None
        else:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3)) if time_match.group(3) else 0
    
    try:
        result_datetime = datetime.combine(target_date, datetime.min.time()).replace(
            hour=hours, minute=minutes, second=seconds, microsecond=0
        )
    except ValueError:
        return None
    
    # Если время в сутках уже прошло — переносим на завтра (кроме точного дня недели)
    if result_datetime.timestamp() <= now_user.timestamp(): 
        if not any(day in user_input for day in DAYS_OF_WEEK):
            result_datetime += timedelta(days=1)
            
    return result_datetime

# --- ХЕНДЛЕРЫ БОТА ---

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await state.set_state(ReminderState.waiting_for_lang)
    await message.answer("🌐 Выберите язык / Choose language / Tilni tanlang:", reply_markup=lang_keyboard)

@dp.message(ReminderState.waiting_for_lang, F.text.in_({"🇷🇺 Русский", "🇺🇸 English", "🇺🇿 O'zbekcha"}))
async def set_language(message: Message, state: FSMContext):
    lang_map = {"🇷🇺 Русский": "ru", "🇺🇸 English": "en", "🇺🇿 O'zbekcha": "uz"}
    lang = lang_map[message.text]
    await state.update_data(lang=lang)
    
    await message.answer(MESSAGES[lang]["start"], parse_mode="HTML", reply_markup=get_main_keyboard(lang))
    await state.set_state(None) # Выходим из стейта, бот готов к работе

@dp.message(Command("help"))
async def help_command(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru") # По умолчанию русский, если язык не выбран
    await message.answer(MESSAGES[lang]["help"], parse_mode="HTML", reply_markup=get_main_keyboard(lang))

@dp.message(F.text.in_({"📋 Мои напоминания", "📋 My reminders", "📋 Mening eslatmalarim"}))
async def my_reminders(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    reminders = get_reminders(message.from_user.id)
    if not reminders:
        await message.answer(MESSAGES[lang]["no_reminders"])
        return

    text = MESSAGES[lang]["your_reminders"]
    for reminder_text, reminder_time in reminders:
        text += f"🕒 {reminder_time}\n📝 {reminder_text}\n\n"
    await message.answer(text)

@dp.message(F.text.in_({"➕ Создать напоминание", "➕ Create a reminder", "➕ Eslatma yaratish"}))
async def create_reminder(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.set_state(ReminderState.waiting_for_text)
    await message.answer(MESSAGES[lang]["ask_text"])

@dp.message(ReminderState.waiting_for_text)
async def get_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.update_data(text=message.text.strip())
    await state.set_state(ReminderState.waiting_for_when)
    await message.answer(MESSAGES[lang]["ask_when"])

@dp.message(ReminderState.waiting_for_when)
async def save_reminder(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    user_input = message.text.strip()
    reminder_datetime = parse_custom_datetime(user_input)
    
    if not reminder_datetime:
        await message.answer(MESSAGES[lang]["parse_error"])
        return

    remind_time_str = reminder_datetime.strftime("%Y-%m-%d %H:%M:%S")
    await state.update_data(remind_time=remind_time_str)
    await state.set_state(ReminderState.waiting_for_repeat)

    repeat_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MESSAGES[lang]["btn_once"])], [KeyboardButton(text=MESSAGES[lang]["btn_daily"])]],
        resize_keyboard=True
    )
    await message.answer(MESSAGES[lang]["ask_repeat"], reply_markup=repeat_keyboard)

@dp.message(F.text.in_({"🗑 Удалить напоминание", "🗑 Delete a reminder", "🗑 Eslatmanі o'chirish"}))
async def delete_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    reminders = get_reminders(message.from_user.id)
    if not reminders:
        await message.answer(MESSAGES[lang]["no_reminders"])
        return

    text = MESSAGES[lang]["choose_delete"]
    for i, (reminder_text, reminder_time) in enumerate(reminders, start=1):
        text += f"{i}. 🕒 {reminder_time}\n   📝 {reminder_text}\n\n"

    await state.update_data(reminders=reminders)
    await state.set_state(ReminderState.waiting_for_delete)
    await message.answer(text)

@dp.message(ReminderState.waiting_for_delete)
async def process_delete(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    reminders = data.get("reminders", [])

    if not message.text.isdigit():
        await message.answer(MESSAGES[lang]["nan_error"])
        return

    index = int(message.text) - 1
    if index < 0 or index >= len(reminders):
        await message.answer(MESSAGES[lang]["index_error"])
        return

    reminder_text, reminder_time = reminders[index]
    delete_reminder(message.from_user.id, reminder_text, reminder_time)

    await message.answer(MESSAGES[lang]["deleted"], reply_markup=get_main_keyboard(lang))
    # Важно: Сохраняем язык пользователя при сбросе стейта!
    await state.set_data({"lang": lang})
    await state.set_state(None)

@dp.message(ReminderState.waiting_for_repeat)
async def process_repeat_choice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    
    if message.text not in [MESSAGES[lang]["btn_once"], MESSAGES[lang]["btn_daily"]]:
        return # Игнорируем левый ввод

    text = user_data.get("text")
    remind_time_str = user_data.get("remind_time")
    
    is_daily = 1 if message.text == MESSAGES[lang]["btn_daily"] else 0
    add_reminder(message.from_user.id, text, remind_time_str, is_daily) 

    tz_user = timezone(timedelta(hours=USER_TZ))
    reminder_datetime = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz_user)
    
    now_utc = datetime.now(timezone.utc)
    seconds_to_wait = (reminder_datetime - now_utc).total_seconds()

    asyncio.create_task(
        send_reminder_by_delay(message.chat.id, message.from_user.id, text, remind_time_str, seconds_to_wait, is_daily, lang)
    )

    await message.answer(
        MESSAGES[lang]["created"].format(text=text, time=remind_time_str, repeat=message.text),
        reply_markup=get_main_keyboard(lang)
    )
    await state.set_data({"lang": lang})
    await state.set_state(None)

async def send_reminder_by_delay(chat_id, user_id, text, remind_time_str, seconds, is_daily=0, lang="ru"):
    try:
        if seconds > 0:
            await asyncio.sleep(seconds)

        await bot.send_message(chat_id, MESSAGES[lang]["notify"].format(text=text), parse_mode="HTML")

        if is_daily:
            old_date = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M:%S")
            new_date = old_date + timedelta(days=1)
            new_time_str = new_date.strftime("%Y-%m-%d %H:%M:%S")

            update_reminder_time(user_id, text, remind_time_str, new_time_str)

            asyncio.create_task(
                send_reminder_by_delay(chat_id, user_id, text, new_time_str, 86400, is_daily=1, lang=lang)
            )
        else:
            delete_reminder(user_id, text, remind_time_str)

    except Exception as e:
        print(f"Ошибка в таске отправки: {e}")

async def load_reminders():
    try:
        reminders = get_all_reminders()
        now_utc = datetime.now(timezone.utc)
        tz_user = timezone(timedelta(hours=USER_TZ))
        
        for reminder in reminders:
            if len(reminder) == 4:
                user_id, text, remind_time_str, is_daily = reminder
            else:
                user_id, text, remind_time_str = reminder
                is_daily = 0
                
            try:
                rem_dt = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz_user)
                seconds = (rem_dt - now_utc).total_seconds()
                # Передаем язык по умолчанию "ru", так как при перезагрузке сервера мы не знаем язык юзера из оперативки FSM
                asyncio.create_task(
                    send_reminder_by_delay(user_id, user_id, text, remind_time_str, max(0, seconds), is_daily, lang="ru")
                )
            except ValueError:
                print(f"Ошибка формата даты в БД: {remind_time_str}")
    except Exception as e:
        print(f"Ошибка загрузки из БД: {e}")

async def main():
    print(f"Бот запущен! Время сервера UTC: {datetime.now(timezone.utc)}")
    await load_reminders()
    await dp.start_polling(bot)

# --- АДМИН ПАНЕЛЬ (НЕ ТРОГАЛИ) ---
@dp.message(F.text == "/users")
async def users_list(message: Message):
    if message.from_user.id != ADMIN_ID: return
    users = get_all_users()
    if not users:
        await message.answer("Пользователей нет.")
        return
    text = "👥 Пользователи:\n\n"
    for user_id, username, first_name, joined_at in users:
        username_text = f"@{username}" if username else "нет username"
        text += f"👤 {first_name}\n🆔 {user_id}\n📛 {username_text}\n📅 {joined_at}\n\n"
    await message.answer(text)

@dp.message(F.text == "/all_reminders")
async def all_reminders(message: Message):
    if message.from_user.id != ADMIN_ID: return
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
        text += f"🕒 {reminder_time}\n📝 {reminder_text}\n\n"

    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks: await message.answer(chunk)
    else:
        await message.answer(text)

if __name__ == "__main__":
    asyncio.run(main())