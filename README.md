# Telegram Reminder Bot

A Telegram bot for creating one-time and daily reminders, built with Python and Aiogram 3.

## Features

- Create one-time reminders
- Create daily reminders
- View all personal reminders
- Delete reminders
- Admin commands for user management
- SQLite database for data storage
- Secure token management using `.env`

## Tech Stack

- Python 3
- Aiogram 3
- SQLite
- Git & GitHub

## Installation

Clone the repository:

```bash
git clone https://github.com/Abdulloh-01/telegram-reminder-bot.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
```

Run the bot:

```bash
python m.py
```

## Project Structure

```text
.
├── m.py          # Main bot logic
├── db.py         # Database functions
├── .env          # Environment variables (not uploaded to GitHub)
├── .gitignore    # Ignored files
└── notes.db      # SQLite database
```

## Author

Abdulloh Aliev