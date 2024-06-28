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



response = requests.get('')
if response and response.status_code == 200:
  with Image.open(BytesIO(response.content)).convert("RGB") as image:
    results = model.predict(image)
    results.show()  # Рисуем рамки на изображении