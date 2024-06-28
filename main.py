import requests
from PIL import Image
from io import BytesIO

from yolov5 import YOLOv5
from telegram import Bot
from pathlib import Path
import pathlib


# import gdown

posix_backup = pathlib.PosixPath
try:
    pathlib.PosixPath = pathlib.WindowsPath
    model = YOLOv5('best.pt')
finally:
    pathlib.PosixPath = posix_backup




base_url = 'https://coomer.su/'

def send_telegram(message):
  print(message)


# Пример списка классов
class_names = ['coconut bra', 'hula skirt', 'flower lei', 'flower bra']
search_names = [ "hawaii", "hula", "luau", "aloha", "tiki","leid", "lei d", "lei'd"]

def not_check_already(target_line):
  with open('already.txt', 'r', encoding='utf-8') as file:
      for line in file:
        if line.strip() == target_line.strip():
          return False
  return True

def detect_objects(image_url, item):
    
    service = item.get("service", "")
    user = item.get("user", "")
    id = item.get("id", "")
    title = item.get("title", "")

    post_url = base_url + f'{service}/' + f'user/{user}/' + f'post/{id}'
    print(post_url)

    if not_check_already(post_url):
      if image_url.startswith('/'):
          image_url = image_url[1:]
      full_url = base_url + image_url  # Конкатенация URL
      response = requests.get(full_url)
      if response:
          print(full_url)
          image = Image.open(BytesIO(response.content))
          results = model.predict(image, augment=0.6)


          for *box, conf, cls in results.xyxy[0]:
              class_name = class_names[int(cls)]

              result_text = (
                      f'User: {user}\n'
                      f'Title: {title}\n'
                      f'Img: {full_url}\n'
                      f'Post: {post_url}\n'
                      f'{class_name} - {conf:.5f}'
                  )
              print(result_text)
              if conf > 0.6:
                with open('simple.txt', 'a') as file:
                  file.write(post_url)
                send_telegram_message(result_text)
                break
          with open('already.txt', 'a') as file:
            file.write(f'{post_url}\n')

          print('=========================================================')
    else: print('already checked')

def isImage(url):
  if url[-3:] == 'jpg' or url[-3:] == 'png' or url[-3:] == 'jpeg':
    return True
  else: return False



def send_telegram_message(message):
    bot_token = '6810766307:AAE-9MIiuW65ouuzDKpazsWk1VQkWFA4Xxk'  # Ваш токен
    chat_id = '-4236684694'  # Ваш ID чата
    bot = Bot(token=bot_token)
    bot.send_message(chat_id=chat_id, text=message)




# Функция для выполнения GET-запроса и обработки списка изображений
def process_images_from_url(api_url):
    for query in search_names: 
      step = 0
      api_url_full = api_url + f'?q={query}'
      while True:
        request_url = api_url_full + f'&o={step}'
        print(request_url)
        response = requests.get(request_url)
        step = step + 50
        if response.status_code == 200:
          data = response.json()
          if(len(data) > 0):
            for item in data:
              item_file = item.get('file')
              if (item.get('attachments') != [] and item['attachments'][0]['path'] and isImage(item['attachments'][0]['path'])):
                detect_objects(item['attachments'][0]['path'], item)
              elif (item_file and isImage(item_file['path'])):
                detect_objects(item_file['path'],item)
          else:
            break



# Пример использования
# api_url = "https://coomer.su/api/v1/posts?q=tropical&o="  # Замените на ваш реальный URL API
api_url = "https://coomer.su/api/v1/posts"  # Замените на ваш реальный URL API
process_images_from_url(api_url)
