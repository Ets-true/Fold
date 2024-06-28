import os
from PIL import Image

# Папка с изображениями
folder_path = 'images'

# Получаем список всех файлов в папке
files = os.listdir(folder_path)

# Перебираем файлы
for file in files:
    # Формируем полный путь к файлу
    file_path = f"{folder_path}/{file}"
    # print(file_path)
    # Открываем изображение
    try:
        with Image.open(file_path) as img:
            # Получаем размеры изображения
            width, height = img.size
            # Проверяем условие размера
            if width < 600 or height < 600:
                img.close()
                # Удаляем изображение, если оно не соответствует условию
                os.remove(file_path)
                print(f"Изображение {file} удалено, так как его размеры меньше 600 px.")
    except Exception as e:
        print(f"Не удалось обработать файл {file}: {e}")
