import os
import requests
import pandas as pd

# Указываем путь к файлу Excel
excel_path = 'table3.xlsx'
# Загружаем данные
data = pd.read_excel(excel_path)

# Создаем папку images, если она не существует
if not os.path.exists('images'):
    os.makedirs('images')

# Обрабатываем каждый URL в столбце image_url
for i, url in enumerate(data['image_url']):
    # Проверяем, заканчивается ли URL на .jpg или .jpeg
    if url.lower().endswith(('.jpg', '.jpeg')):
        try:
            # Получаем содержимое по URL
            response = requests.get(url)
            # Проверяем статус-код ответа
            if response.status_code == 200:
                # Форматируем имя файла
                filename = f"{i+701:04d}.jpg"  # Нумерация файлов начинается с 0001.jpg
                # Путь к файлу
                file_path = os.path.join('images', filename)
                # Сохраняем файл
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"Файл {filename} успешно сохранен.")
        except Exception as e:
            print(f"Не удалось загрузить изображение {url}: {e}")
