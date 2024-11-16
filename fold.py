from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

async def func(query):
    # Здесь выполняется анализ или другая логика.
    print(f"Выполняется анализ для: {query}")

async def monitor_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if message_text.startswith("/coomer "):
        query = message_text[len("/coomer "):].strip()
        if query:
            chat_id = update.message.chat_id
            await context.bot.send_message(chat_id=chat_id, text=f"Начат анализ {query}")
            await func(query)
        else:
            await update.message.reply_text("Пожалуйста, укажите запрос после команды /coomer.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен. Используйте /coomer <запрос> для анализа.")

def main():
    # Укажите ваш токен Telegram Bot API
    TOKEN = "ВАШ_ТОКЕН"
    
    # Создаем объект приложения
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Регистрируем обработчик сообщений с командой /coomer
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/coomer '), monitor_chat))

    # Запускаем бота
    print("Бот запущен. Нажмите Ctrl+C для завершения.")
    app.run_polling()

if __name__ == "__main__":
    main()
