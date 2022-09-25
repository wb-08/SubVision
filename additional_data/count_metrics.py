import os
import json
import fastwer
import cv2
import pytesseract
from pytesseract import Output

os.environ['TESSDATA_PREFIX'] = '/usr/local/share/tessdata/'
subtitle_folder = 'test_markup/'
image_folder = 'test_images/'
check_file = 'check.json'


def read_json_file(json_file):
    file = open(json_file)
    data = json.load(file)
    return data


def extract_bboxes(json_file):
    """
    Extract bounding boxes of subtitles from json_file
    Parameters:
        json_file (str): name of the  json file

    Returns:
        bboxes (list of float): bounding boxes of subtitles
    """
    data = read_json_file(json_file)
    return list(map(int, sum(data['shapes'][0]['points'], [])))


def crop_image(image_name, bboxes):
    """
    Cutting out a fragment with subtitles from an image

    Parameters:
        image_name (str) : name of the input image
        bboxes (list of float): bounding boxes of subtitles

    Returns:
       subtitle_image (np.array): part of the image with subtitles
    """
    image = cv2.imread(image_name)
    subtitle_image = image[bboxes[1]:bboxes[3], bboxes[0]:bboxes[2]]
    return subtitle_image


def image_processing(image):
    """
    image processing like binarization, dilatation
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh_img = cv2.threshold(gray, 200, 255,
                                  cv2.THRESH_BINARY)
    dilate_image = cv2.morphologyEx(thresh_img, cv2.MORPH_OPEN, kernel, iterations=1)
    return dilate_image


def text_recognition(image):
    """
    extracting text from the image
    """
    dilate_image = image_processing(image)
    text = pytesseract.image_to_string(dilate_image, lang='eng', config=r'--psm 3 --oem 2',
                                       output_type=Output.DICT)['text']
    clean_text = "".join([str(i.lower()) for i in text.splitlines()])
    return clean_text


def extract_reference_text(json_file, image_name):
    data = read_json_file(json_file)
    return data[image_name]


def calculate(ref, output):
    """
    Calculate Character Error Rate (CER) and Word Error Rate (WER)
    Parameters:
		ref (str): reference text
		output (str): output text
	Returns:
        cer (float): Character Error Rate value
		wer (float): Word Error Rate value
    """
    cer = fastwer.score_sent(output, ref, char_level=True)
    wer = fastwer.score_sent(output, ref)
    return cer, wer


if __name__ == '__main__':
    for subtitle_file in os.listdir(subtitle_folder):
        bboxes = extract_bboxes(subtitle_folder+subtitle_file)
        image_name = subtitle_file.split('.')[0] + '.png'
        subtitle_image = crop_image(image_folder+image_name, bboxes)
        output_text = text_recognition(subtitle_image)
        ref_text = extract_reference_text(check_file, image_name)
        cer, wer = calculate(ref_text, output_text)
