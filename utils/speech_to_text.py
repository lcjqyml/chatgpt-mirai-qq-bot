import os
import re
import time

import soundfile as sf
import speech_recognition as sr
from aip import AipSpeech
from loguru import logger
from werkzeug.datastructures import FileStorage

from constants import config


def init_google_converter():
    if config.speech_to_text.engine == 'google':
        return sr.Recognizer()
    return None


def init_baidu_converter():
    if config.speech_to_text.engine == 'baidu':
        return AipSpeech(config.speech_to_text.app_id, config.speech_to_text.api_key, config.speech_to_text.secret_key)
    return None


baidu_converter = init_baidu_converter()
google_converter = init_google_converter()


def get_content_type(audio_data):
    # 使用正则表达式提取文件格式
    match = re.search(r"data:audio/(\w+);", audio_data)
    file_extension = ""
    if match:
        file_extension = match.group(1)
    return file_extension


def get_random_name(speech_file):
    current_time = int(time.time() * 1000)
    if isinstance(speech_file, FileStorage):
        file_extension = os.path.splitext(speech_file.filename)[1].lower()
    elif speech_file.startswith("data:audio"):
        file_extension = f'.{get_content_type(speech_file)}'
    else:
        raise Exception("error file.")
    return f'/tmp/{current_time}{file_extension}'


def convert_by_google(file_path, language):
    file_extension = os.path.splitext(file_path)[1]
    if file_extension not in ['.wav', '.aiff', '.flac']:
        logger.warning(f"Only support wav/aiff/flac in google engine. -> {file_path}")
        return ""
    # 使用AudioFile方法打开音频文件
    with sr.AudioFile(file_path) as source:
        # 使用record方法录制音频数据
        audio_data = google_converter.record(source)
    # 使用recognize_google方法将音频数据转换为文字
    return google_converter.recognize_google(audio_data, language)


def convert_by_baidu(file_path, language):
    file_extension = os.path.splitext(file_path)[1]
    if file_extension not in ['.pcm', '.wav', '.amr']:
        logger.warning(f"Only support pcm/wav/amr in baidu engine. -> {file_path}")
        return ""
    if language != 'zh-CN':
        logger.warning(f"Only support zh-CN in baidu engine. -> {language}")
        return ""
    with open(file_path, 'rb') as fp:
        fr = fp.read()
    try:
        return baidu_converter.asr(fr, file_extension.lstrip("."), 16000, {
            'dev_pid': 1537,
        }).get('result')[0]
    except Exception as ee:
        logger.exception(ee)
        return ""


def convert_data_to_file(audio_data, file_path):
    import base64
    audio_data = audio_data.split(",")[1]
    # 使用base64库解码音频数据
    audio_data = base64.b64decode(audio_data)
    with open(file_path, "wb") as f:
        # 将音频数据写入文件
        f.write(audio_data)


def speech_to_text(speech_file, language="zh-CN"):
    if not speech_file:
        return ""
    file_path = speech_file
    if isinstance(file_path, FileStorage):
        file_path = get_random_name(speech_file)
        data, _sr = sf.read(speech_file)
        sf.write(file_path, data, _sr)
    elif speech_file.startswith("data:audio"):
        file_path = get_random_name(speech_file)
        convert_data_to_file(speech_file, file_path)
    if config.speech_to_text.engine == 'google':
        # support wav/aiff/flac
        text = convert_by_google(file_path, language)
    elif config.speech_to_text.engine == 'baidu':
        # support pcm/wav/amr
        text = convert_by_baidu(file_path, language)
    else:
        return ""
    logger.debug(f"Speech to text done. -> {text}")
    return text


if __name__ == '__main__':
    try:
        speech_to_text("C:\\Users\\Milin3\\Desktop\\介绍你自己.wav")
    except Exception as e:
        logger.exception(e)
