# Telegram Reminder Bot

A multilingual Telegram bot for creating one-time and daily reminders, built with Python and Aiogram 3. The bot supports natural language date parsing and is deployed on Railway.

## Features

* Create one-time reminders
* Create daily reminders
* Natural language date parsing

  * Examples:

    * `tomorrow at 10:00`
    * `Friday 18:00`
    * `15.07.2026 15:00`
    * `today at 12 pm`
* Multi-language support

  * 🇷🇺 Russian
  * 🇺🇸 English
  * 🇺🇿 Uzbek
* View all personal reminders
* Delete reminders
* Automatic reminder recovery after server restart
* Admin commands for user management
* SQLite database for data storage
* Secure token management using `.env`
* Cloud deployment with Railway

## Tech Stack

* Python 3
* Aiogram 3
* SQLite
* Python Dotenv
* Railway
* Git & GitHub

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
python main.py
```

## Deployment

The bot is deployed on Railway.

Environment variables are managed securely through the Railway dashboard, which keeps sensitive data such as the bot token out of the source code.

## Project Structure

```text
.
├── main.py          # Main bot logic
├── db.py         # Database functions
├── .env          # Environment variables (not uploaded to GitHub)
├── .gitignore    # Ignored files
└── notes.db      # SQLite database
```

## Future Improvements

* Weekly reminders
* Custom user time zones
* PostgreSQL support
* Web dashboard
* Reminder categories and tags

## Author

Abdulloh Aliev
