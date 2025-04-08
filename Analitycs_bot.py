import json
import binance_pumps
import binance_dumps
import binance_announcements
import pump_detector_extended
import dump_detector_final
from tabulate import tabulate
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.ext import CommandHandler
from news_aggregator import get_all_news

# Замените на ваш токен от @BotFather
BOT_TOKEN = "8104073552:AAFuJUUGX7NHOhWC9WDkuwcN8Wkxd9IJjps"

# Кнопки
keyboard = [
    ["📈 Памп-кандидаты", "📉 Дамп-кандидаты", "📢 Анонсы Binance", "📈 Binance пампы", "📉 Binance дампы"]
]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Загрузка данных
def load_data(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def format_table(data, title):
    headers = ["Name", "Symbol", "Price", "24h %", "Volume", "Exchanges"]
    table = []
    for token in data:
        table.append([
            token["name"],
            token["symbol"],
            round(token["price"], 6) if token["price"] else "-",
            round(token["price_change_24h"], 2),
            round(token["volume"], 2),
            token.get("exchanges", "N/A")
        ])
    text = f"🔔 <b>{title}</b>\n\n"
    text += f"<pre>{tabulate(table, headers=headers, tablefmt='grid')}</pre>"
    return text[:4096]  # Telegram ограничение на сообщение

# /start команда
async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("📌 Введите команду в формате:\n/news <токен>\n\nПример: /news pepe")
        return

    token = context.args[0]
    await update.message.reply_text(f"🔎 Ищу новости по токену <b>{token.upper()}</b>...", parse_mode="HTML")

    news = get_all_news(token)
    if not news:
        await update.message.reply_text("😕 Новости не найдены.")
        return

    msg = f"📰 <b>Новости по токену {token.upper()}:</b>\n\n"
    for item in news:
        msg += f"🔸 <b>{item['title']}</b> — <i>{item['source']}</i>\n{item['url']}\n\n"

    await update.message.reply_html(msg[:4090], disable_web_page_preview=True)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выбери, что показать:",
        reply_markup=markup
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📈 Памп-кандидаты":
        data = load_data("pump_candidates.json")
        if not data:
            await update.message.reply_text("Нет данных по памп-кандидатам 😕")
            return

        msg = "📈 <b>Памп-кандидаты (CoinGecko):</b>\n\n"
        for token in data:
            symbol = token.get("symbol", "???").upper()
            price = token.get("price_change_24h", "-")
            volume = token.get("volume_24h", "-")
            exchanges = token.get("exchanges", "N/A")
            msg += f"🔸 <b>{token['symbol'].upper()}</b> — +{round(token['price_change_24h'], 2)}% | Объём: ${int(token['volume_24h']):,}"
            if 'exchanges' in token:
                msg += f" | Биржи: {token['exchanges']}"
            msg += "\n"

        await update.message.reply_html(msg)


    elif text == "📉 Дамп-кандидаты":
        data = load_data("dump_candidates_final.json")
        if not data:
            await update.message.reply_text("Нет данных по дамп-кандидатам 😕")
            return

        msg = "📉 <b>Дамп-кандидаты (CoinGecko):</b>\n\n"
        for token in data:
            symbol = token.get("symbol", "???").upper()
            price = token.get("price_change_24h", "-")
            volume = token.get("volume_24h", "-")
            exchanges = token.get("exchanges", "N/A")

            price_text = f"{round(price, 2)}%" if isinstance(price, (float, int)) else "-"
            volume_text = f"${int(volume):,}" if isinstance(volume, (float, int)) else "-"

            msg += f"🔻 <b>{symbol}</b> — {price_text} | Объём: {volume_text} | Биржи: {exchanges}\n"

        await update.message.reply_html(msg)


    elif text == "📢 Анонсы Binance":
        data = load_data("binance_announcements.json")
        if not data:
            await update.message.reply_text("Нет свежих анонсов с Binance 😕")
            return

        msg = "📢 <b>Последние листинги на Binance:</b>\n\n"
        for item in data:
            msg += f"🔸 <a href='{item['url']}'>{item['title']}</a>\n"

        await update.message.reply_html(msg, disable_web_page_preview=True)

    elif text == "📈 Binance пампы":
        data = load_data("binance_pumps.json")
        if not data:
            await update.message.reply_text("Нет токенов с ростом > 20% за сутки 😕")
            return

        msg = "📈 <b>Памп-кандидаты на Binance (24ч):</b>\n\n"
        for token in data:
            msg += f"🔸 <b>{token['symbol']}</b> — +{token['priceChangePercent']}% | Объём: ${int(token['volume']):,}\n"

        await update.message.reply_html(msg)

    elif text == "📉 Binance дампы":
        data = load_data("binance_dumps.json")
        if not data:
            await update.message.reply_text("Нет токенов с падением > 15% за сутки 😕")
            return

        msg = "📉 <b>Дамп-кандидаты на Binance (24ч):</b>\n\n"
        for token in data:
            msg += f"🔻 <b>{token['symbol']}</b> — {token['priceChangePercent']}% | Объём: ${int(token['volume']):,}\n"

        await update.message.reply_html(msg)


    else:
        await update.message.reply_text("Выбери кнопку на клавиатуре 👇", reply_markup=markup)

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("news", news_handler))

    # 👇 Обновление всех JSON при запуске
    print("🔄 Обновляем данные...")
    pump_detector_extended.update()
    dump_detector_final.update()
    binance_pumps.update()
    binance_dumps.update()
    binance_announcements.update()
    print("✅ Данные обновлены. Запускаем бота...\n")

    app.run_polling()
