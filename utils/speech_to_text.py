import speech_recognition as sr
from loguru import logger


def speech_to_text(speech_file):
    if not speech_file:
        return ""
    r = sr.Recognizer()
    # 使用AudioFile方法打开音频文件
    with sr.AudioFile(speech_file) as source:
        # 使用record方法录制音频数据
        audio_data = r.record(source)
    # 使用recognize_google方法将音频数据转换为文字
    text = r.recognize_google(audio_data)
    logger.debug(f"Speech to text done. -> {text}")
    return text
