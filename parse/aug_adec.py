import cv2
import albumentations as A
import os
import random
import shutil


def load_yolo_annotations(filename, img_width, img_height):
    with open(filename, 'r') as file:
        lines = file.readlines()
        bboxes = []
        for line in lines:
            parts = line.strip().split()
            x_center, y_center, width, height = map(float, parts[1:])
            x_min = (x_center - width / 2) * img_width
            y_min = (y_center - height / 2) * img_height
            x_max = (x_center + width / 2) * img_width
            y_max = (y_center + height / 2) * img_height
            bboxes.append([x_min, y_min, x_max, y_max, int(parts[0])])
    return bboxes

def save_yolo_annotations(filename, bboxes, img_width, img_height):
    with open(filename, 'w') as file:
        for bbox in bboxes:
            x_min, y_min, x_max, y_max, class_id = bbox
            x_center = ((x_min + x_max) / 2) / img_width
            y_center = ((y_min + y_max) / 2) / img_height
            width = (x_max - x_min) / img_width
            height = (y_max - y_min) / img_height
            file.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

def augment_and_save(image_path, annotation_path, output_folder, aug, img_number):
    image = cv2.imread(image_path)
    img_width, img_height = image.shape[1], image.shape[0]
    bboxes = load_yolo_annotations(annotation_path, img_width, img_height)
    class_labels = [bbox[4] for bbox in bboxes]
    transformed = aug(image=image, bboxes=bboxes, class_labels=class_labels)
    transformed_image = transformed['image']
    transformed_bboxes = transformed['bboxes']

    # Create directories if they don't exist
    output_image_folder = os.path.join(output_folder, "images")
    output_label_folder = os.path.join(output_folder, "labels")
    os.makedirs(output_image_folder, exist_ok=True)
    os.makedirs(output_label_folder, exist_ok=True)

    # Construct new filenames for augmented images
    new_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_aug_{img_number}.jpg"
    new_annotation_filename = f"{os.path.splitext(os.path.basename(annotation_path))[0]}_aug_{img_number}.txt"
    
    # Save augmented image and annotations
    cv2.imwrite(os.path.join(output_image_folder, new_filename), transformed_image)
    save_yolo_annotations(os.path.join(output_label_folder, new_annotation_filename), transformed_bboxes, img_width, img_height)

    # Additionally save original images with '_original' suffix if it's the first augmentation only
    if img_number == 0:
        original_image_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_original.jpg"
        original_annotation_filename = f"{os.path.splitext(os.path.basename(annotation_path))[0]}_original.txt"
        shutil.copy2(image_path, os.path.join(output_image_folder, original_image_filename))
        shutil.copy2(annotation_path, os.path.join(output_label_folder, original_annotation_filename))


aug_pipeline = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.OneOf([
        A.RandomGamma(gamma_limit=(90, 110), p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),
    ], p=0.75),
    A.OneOf([
        A.Blur(blur_limit=(3, 7), p=0.5),  # Уточнение, что минимальное значение blur_limit равно 3
        A.GaussianBlur(blur_limit=(3, 7), p=0.5)  # То же для GaussianBlur
    ], p=0.75),
    A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.05, rotate_limit=15, p=0.75)
], bbox_params=A.BboxParams(
    format='pascal_voc', 
    label_fields=['class_labels'],
    min_area=0.2,
    min_visibility=0.5,
    check_each_transform=True
))



# Path to your images and annotations
image_folder = 'test_images/images'
annotation_folder = 'test_images/labels'
output_folder = 'aug_images'

# Processing each image and its annotation
for i, filename in enumerate(os.listdir(image_folder)):
    if filename.endswith('.jpg'):
        image_path = os.path.join(image_folder, filename)
        annotation_path = os.path.join(annotation_folder, filename.replace('.jpg', '.txt'))
        for j in range(5):  # Change the range to increase/decrease the number of augmentations per image
            augment_and_save(image_path, annotation_path, output_folder, aug_pipeline, j)


#=================== Далее пермешивание файлов =====================================================

print('hello')
def rename_and_shuffle(image_folder, annotation_folder, output_image_folder, output_annotation_folder):
    # Создаем выходные папки, если они не существуют
    os.makedirs(output_image_folder, exist_ok=True)
    os.makedirs(output_annotation_folder, exist_ok=True)

    # Загружаем список файлов
    images = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]
    random.shuffle(images)  # Перемешиваем изображения

    # Переименовываем файлы
    for idx, filename in enumerate(images):
        # Получаем новое имя файла
        new_name = f"{idx + 1:04d}.jpg"
        old_image_path = os.path.join(image_folder, filename)
        old_annotation_path = os.path.join(annotation_folder, filename.replace('.jpg', '.txt'))
        new_image_path = os.path.join(output_image_folder, new_name)
        new_annotation_path = os.path.join(output_annotation_folder, new_name.replace('.jpg', '.txt'))

        # Копируем файлы в новое местоположение с новыми именами
        shutil.copy2(old_image_path, new_image_path)
        if os.path.exists(old_annotation_path):
            shutil.copy2(old_annotation_path, new_annotation_path)

# Пути к папкам
image_folder = 'aug_images/images'
annotation_folder = 'aug_images/labels'
output_image_folder = 'aug_images_sorted/images'
output_annotation_folder = 'aug_images_sorted/labels'

# Вызов функции
rename_and_shuffle(image_folder, annotation_folder, output_image_folder, output_annotation_folder)
