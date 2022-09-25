import os
import PySimpleGUI as sg
import logging
import pyttsx3
import textwrap
from connector import Pulling

logger = logging.getLogger('logger')

INPUT_PORT = 9090


def text_dubbing(text):
    engine = pyttsx3.init()
    engine.setProperty('voice', 'ru')
    engine.setProperty('rate', 170)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()


def popup(input_conn):
    """
    displaying text on the screen
    """
    message = input_conn.get()['translate_text']
    message = textwrap.fill(message, 30)
    sg.set_options(font=("Courier New", 15))
    bg = '#add123'
    layout = [[sg.Text(message, background_color=bg, pad=(0, 0))]]
    win = sg.Window('title', layout, no_titlebar=True, keep_on_top=True,
        location=(100, 600), transparent_color=bg, margins=(0, 0), finalize=True)
    text_dubbing(message)
    win.close()


if __name__ == '__main__':
    logger.info("Starting text representation")
    input_connector = Pulling(port=int(os.environ['REPRESENTATION_INPUT_PORT']), host=os.environ['HOST'])
    while True:
        popup(input_connector)
