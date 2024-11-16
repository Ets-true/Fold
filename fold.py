from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import psutil
import time
import random
import concurrent.futures
from queue import Queue
from telegram import Bot
from yolov5 import YOLOv5
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
import queue
import pathlib
import os
import threading


def log_to_telegram(message):
    bot_token = '6810766307:AAGtQBxU156nBr3f6CEA6l8N6S8KPO4sW80'
    chat_id = '-4236684694'
    bot = Bot(token=bot_token)
    try:
        bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Failed to send log to Telegram: {e}")

def send_telegram_photo(img_path, caption, max_retries=5, delay_between_retries=5):
    print('START SENDING')
    bot_token = '6810766307:AAGtQBxU156nBr3f6CEA6l8N6S8KPO4sW80'
    chat_id = '-4236684694'
    bot = Bot(token=bot_token)
  
    for attempt in range(max_retries):
        try:
            with open(img_path, 'rb') as photo:
                bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
            print('END SENDING')
            return True  # Если отправка успешна, выходим из функции
        except Exception as e:
            print(f"Попытка {attempt + 1} не удалась. Ошибка: {e}")
            if attempt < max_retries - 1:
                print(f"Повторная попытка через {delay_between_retries} секунд...")
                time.sleep(delay_between_retries)  # Ожидание перед повтором
            else:
                print('TG NOT SENDED после нескольких попыток')
                return False



# Создание директории для временных файлов, если она не существует
if not os.path.exists('temp_files'):
    os.makedirs('temp_files')

# Создание файла already.txt, если он не существует
if not os.path.exists('already.txt'):
    with open('already.txt', 'w', encoding='utf-8') as file:
        file.write('')

# Инициализация модели YOLO
model = YOLOv5('best3.pt')


base_url = 'https://coomer.su/'
class_names = ['coconut bra', 'flower lei', 'flower-band', 'flower-bra', 'flower-head', 'hula skirt', 'shell-bra']

total_elements = 0
processed_elements = 0
model_lock = threading.Lock()


def safe_request(url, headers=None, max_retries=5):
    """Отправляет запрос с экспоненциальной задержкой в случае ошибки 429."""
    retry_delay = 1
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, timeout=40)
        if response.status_code == 429:
            time.sleep(retry_delay)
            retry_delay *= 2
        else:
            return response
    return None

# Функция отправки логов в Telegram

def detect_objects(image_url, item, post_url):
    print(image_url)
    try:
        response = safe_request(image_url)
        if response and response.status_code == 200:
            with Image.open(BytesIO(response.content)).convert("RGB") as image:
                 # Изменение размера изображения пропорционально
                if image.size[1] > 800:
                    target_height = 800
                    height_percent = (target_height / float(image.size[1]))
                    target_width = int((float(image.size[0]) * float(height_percent)))
                    image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

                frame_rgb = np.array(image)
                # frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
                with model_lock:  # Использование блокировки при доступе к модели
                    results = model.predict(frame_rgb)



                for *box, conf, cls in results.xyxy[0]:
                    if conf > 0.74:
                        results.render()
                        img_path = f"temp_files/temp_result_{item['id']}.jpg"
                        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)

                        # frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
                        cv2.imwrite(img_path, frame_rgb)
                        class_name = class_names[int(cls)]
                        result_text = (
                            f"User: {item['user']}\n"
                            f"Title: {item['title']}\n"
                            f"Img: {image_url}\n"
                            f"Post: {post_url}\n"
                            f"{class_name} - {conf:.5f}"
                        )
                        send_telegram_photo(img_path, result_text)
                        return True
    except requests.RequestException as e:
        print(f"Failed to load image {image_url}: {str(e)}")
    return False

def is_image(url):
    return url.split('.')[-1] in ['jpg', 'png', 'jpeg']

def is_video(url):
    return url.split('.')[-1] in ['mp4', 'm4v']

def extract_media_urls(item):
    media_urls = []
    if 'file' in item and item['file']:
        media_urls.append(f"https://coomer.su/{item['file']['path'].lstrip('/')}")
    if 'attachments' in item and item['attachments']:
        for attachment in item['attachments']:
            media_urls.append(f"https://coomer.su/{attachment['path'].lstrip('/')}")
    return media_urls

def not_check_already(target_line):
    with open('already.txt', 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() == target_line.strip():
                return False
    return True

def not_minus_words(title):
    title_lower = title.lower()
    minus_words = ["juicy", "@sweetcheeksjuliefree"]
    for word in minus_words:
        if word.lower() in title_lower:
            return False
    return True

def print_progress():
    if total_elements > 0:
        progress = (processed_elements / total_elements) * 100
        message = f"Progress: {processed_elements}/{total_elements} ({progress:.2f}%)"
    else:
        message = "No total elements to process."
    print(message)
    log_to_telegram(message)





def detect_in_video(video_url, item, post_url, max_retries=5, time_interval=10, retry_delay=2):
    print(video_url)
    try:
        retries = 0

        while retries < max_retries:
            # Пытаемся загрузить видео по URL
            cap = cv2.VideoCapture(video_url)

            if cap.isOpened():
                print(f"Видео успешно открыто на попытке {retries + 1}")
                break
            else:
                print(f"Не удалось открыть видео на попытке {retries + 1}. Попробую снова через {retry_delay} секунд.")
                retries += 1
                time.sleep(retry_delay)

        if retries == max_retries:
            print(f"Не удалось открыть видео: {video_url} после {max_retries} попыток.")
            return False

        # Получаем FPS (кадры в секунду) и общее количество кадров
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            print(f"Не удалось получить FPS для видео: {video_url}")
            return False

        # Рассчитываем интервал между кадрами в зависимости от времени (в секундах)
        frame_interval = int(fps * time_interval)  # Количество кадров для интервала времени (например, 10 секунд)
        print(f"FPS: {fps}, обрабатывается каждый {frame_interval}-й кадр (примерно каждые {time_interval} секунд)")

        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Видео окончено или не удалось считать кадр")
                break

            # Обрабатываем кадр, если его номер соответствует интервалу
            if frame_count % frame_interval == 0:
                print(f"Обрабатывается кадр: {frame_count}")
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                with model_lock:  # Использование блокировки при доступе к модели
                    results = model.predict(frame_rgb)

                for *box, conf, cls in results.xyxy[0]:
                    class_name = class_names[int(cls)]
                    if class_name == 'hula skirt' and conf > 0.74:
                        results.render()
                        print(f"Найден элемент: {class_name} - {conf}")

                        # Конвертация обратно в BGR для сохранения
                        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                        img_path = f"temp_files/temp_result_{item['id']}_frame_{frame_count}.jpg"
                        cv2.imwrite(img_path, frame_bgr)

                        # Отправка результата
                        result_text = (
                            f"User: {item['user']}\n"
                            f"Title: {item['title']}\n"
                            f"Img: {video_url}\n"
                            f"Post: {post_url}\n"
                            f"{class_name} - {conf:.5f}"
                        )
                        send_telegram_photo(img_path, result_text)
                        cap.release()
                        return True

            frame_count += 1

        cap.release()
        print("Обработка видео завершена")

    except Exception as e:
        print(f"Ошибка при обработке видео: {str(e)}")

    return False


def process_item(item, base_url, thread):
    print(psutil.virtual_memory().percent)
    while psutil.virtual_memory().percent > 70:
        print("Высокая загрузка памяти. Ожидание...")
        time.sleep(10)
    post_url = f"{base_url}{item['service']}/user/{item['user']}/post/{item['id']}"
    if not_check_already(post_url) and not_minus_words(item['title']):

        media_urls = extract_media_urls(item)

        for index, media_url in enumerate(media_urls):
            if index > 5:
                break
            if (is_image(media_url) and detect_objects(media_url, item, post_url)):
                break
            # elif (is_video(media_url) and detect_in_video(media_url, item, post_url)):
            #     break
        with open('already.txt', 'a', encoding='utf-8') as file:
          file.write(f"{post_url}\n")

    global processed_elements
    processed_elements += 1
    print_progress()


def collect_posts(api_url, query):
    task_queue = Queue()
    step = 50

    for q in query:
      offset = 0

      while True:
          request_url = f'{api_url}?q={q}&o={offset}'
          print(request_url)
          response = requests.get(request_url)
          if response.status_code != 200:
              print(f"Failed to fetch data at offset {offset}: {response.status_code}")
              break

          data = response.json()
          if not data:
              break
          # data = [{'id': '187065312', 'user': 'aalannajade', 'service': 'onlyfans', 'title': 'We went to a luau last night 😁😈🌺', 'substring': 'We went to a luau last night 😁😈🌺', 'published': '2021-08-21T20:16:48', 'file': {'name': '75bc39c7-b3cc-437a-a586-6f7c04419b55.m4v', 'path': '/4b/84/4b84bebf60dca5d82ce04c4a05c34d51a7e4df5aa9c1b32a94d0dfa859ac1a3e.m4v'}, 'attachments': []}]

          for item in data:
              task_queue.put(item)
              global total_elements
              total_elements += 1
          offset += step

    print(f"Total posts collected: {task_queue.qsize()}")
    return task_queue

def worker(task_queue):
    while not task_queue.empty():
        try:
            item = task_queue.get_nowait()
            process_item(item, base_url, thread=concurrent.futures.thread.ThreadPoolExecutor()._threads)
            task_queue.task_done()
        except Exception as e:
            print(f"Error in worker: {e} with {item['img_url']}")
            task_queue.task_done()

async def start_processing(api_url, query, threads=16):
    task_queue = collect_posts(api_url, query)
    if task_queue.empty():
        print("No posts to process.")
        return

    print(f"Collected {task_queue.qsize()} posts for processing.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(worker, task_queue) for _ in range(threads)]
        task_queue.join()  # Ожидание завершения всех задач
        concurrent.futures.wait(futures)
    print("Processing complete.")

api_url = "https://coomer.su/api/v1/posts"


async def monitor_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if message_text.startswith("/coomer "):
        query = message_text[len("/coomer "):].strip()
        if query:
            chat_id = update.message.chat_id
            await context.bot.send_message(chat_id=chat_id, text=f"Начат анализ {query}")
            await start_processing(api_url, [query], threads=1)
            await context.bot.send_message(chat_id=chat_id, text="Анализ завершен.")
        else:
            await update.message.reply_text("Пожалуйста, укажите запрос после команды /coomer.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен. Используйте /coomer <запрос> для анализа.")



def main():
    # Укажите ваш токен Telegram Bot API
    
    TOKEN = "6810766307:AAGtQBxU156nBr3f6CEA6l8N6S8KPO4sW80"
    
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
