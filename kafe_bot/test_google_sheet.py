import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import json

# 📎 Кнопка
markup = ReplyKeyboardMarkup([
    ["📄 Моя информация"]
], resize_keyboard=True)

# 🔐 Подключение к Google Таблице
def get_user_info_by_id(user_id, sheet_name="TelegramSubscribers"):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open(sheet_name).sheet1
    data = sheet.get_all_records()

    for row in data:
        if str(row.get("user_id")) == str(user_id):
            return row  # возвращаем всю строку

    return None

# 📩 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Нажми кнопку ниже, чтобы получить свою информацию:",
        reply_markup=markup
    )

# 🧾 Обработка кнопки "📄 Моя информация"
async def show_my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = get_user_info_by_id(user.id)

    if not row:
        await update.message.reply_text("😕 Тебя пока нет в таблице.")
        return

    msg = "📄 <b>Твоя информация:</b>\n\n"
    for key, value in row.items():
        msg += f"<b>{key}</b>: {value}\n"

    await update.message.reply_html(msg)

# 📥 Обработка текстов
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📄 Моя информация":
        await show_my_info(update, context)
    else:
        await update.message.reply_text("Выбери действие с клавиатуры 👇", reply_markup=markup)

# ▶️ Запуск бота
if __name__ == "__main__":
    BOT_TOKEN = "8033606007:AAHBLngkWy8UjcU5stSRE-anti9Sf2gad3A"

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен. Готов отвечать!")
    app.run_polling()
