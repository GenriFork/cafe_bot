import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from datetime import datetime, timedelta
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import json
import os
import csv
from io import StringIO


# 📎 Кнопка
markup = ReplyKeyboardMarkup([
    ["📄 Моя информация"],["📆 Список на сегодня", "📆 Список на завтра"], ["📅 Выбрать дату"], ["🔍 ВГ-5 / ВГ-6", "🔜 ВГ-5 / ВГ-6 на завтра"]
], resize_keyboard=True)

# 🔐 Подключение к Google Таблице
def get_raw_row_by_user_id(user_id, sheet_name="TelegramSubscribers"):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    json_creds_str = os.environ.get("GOOGLE_CREDS")
    json_creds_dict = json.loads(json_creds_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds_dict, scope)

    client = gspread.authorize(creds)

    sheet = client.open(sheet_name).sheet1
    all_rows = sheet.get_all_values()  # получаем всё "как есть"

    # Пропускаем первые 3 строки
    for row in all_rows[3:]:
        if not row:
            continue

        if len(row) < 1:
            continue

        user_id_in_sheet = row[1]  # предполагаем, что user_id — в первом столбце
        if str(user_id_in_sheet).strip() == str(user_id).strip():
            return row

    return None


# 📩 Команда /start
def get_shift_column_index(target_date: datetime, base_date: datetime) -> int:
    day_diff = (target_date - base_date).days
    return 4 + (day_diff * 2)  # каждая дата — 2 колонки, старт с ячейки 5 (индекс 4)

def clean_field(value):
    value = value.strip()
    if value.isdigit() and len(value) > 6:
        return ""
    return value

def get_all_user_shifts_for_date(target_date: datetime, sheet_name="TelegramSubscribers"):
    # Подключение к Google Таблице
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    json_creds_str = os.environ.get("GOOGLE_CREDS")
    json_creds_dict = json.loads(json_creds_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    all_rows = sheet.get_all_values()

    # Дата начала (07.04.2025) — от неё считаем смещение
    base_date = datetime.strptime("07.04.2025", "%d.%m.%Y")
    col_index = get_shift_column_index(target_date, base_date)

    # Преобразуем ФИО в формат: "Фамилия І.О."
    def format_name(full_name):
        parts = full_name.strip().split()
        if len(parts) == 0:
            return ""
        last_name = parts[0]
        initials = ""
        if len(parts) > 1:
            initials += parts[1][0] + "."
        if len(parts) > 2:
            initials += parts[2][0] + "."
        return f"{last_name} {initials}"

    results = []
    not_assigned = []  # незадействованные

    for row in all_rows[3:]:
        if len(row) > col_index:
            rank = row[2].strip() if len(row) > 2 else ""
            name = format_name(row[3]) if len(row) > 3 else ""
            val1 = row[col_index].strip()
            val2 = row[col_index + 1].strip() if len(row) > col_index + 1 else ""

            if val1 or val2:
                values = " / ".join([add_emoji(v) for v in [val1, val2] if v])
                results.append((rank, name, values))
            else:
                not_assigned.append((rank, name))

    return results, not_assigned


CSV_FILE = "users.csv"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"[LOG] Новый пользователь: {user_id} — {first_name} ({username})")

    save_user_to_csv(user_id, username, first_name, timestamp)

    await update.message.reply_text(
        "👋 Привет! Нажми кнопку ниже, чтобы получить свою информацию.",
        reply_markup=markup
    )
def save_user_to_csv(user_id, username, first_name, timestamp):
    file_exists = os.path.exists(CSV_FILE)

    # Проверка: если user_id уже есть — не дублировать
    existing_ids = set()
    if file_exists:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # пропускаем заголовок
            for row in reader:
                if len(row) > 0:
                    existing_ids.add(row[0])

    if str(user_id) in existing_ids:
        print(f"[INFO] ID {user_id} уже записан.")
        return

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["user_id", "username", "first_name", "date"])
        writer.writerow([user_id, username, first_name, timestamp])
        print(f"[✔] Добавлен: {user_id} — {first_name}")


# 🧾 Обработка кнопки "📄 Моя информация"
def add_emoji(value):
    original_value = value
    value = value.strip().lower()

    emoji_map = {
        "кпп": "🚪 КПП",
        "чвн": "👨‍✈️ ЧВН",
        "водій": "🚗 Водій",
        "пнвн": "🧑‍✈️ ПНВН",
        "вп": "🌊 ВП",
        "вд": "🪣 ВД"
    }

    mapped = emoji_map.get(value, original_value)

    print(f"[LOG] Сырые данные: '{original_value}' → Обработано: '{value}' → Результат: '{mapped}'")

    return mapped



async def show_my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = get_raw_row_by_user_id(user.id)

    if not row or len(row) < 6:
        await update.message.reply_text("😕 Інформацію по вашому ID не знайдено або вона неповна.")
        return

    rank = row[1]
    name = row[2]

    start_date = datetime.strptime("07.04", "%d.%m")
    msg = f"👤 <b>{rank}</b> — <b>{name}</b>\n\n📄 <b>Твій графік присутності:</b>\n\n"

    data_cells = row[4:]

    for i in range(0, len(data_cells), 2):
        date = (start_date + timedelta(days=i // 2)).strftime("%d.%m.%Y")

        val1 = data_cells[i].strip() if i < len(data_cells) else ""
        val2 = data_cells[i+1].strip() if i+1 < len(data_cells) else ""

        if val1 or val2:
            formatted_vals = " / ".join([add_emoji(v) for v in [val1, val2] if v])
            msg += f"<b>{date}</b>: {formatted_vals}\n"

    await update.message.reply_html(msg)

async def send_vg_filtered_list(update: Update, target_date: datetime, shift_data):
    results, _ = shift_data
    date_str = target_date.strftime("%d.%m.%Y")

    vg5 = [(r, n) for r, n, s in results if "вг-5" in s.lower()]
    vg6 = [(r, n) for r, n, s in results if "вг-6" in s.lower() and (r, n) not in vg5]

    if not vg5 and not vg6:
        await update.message.reply_text(f"📆 На {date_str} немає ВГ-5 / ВГ-6.")
        return

    max_rank = max((len(r) for r, _ in vg5 + vg6), default=6)
    max_name = max((len(n) for _, n in vg5 + vg6), default=6)

    header = f"<pre>📆 ВГ-5 / ВГ-6 на {date_str}:\n\n"

    lines = []

    if vg5:
        lines.append("🔸 ВГ-5:")
        lines.extend([f"👤 {r:<{max_rank}} — {n:<{max_name}}" for r, n in vg5])
        lines.append("")

    if vg6:
        lines.append("🔸 ВГ-6:")
        lines.extend([f"👤 {r:<{max_rank}} — {n:<{max_name}}" for r, n in vg6])

    footer = f"\n\n🔢 ВГ-5: {len(vg5)}     ВГ-6: {len(vg6)}     Всього: {len(vg5) + len(vg6)}"

    message = header + "\n".join(lines) + footer + "</pre>"

    await update.message.reply_html(message)


# 📥 Обработка текстов
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text


    if text == "📄 Моя информация":
        await show_my_info(update, context)

    elif text == "📆 Список на сегодня":
        target_date = datetime.today()
        shifts = get_all_user_shifts_for_date(target_date)
        await send_shift_list(update, target_date, shifts)

    elif text == "📆 Список на завтра":
        target_date = datetime.today() + timedelta(days=1)
        shifts = get_all_user_shifts_for_date(target_date)
        await send_shift_list(update, target_date, shifts)

    elif text == "🔍 ВГ-5 / ВГ-6":
        target_date = datetime.today()
        shifts = get_all_user_shifts_for_date(target_date)
        await send_vg_filtered_list(update, target_date, shifts)

    elif text == "🔜 ВГ-5 / ВГ-6 на завтра":
        target_date = datetime.today() + timedelta(days=1)
        shifts = get_all_user_shifts_for_date(target_date)
        await send_vg_filtered_list(update, target_date, shifts)


    elif text == "📅 Выбрать дату":

        await update.message.reply_text("📅 Введи дату в формате ДД.ММ (например: 12.04)")


    elif re.match(r"\d{2}\.\d{2}", text):

        try:

            day, month = map(int, text.split("."))

            year = datetime.today().year  # можно заменить на фиксированный: 2025

            target_date = datetime(year=year, month=month, day=day)

            shifts = get_all_user_shifts_for_date(target_date)

            await send_shift_list(update, target_date, shifts)

        except ValueError:

            await update.message.reply_text("❌ Невірна дата. Приклад правильного формату: 12.04")


    else:
        await update.message.reply_text("Выбери действие с клавиатуры 👇", reply_markup=markup)

async def send_shift_list(update: Update, target_date: datetime, shift_data):
    results, not_assigned = shift_data
    date_str = target_date.strftime("%d.%m.%Y")

    if not results and not not_assigned:
        await update.message.reply_text(f"📆 На {date_str} даних не знайдено.")
        return

    max_rank = max((len(r) for r, _, _ in results), default=6)
    max_name = max((len(n) for _, n, _ in results), default=6)

    header = f"<pre>📆 Список на {date_str}:\n\n"
    header += f"{'Ранг':<{max_rank}} | {'ПІБ':<{max_name}} | Зміна\n"
    header += f"{'-'*max_rank}-+-{'-'*max_name}-+-{'-'*15}\n"

    lines = [f"{r:<{max_rank}} | {n:<{max_name}} | {s}" for r, n, s in results]

    # Счётчики
    vg5_count = sum(1 for _, _, s in results if "вг-5" in s.lower())
    vg6_count = sum(1 for _, _, s in results if "вг-6" in s.lower())
    total = len(results)

    footer = f"\n\n🔢 ВГ-5: {vg5_count}     ВГ-6: {vg6_count}     Всього: {total}"

    # 🧍 Добавляем незадіяних
    if not_assigned:
        footer += "\n\n🙋 Не задіяні:\n"
        for r, n in not_assigned:
            footer += f"👤 {r} — {n}\n"

    message = header + "\n".join(lines) + footer + "</pre>"

    await update.message.reply_html(message)




# ▶️ Запуск бота
if __name__ == "__main__":
    BOT_TOKEN = "8033606007:AAHBLngkWy8UjcU5stSRE-anti9Sf2gad3A"

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен. Готов отвечать!")
    app.run_polling()
