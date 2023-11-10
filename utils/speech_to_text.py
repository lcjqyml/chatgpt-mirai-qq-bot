import speech_recognition as sr
from loguru import logger
from werkzeug.datastructures import FileStorage
import os
import time


def get_random_name(speech_file):
    current_time = int(time.time() * 1000)
    file_extension = os.path.splitext(speech_file.filename)[1]
    return f'/tmp/{current_time}{file_extension}'


async def speech_to_text(speech_file):
    logger.info(8)
    if not speech_file:
        return ""
    file_path = speech_file
    if isinstance(file_path, FileStorage):
        file_path = get_random_name(speech_file)
        await speech_file.save(file_path)
    r = sr.Recognizer()
    logger.info(9)
    # 使用AudioFile方法打开音频文件
    with sr.AudioFile(file_path) as source:
        logger.info(10)
        # 使用record方法录制音频数据
        audio_data = r.record(source)
    logger.info(11)
    # 使用recognize_google方法将音频数据转换为文字
    text = r.recognize_google(audio_data, language="zh-CN")
    logger.info(12)
    logger.debug(f"Speech to text done. -> {text}")
    return text
