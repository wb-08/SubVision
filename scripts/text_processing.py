import os
from googletrans import Translator
from difflib import Differ
import enchant
import logging
from connector import Pulling, Pushing

logger = logging.getLogger('logger')


def replacement(text):
    # TODO: maybe replace one separate T with I
    text = text.replace('|', 'I')
    text = text.replace('1', 'I')
    return text


def find_text_diff(previous_text, current_text):
    """
    calculate the difference between two texts
    """
    text_diff = Differ().compare(previous_text.split(), current_text.split())
    return " ".join(str(word) for word in list(word[2:] for word in text_diff if word.startswith(("+"))))


def text_correction(current_text, previous_text):
    """
    spell check of words
    """
    current_text = replacement(current_text)
    current_text = find_text_diff(previous_text, current_text)
    dct = enchant.Dict("en_US")
    current_text = list(filter(len, current_text.split(' ')))
    for i, word in enumerate(current_text):
        right_word = dct.check(word)
        if not right_word:
            try:
                current_text[i] = dct.suggest(word)[0]
            except IndexError:
                current_text[i] = None
    text = [word for word in current_text if word is not None]
    text = " ".join(str(word) for word in text)
    return text


def text_translate(input_conn, output_conn, previous_text):
    current_text = input_conn.get()['text']
    foreign_text = text_correction(current_text, previous_text)
    if foreign_text:
        translator = Translator()
        from_lang = 'en'
        to_lang = 'ru'
        text_to_translate = translator.translate(foreign_text, src=from_lang, dest=to_lang)
        output_conn.put({'translate_text': text_to_translate.text})
        return foreign_text
    else:
        return ''


if __name__ == '__main__':
    logger.info("Starting text processing")
    previous_text = ['not previous text']
    input_connector = Pulling(port=int(os.environ['PROCESSING_INPUT_PORT']), host=os.environ['HOST'])
    output_connector = Pushing(port=int(os.environ['PROCESSING_OUTPUT_PORT']))
    while True:
        foreign_text = text_translate(input_connector, output_connector, previous_text[0])
        if foreign_text:
            previous_text[0] = foreign_text
