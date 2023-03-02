import asyncio
import os
import re
import sys
from collections import deque

import simple_http_server.server as server
from loguru import logger
from bot import handle_message
from simple_http_server import JSONBody, PathValue
from simple_http_server import request_map

import chatbot
from config import Config

sys.path.append(os.getcwd())

config = Config.load_config()
processed_messages = deque(maxlen=100)


@request_map("/v1/chatgpt/ask/{session_id}", method=["post"])
async def chatgpt_ask(data=JSONBody(), session_id=PathValue(), time=""):
    message = session_id + "[" + time + "]: " + data['message']
    print(message)
    if message in processed_messages:
        response = "skip"
    else:
        ##
        #  JSONBody 是 dict 的子类，你可以直接其是一个 dict 来使用
        response = await handle_message(session_id=session_id, message=data['message'], silence=True, target=None, source=None)
        processed_messages.append(message)
    return {"success": response}


def main(*args):
    task_list = [login_openai(), server.start_async(host="", port=8080)]
    loops = asyncio.get_event_loop()
    loops.run_until_complete(asyncio.wait(task_list))


async def login_openai():
    try:
        logger.info("OpenAI 服务器登录中……")
        chatbot.setup()
    except Exception as e:
        logger.error("OpenAI 服务器失败！")
        exit(-1)


if __name__ == "__main__":
    main()
