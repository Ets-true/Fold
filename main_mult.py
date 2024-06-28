# !pip install requests torch torchvision pillow yolov5
# !pip install python-telegram-bot==13.7

import requests
from PIL import Image
from io import BytesIO
from telegram import Bot
import concurrent.futures
from yolov5 import YOLOv5  # Убедитесь, что у вас есть доступ к модифицированному YOLOv5
import time
import os
import cv2
import numpy as np
# Инициализация модели YOLO
model = YOLOv5('best2.pt')

base_url = 'https://coomer.su/'
class_names = ['coconut bra', 'hula skirt', 'flower lei', 'flower bra']



def safe_request(url, max_retries=5):
    """ Отправляет запрос с экспоненциальной задержкой в случае ошибки 429. """
    retry_delay = 1  # Начальная задержка в секундах
    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code == 429:  # Слишком много запросов
            # print(f"Request rate limit exceeded, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Увеличиваем задержку вдвое
        else:
            return response
    return None  # Возвращает None, если все попытки неудачны

def not_check_already(target_line):
    """ Проверка, была ли ссылка уже обработана ранее. """
    with open('already3.txt', 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() == target_line.strip():
                return False
    return True

# totalCountUrl = 0


def detect_objects(image_url, item):
    service = item.get("service", "")
    user = item.get("user", "")
    id = item.get("id", "")
    title = item.get("title", "")
    post_url = base_url + f'{service}/' + f'user/{user}/' + f'post/{id}'

    if not_check_already(post_url):
        full_url = image_url.lstrip('/')
        try:
            response = safe_request(full_url)
            if response and response.status_code == 200:
                with Image.open(BytesIO(response.content)).convert("RGB") as image:
                    results = model.predict(image)
                    results.render()  # Рисуем рамки на изображении

                    img_array = np.array(image)  # Преобразуем PIL Image в numpy array
                    img_to_save = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)  # Конвертируем из RGB в BGR для сохранения с OpenCV
                    img_path = f"temp_result_{id}.jpg"  # Путь для сохранения изображения
                    print(img_path)
                    cv2.imwrite(img_path, img_to_save)  # Сохраняем изображение
                    for *box, conf, cls in results.xyxy[0]:
                        if conf > 0.1:
                            with open('simple.txt', 'a') as simple_file:
                                simple_file.write(post_url)
                            class_name = class_names[int(cls)]
                            result_text = (
                                f'User: {user}\n'
                                f'Title: {title}\n'
                                f'Img: {full_url}\n'
                                f'Post: {post_url}\n'
                                f'{class_name} - {conf:.5f}'
                            )
                            send_telegram_photo(img_path, result_text)  # Отправляем изображение и текст в Telegram
                            break

                    with open('already3.txt', 'a') as file:
                        file.write(f'{post_url}\n')

        except requests.RequestException as e:
            print(f"Failed to load image {full_url}: {str(e)}")
        finally:
            if 'response' in locals():
                response.close()

def send_telegram_photo(img_path, caption):
    """ Отправляет фото в Telegram. """
    bot_token = '6810766307:AAE-9MIiuW65ouuzDKpazsWk1VQkWFA4Xxk'
    chat_id = '-4236684694'
    bot = Bot(token=bot_token)
    with open(img_path, 'rb') as photo:
        bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
    os.remove(img_path)  # Удаляем файл после отправки, чтобы освободить место


def isImage(url):
    """ Проверяет, является ли файл по URL изображением. """
    return url.split('.')[-1] in ['jpg', 'png', 'jpeg']

def extract_image_url(item):
    """ Возвращает URL изображения из элемента данных, если оно существует. """
    if 'attachments' in item and item['attachments'] and isImage(item['attachments'][0]['path']):
        return f"https://coomer.su/{item['attachments'][0]['path'].lstrip('/')}"
    elif 'file' in item and item['file'] and isImage(item['file']['path']):
        return f"https://coomer.su/{item['file']['path'].lstrip('/')}"
    return None


def process_page_range(api_url, query, start, end, step=50):
    """ Обрабатывает страницы данных в заданном диапазоне. """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        current_step = start
        while current_step < end:
            request_url = f'{api_url}?q={query}&o={current_step}'
            try:
                response = requests.get(request_url)
                response.raise_for_status()
                data = response.json()
                if not data:
                    break

                futures = []
                for item in data:
                    image_url = extract_image_url(item)
                    if image_url:
                        futures.append(executor.submit(detect_objects, image_url, item))
                concurrent.futures.wait(futures)
                current_step += step
            except requests.RequestException as e:
                print(f"Failed to fetch data at offset {current_step}: {str(e)}")
            finally:
                response.close()


def start_parallel_page_processing(api_url, query, total_pages, threads=8, start_page=0):
    """ Запускает параллельную обработку страниц на множестве потоков. """
    print('started')
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        step = (total_pages - start_page) // threads
        futures = []
        current_start = start_page * 50


        for i in range(threads):

            end = current_start + step * 50
            futures.append(executor.submit(process_page_range, api_url, query, current_start, end))
            current_start = end

        concurrent.futures.wait(futures)


def get_total_objects(api_url, query):
    step = 50
    offset = 0
    total_objects = 0

    while True:
        request_url = f'{api_url}?q={query}&o={offset}'
        response = requests.get(request_url)
        print(request_url)

        if response.status_code != 200:
            print(f"Failed to fetch data at offset {offset}: {response.status_code}")
            break

        data = response.json()

        if len(data) == 0:
            break

        total_objects += 1
        offset += step

    return total_objects

# Пример вызова
api_url = "https://coomer.su/api/v1/posts"
queries = ["leid", "lei d", "lei'd", "lei"]

# start_parallel_page_processing(api_url, '🥥 + -jfsldfj', 1100, threads=16, start_page=0)


for query in queries:
  total_pages = get_total_objects(api_url, query)  # Общее количество страниц для обработки
  # total_pages = 100
  print(total_pages)
  threads = 1
  if total_pages >= 16:
    threads = 16
  if total_pages < 16 and total_pages >= 8:
    threads = 8
  if total_pages < 8 and total_pages >= 4 :
    threads = 4
  if total_pages < 4 and total_pages >= 2:
    threads = 2
  if total_pages < 2:
    threads = 1
  start_parallel_page_processing(api_url, query, total_pages, threads=threads, start_page=0)
