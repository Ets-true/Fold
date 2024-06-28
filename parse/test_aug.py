import cv2
import numpy as np

def draw_bboxes(img_path, label_path):
    # Словарь для меток классов
    labels = {
        0: "coconut bra",
        1: "hula skirt",
        2: "flower lei"
    }
    
    # Читаем изображение
    image = cv2.imread(img_path)
    height, width, _ = image.shape

    # Читаем аннотации из файла
    with open(label_path, 'r') as file:
        lines = file.readlines()

    # Рисуем каждую ограничивающую рамку
    for line in lines:
        parts = line.strip().split()
        class_id = int(parts[0])
        x_center, y_center, bbox_width, bbox_height = map(float, parts[1:])
        x_center *= width
        y_center *= height
        bbox_width *= width
        bbox_height *= height

        x_min = int(x_center - bbox_width / 2)
        y_min = int(y_center - bbox_height / 2)
        x_max = int(x_center + bbox_width / 2)
        y_max = int(y_center + bbox_height / 2)

        # Рисуем прямоугольник на изображении
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        # Добавляем метку класса к прямоугольнику
        cv2.putText(image, labels[class_id], (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

    # Показываем изображение
    cv2.imshow("Image with BBoxes", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Пути к файлам
img_path = 'aug_images_sorted/images/0004.jpg'
label_path = 'aug_images_sorted/labels/0004.txt'

# Вызываем функцию для рисования ограничивающих рамок
draw_bboxes(img_path, label_path)
