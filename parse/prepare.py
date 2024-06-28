import os
from PIL import Image

def resize_and_pad(img, target_size):
    # Сначала масштабируем с сохранением пропорций
    img.thumbnail(target_size, Image.Resampling.LANCZOS)  # Используем Image.Resampling.LANCZOS вместо Image.ANTIALIAS
    # Создаем новое изображение с черными полосами (padding)
    new_img = Image.new("RGB", target_size, (0, 0, 0))
    # Получаем координаты для центрирования изображения
    left = (target_size[0] - img.width) // 2
    top = (target_size[1] - img.height) // 2
    new_img.paste(img, (left, top))
    return new_img

def process_images(input_folder, output_folder, size=(640, 640)):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    files.sort()  # Сортировка файлов для сохранения порядка

    for i, filename in enumerate(files, 1):
        with Image.open(os.path.join(input_folder, filename)) as img:
            # Изменяем размер и добавляем padding
            processed_img = resize_and_pad(img, size)
            # Форматируем новое имя файла с нумерацией
            new_filename = f"{i:04d}.jpg"
            # Сохраняем обработанное изображение
            processed_img.save(os.path.join(output_folder, new_filename))
            print(f"Processed {new_filename}")

# Используйте функцию
input_folder = 'images'  # Укажите путь к папке с исходными изображениями
output_folder = 'prepared_images'  # Укажите путь к папке, куда сохранять обработанные изображения

process_images(input_folder, output_folder)
