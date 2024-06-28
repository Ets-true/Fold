import os
import random

def randomize_images(folder_path):
    # Получаем список файлов в папке
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    # Перемешиваем список файлов
    random.shuffle(files)

    # Переименовываем файлы с временными именами, чтобы избежать конфликтов
    temp_names = [os.path.join(folder_path, f"temp_{i:04d}.tmp") for i in range(len(files))]
    for original, temp in zip(files, temp_names):
        os.rename(os.path.join(folder_path, original), temp)

    # Переименовываем временные файлы в новую нумерацию
    for i, temp in enumerate(temp_names, 1):
        new_name = f"{i:04d}.jpg"  # предполагаем, что все файлы в формате PNG
        os.rename(temp, os.path.join(folder_path, new_name))

    print("Файлы успешно перемешаны и переименованы.")

# Задайте путь к вашей папке с изображениями
folder_path = 'prepared_images'
randomize_images(folder_path)
