import speech_recognition as sr
from loguru import logger


def speech_to_text(speech_file):
    logger.info(8)
    if not speech_file:
        return ""
    r = sr.Recognizer()
    logger.info(9)
    # 使用AudioFile方法打开音频文件
    with sr.AudioFile(speech_file) as source:
        logger.info(10)
        # 使用record方法录制音频数据
        audio_data = r.record(source)
    logger.info(11)
    # 使用recognize_google方法将音频数据转换为文字
    text = r.recognize_google(audio_data)
    logger.info(12)
    logger.debug(f"Speech to text done. -> {text}")
    return text
