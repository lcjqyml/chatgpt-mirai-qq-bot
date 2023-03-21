import asyncio
import json
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
from pojo.Constants import Constants

sys.path.append(os.getcwd())

config = Config.load_config()
processed_messages = deque(maxlen=100)


@request_map("/v1/chatbot/ask/{session_id}", method=["post"])
async def chatgpt_v1_ask(data=JSONBody(), session_id=PathValue(), time=""):
    return await ask(data=data, bot_id=session_id, time=time, api_version=Constants.V1_API.value)


@request_map("/v3/chatbot/ask/{session_id}", method=["post"])
async def chatgpt_v3_ask(data=JSONBody(), session_id=PathValue(), time=""):
    return await ask(data=data, bot_id=session_id, time=time, api_version=Constants.V3_API.value)


@request_map("/poe/chatbot/ask/{bot_name}", method=["post"])
async def chatgpt_poe_ask(data=JSONBody(), bot_name=PathValue(), time=""):
    return await ask(data=data, bot_id=bot_name, time=time, api_version=Constants.POE_API.value)


@request_map("/v_/chatbot/ask/{session_id}", method=["post"])
async def chatgpt_v_ask(data=JSONBody(), session_id=PathValue(), time=""):
    return await ask(data=data, bot_id=session_id, time=time, api_version=None)


async def ask(data=JSONBody(), bot_id=None, time="", api_version: str = None):
    message = bot_id + "[" + time + "]: " + data['message']
    logger.info("API[" + (api_version if api_version else "_") + "]: " + message)
    session_summary = ""
    if message in processed_messages:
        response = "skip"
    else:
        # JSONBody 是 dict 的子类，你可以直接其是一个 dict 来使用
        response, session_summary = await handle_message(bot_id=bot_id, message=data['message'],
                                                         api_version=api_version)
        processed_messages.append(message)
    logger.info(response)
    response_obj = {"success": response}
    if session_summary != "":
        response_obj["session_summary"] = json.loads(session_summary)
    return response_obj


def main(*args):
    task_list = [login_openai(), server.start(host="", port=8080)]
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
