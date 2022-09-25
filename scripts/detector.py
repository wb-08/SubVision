import os
import torch
from PIL import Image
from mss import mss
import numpy as np
from time import sleep
import pytesseract
import logging
from image_utils import get_recent_images, find_intersection, image_processing
from connector import Pushing

os.environ['TESSDATA_PREFIX'] = '/usr/local/share/tessdata/'
logger = logging.getLogger('logger')
logging.getLogger("yolov5").setLevel(logging.WARNING)

model = torch.hub.load(os.environ['MODEL_PATH'], 'custom',
                       path=os.environ['MODEL'], source='local')
model.conf = float(os.environ['MODEL_CONFIDENCE'])
model.max_det = int(os.environ['MODEL_MAX_DETECTIONS'])
sct = mss()


def text_recognition(output_conn, image):
    """
    extracting text from the image
    """
    dilate_image = image_processing(image, only_dilate=True, make_border=True, iterations=1)
    text = pytesseract.image_to_string(dilate_image, lang='eng',
                                           config=r'--psm 3 --oem 2', output_type=pytesseract.Output.DICT)['text']
    clean_text = " ".join([str(i.lower()) for i in text.splitlines()])
    logger.info(clean_text)
    output_conn.put({'text': clean_text})


if __name__ == '__main__':
    logger.info("Starting detector")
    output_connector = Pushing(port=int(os.environ['DETECTOR_INPUT_PORT']))
    while True:
        w, h = 1920, 1080
        monitor = {'top': 0, 'left': 0, 'width': w, 'height': h}
        img = Image.frombytes('RGB', (w, h), sct.grab(monitor).rgb)
        result = model(np.array(img), size=640)
        crops = result.crop(save=True, save_dir=os.environ['CROP_DIR'])
        images = get_recent_images()
        if images:
            main_image, res = find_intersection(images[0], images[1], images[2])
            if res == 'difference':
                text_recognition(output_connector, main_image)
                logger.info(images[2])
                logger.info('-'*50)
                sleep(2)
