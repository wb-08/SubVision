import cv2
import os
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger('logger')


def sort_contours(cnts, method):
    bounding_boxes = [cv2.boundingRect(c) for c in cnts]
    if method == "left-to-right":
        bounding_boxes.sort(key=lambda tup: tup[0])
    return bounding_boxes


def avg_value(value):
    try:
        return sum(value) / len(value)
    except ZeroDivisionError:
        return 0


def find_numerical_error_rate(size, error=150):
    return size*error/100


def image_processing(image, only_dilate=False, make_border=False, iterations=1):
    """
    image processing like binarization, dilatation
    """
    if only_dilate:
        structuring_element = np.ones((1, 2), np.uint8)
        transformation_image = cv2.dilate(image, structuring_element, iterations=iterations)

        if make_border:
            transformation_image = cv2.copyMakeBorder(transformation_image, 2, 2, 1, 1, cv2.BORDER_CONSTANT, None, value=0)

    else:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh_img = cv2.threshold(gray, 200, 255,
                                  cv2.THRESH_BINARY)
        transformation_image = cv2.morphologyEx(thresh_img, cv2.MORPH_OPEN, kernel, iterations=1)
    return transformation_image


def get_recent_images():
    """
    get the latest images that were found by detector
    """
    # TODO: deleting images when the container stops
    try:
        last_images = sorted(Path(os.environ['CROP_FULL_DIR']).iterdir(), key=os.path.getmtime)[-3:]
        first_image, second_image, last_image = str(last_images[0]), str(last_images[1]), str(last_images[2])
        return [second_image, last_image, first_image]
    except (FileNotFoundError, IndexError):
        return False


def find_text_bboxes(image):
    """
    find the bounding boxes of each letter in the
    image and crop the image at these coordinates
    """
    cnts, _ = cv2.findContours(
                image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = sort_contours(cnts, method="left-to-right")
    bounding_boxes = [list(bbox) for bbox in bounding_boxes]
    if len(bounding_boxes) == 0:
        return "Can't find bboxes"

    avg_width = avg_value([w for x, y, w, h in bounding_boxes])
    avg_height = avg_value([h for x, y, w, h in bounding_boxes])
    right_contours = []
    for x, y, w, h in bounding_boxes:
        if avg_width-find_numerical_error_rate(avg_width, error=100) < w < avg_width+find_numerical_error_rate(avg_width) and \
           avg_height-find_numerical_error_rate(avg_height, error=25) < h < avg_height+find_numerical_error_rate(avg_height):
            right_contours.append([x, y, w, h])
        else:
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 0), -1)

    max_letter_height = min([y for x, y, w, h in right_contours])
    min_letter_height = max([y+h for x, y, w, h in right_contours ])
    min_letter_width = min([x for x, y, w, h in right_contours])
    image = image[max_letter_height:min_letter_height, min_letter_width:image.shape[1]]
    return image


def find_intersection(img1, img2, img3):
    """
    Find intersection between binary images
    """
    img1 = cv2.imread(img1)
    img2 = cv2.imread(img2)
    img3 = cv2.imread(img3)

    img1 = image_processing(img1)
    img2 = image_processing(img2)
    img3 = image_processing(img3)

    img1 = find_text_bboxes(img1)
    img2 = find_text_bboxes(img2)
    img3 = find_text_bboxes(img3)

    if img1 == "Can't find bboxes" or img2 == "Can't find bboxes":
        logger.info("Can't find bboxes")
        return img3, 'difference'
    else:
        height_diff = abs(img1.shape[0] - img2.shape[0])
        width_diff = abs(img1.shape[1] - img2.shape[1])

        if img2.shape[1] > img1.shape[1]:
            img1 = cv2.copyMakeBorder(img1, 0, 0, 0, img2.shape[1]-img1.shape[1], cv2.BORDER_CONSTANT, None, value=0)

        if img1.shape[1] > img2.shape[1]:
            img2 = cv2.copyMakeBorder(img2, 0, 0, 0, img1.shape[1] - img2.shape[1], cv2.BORDER_CONSTANT, None, value=0)

        if img1.shape[0] > img2.shape[0]:
            img2 = cv2.copyMakeBorder(img2, 0, img1.shape[0]-img2.shape[0], 0, 0, cv2.BORDER_CONSTANT, None, value=0)

        if img2.shape[0] > img1.shape[0]:
            img1 = cv2.copyMakeBorder(img1, 0, img2.shape[0] - img1.shape[0], 0, 0, cv2.BORDER_CONSTANT, None, value=0)

        img4 = cv2.copyMakeBorder(img1, height_diff, height_diff, width_diff, width_diff,
                                  cv2.BORDER_CONSTANT, None, value=0)

        result = cv2.matchTemplate(img2, img4, cv2.TM_CCOEFF_NORMED)
        _, maxVal, _, _ = cv2.minMaxLoc(result)

        if maxVal > 0.75:
            return img1, 'same'
        else:
            matches = []
            for iteration in range(3):
                img_bw = image_processing(cv2.bitwise_and(img1, img2), only_dilate=True, iterations=iteration)
                result = cv2.matchTemplate(img_bw, img4, cv2.TM_CCOEFF_NORMED)
                _, maxVal, _, _ = cv2.minMaxLoc(result)
                matches.append(maxVal)
            if max(matches) > 0.75:
                return img1, 'same'
            else:
                return img3, 'difference'
