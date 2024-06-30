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

# Инициализация модели YOLO
model = YOLOv5('best2.pt')
base_url = 'https://coomer.su/'
class_names = ['coconut bra', 'hula skirt', 'flower lei', 'flower bra']

total_elements = 0
processed_elements = 0

def safe_request(url, max_retries=5):
    """Отправляет запрос с экспоненциальной задержкой в случае ошибки 429."""
    retry_delay = 1
    for attempt in range(max_retries):
        response = requests.get(url, timeout=40)
        if response.status_code == 429:
            time.sleep(retry_delay)
            retry_delay *= 2
        else:
            return response
    return None

def detect_objects(image_url, item, post_url):
    try:
        response = safe_request(image_url)
        if response and response.status_code == 200:
            with Image.open(BytesIO(response.content)).convert("RGB") as image:
                results = model.predict(image)
                results.render()
                img_array = np.array(image)
                img_to_save = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                img_path = f"temp_files/temp_result_{item['id']}.jpg"
                cv2.imwrite(img_path, img_to_save)

                for *box, conf, cls in results.xyxy[0]:
                    if conf > 0.5:
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
        with open('to_long.txt', 'a', encoding='utf-8') as file:
            file.write(f"{post_url}\n")
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
        print(f"Progress: {processed_elements}/{total_elements} ({progress:.2f}%)")
    else:
        print("No total elements to process.")

def detect_in_video(video_url, item, post_url):
    try:
        response = safe_request(video_url)
        if response and response.status_code == 200:
            video_data = response.content
            video_path = f"temp_files/temp_video_{item['id']}.mp4"
            with open(video_path, 'wb') as video_file:
                video_file.write(video_data)

            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            for i in range(0, frame_count, frame_count // 20):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = model.predict(frame_rgb)
                results.render()

                img_path = f"temp_files/temp_result_{item['id']}_frame_{i}.jpg"
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(img_path, frame_bgr)

                for *box, conf, cls in results.xyxy[0]:
                    if conf > 0.5:
                        class_name = class_names[int(cls)]
                        result_text = (
                            f"User: {item['user']}\n"
                            f"Title: {item['title']}\n"
                            f"Video: {video_url}\n"
                            f"Post: {post_url}\n"
                            f"{class_name} - {conf:.5f}"
                        )
                        send_telegram_photo(img_path, result_text)
                        cap.release()
                        return True
            cap.release()
    except requests.RequestException as e:
        with open('to_long.txt', 'a', encoding='utf-8') as file:
            file.write(f"{post_url}\n")
        print(f"Failed to load video {video_url}: {str(e)}")
    return False

def send_telegram_photo(img_path, caption):
    bot_token = '6810766307:AAE-9MIiuW65ouuzDKpazsWk1VQkWFA4Xxk'
    chat_id = '-4236684694'
    bot = Bot(token=bot_token)
    with open(img_path, 'rb') as photo:
        bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)


def process_item(item, base_url, thread):
    print(psutil.virtual_memory().percent)
    while psutil.virtual_memory().percent > 70:
        print("Высокая загрузка памяти. Ожидание...")
        time.sleep(10)
    post_url = f"{base_url}{item['service']}/user/{item['user']}/post/{item['id']}"
    if not_check_already(post_url) and not_minus_words(item['title']):

        media_urls = extract_media_urls(item)


        for media_url in media_urls:
            if (is_image(media_url) and detect_objects(media_url, item, post_url)):
                break
            elif (is_video(media_url) and detect_in_video(media_url, item, post_url)):
                break
        with open('already.txt', 'a', encoding='utf-8') as file:
          file.write(f"{post_url}\n")

    global processed_elements
    processed_elements += 1
    print_progress()


def collect_posts(api_url, query):
    task_queue = Queue()
    offset = 0
    step = 50

    while True:
        request_url = f'{api_url}?q={query}&o={offset}'
        print(request_url)
        response = requests.get(request_url)
        if response.status_code != 200:
            print(f"Failed to fetch data at offset {offset}: {response.status_code}")
            break

        data = response.json()
        if not data:
            break

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
        except queue.Empty:
            break

def start_processing(api_url, query, threads=16):
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

# Пример вызова
api_url = "https://coomer.su/api/v1/posts"
# queries = ["🌴+-fjlsjfg"]
queries = ["leid"]

for query in queries:
    start_processing(api_url, query, threads=64)

