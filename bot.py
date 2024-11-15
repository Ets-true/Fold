from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
from PIL import Image, ImageDraw
import io
from yolov5 import YOLOv5


model = YOLOv5('best3.pt')

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь мне фото, и я выполню детекцию объектов с помощью твоей модели.')

async def handle_photo(update: Update, context: CallbackContext) -> None:
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    
    # Открываем изображение
    img = Image.open(io.BytesIO(photo_bytes))
    
    # Прогоняем через модель
    results = model.predict(img)
    
    # Получаем результаты и рисуем их
    draw = ImageDraw.Draw(img)
    for *box, conf, cls in results.xyxy[0]:
        x1, y1, x2, y2 = map(int, box)
        label = f'{results.names[int(cls)]} {conf:.2f}'
        draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
        draw.text((x1, y1), label, fill='red')
    
    # Сохраняем изображение в буфер
    bio = io.BytesIO()
    img.save(bio, format='JPEG')
    bio.seek(0)
    
    # Отправляем обратно пользователю
    await update.message.reply_photo(photo=bio)

def main() -> None:
    # Вставьте свой токен
    TOKEN = '6810766307:AAGtQBxU156nBr3f6CEA6l8N6S8KPO4sW80'
    
    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
