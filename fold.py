from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

def func(query):
    # Здесь выполняется анализ или другая логика.
    print(f"Выполняется анализ для: {query}")

def monitor_chat(update: Update, context: CallbackContext):
    message_text = update.message.text
    if message_text.startswith("/coomer "):
        query = message_text[len("/coomer "):].strip()
        if query:
            chat_id = update.message.chat_id
            context.bot.send_message(chat_id=chat_id, text=f"Начат анализ {query}")
            func(query)
        else:
            update.message.reply_text("Пожалуйста, укажите запрос после команды /coomer.")

def main():
    # Укажите ваш токен Telegram Bot API
    TOKEN = "6810766307:AAGtQBxU156nBr3f6CEA6l8N6S8KPO4sW80"
    
    # Создаем объект Updater и передаем ему токен вашего бота
    updater = Updater(TOKEN)

    # Получаем диспетчер для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрируем обработчик для всех сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, monitor_chat))

    # Запускаем бота
    updater.start_polling()
    print("Бот запущен. Нажмите Ctrl+C для завершения.")
    updater.idle()

if __name__ == "__main__":
    main()