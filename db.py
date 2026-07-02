import sqlite3
from datetime import datetime

db = sqlite3.connect("notes.db")
cursor = db.cursor()


# Таблица напоминаний
# Таблица напоминаний
cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    remind_time TEXT,
    is_daily INTEGER DEFAULT 0
)
""")


# Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    joined_at TEXT
)
""")

db.commit()



# ======================
# Напоминания
# ======================

def add_reminder(user_id, text, remind_time, is_daily=0):
    cursor.execute(
        """
        INSERT INTO reminders (user_id, text, remind_time, is_daily)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, text, remind_time, is_daily)
    )

    db.commit()


def get_reminders(user_id):
    cursor.execute(
        """
        SELECT text, remind_time
        FROM reminders
        WHERE user_id = ?
        """,
        (user_id,)
    )

    return cursor.fetchall()


def delete_reminder(user_id, text, remind_time):
    cursor.execute(
        """
        DELETE FROM reminders
        WHERE user_id = ? AND text = ? AND remind_time = ?
        """,
        (user_id, text, remind_time)
    )

    db.commit()


def get_all_reminders():
    cursor.execute("""
        SELECT user_id, text, remind_time, is_daily
        FROM reminders
    """)

    return cursor.fetchall()

# ======================
# Пользователи
# ======================

def add_user(user_id, username, first_name):
    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        username,
        first_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    db.commit()


def get_all_users():
    cursor.execute("""
        SELECT user_id, username, first_name, joined_at
        FROM users
        ORDER BY joined_at DESC
    """)

    return cursor.fetchall()


def update_reminder_time(user_id, text, old_time, new_time):
    cursor.execute("""
        UPDATE reminders
        SET remind_time = ?
        WHERE user_id = ? AND text = ? AND remind_time = ?
    """, (new_time, user_id, text, old_time))

    db.commit()

# def delete_reminder(user_id, text, reminder_time):
#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()

#     cursor.execute("""
#         DELETE FROM reminders
#         WHERE user_id = ? AND text = ? AND remind_time = ?
#     """, (user_id, text, reminder_time))

#     conn.commit()
#     conn.close()