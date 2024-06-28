import os

def create_empty_annotations(image_folder, annotation_folder):
    # Получаем список всех изображений в папке images
    images = [img for img in os.listdir(image_folder) if img.endswith('.jpg')]
    
    # Перебираем список изображений
    for img in images:
        # Строим путь к файлу аннотации, соответствующему данному изображению
        annotation_file = os.path.join(annotation_folder, img.replace('.jpg', '.txt'))
        
        # Проверяем, существует ли файл аннотации
        if not os.path.exists(annotation_file):
            # Если файл аннотации не существует, создаем пустой файл
            with open(annotation_file, 'w') as f:
                pass  # Создаем пустой файл

# Укажите пути к папкам с изображениями и аннотациями
image_folder = 'test_images/images'
annotation_folder = 'test_images/labels'

# Вызываем функцию
create_empty_annotations(image_folder, annotation_folder)
