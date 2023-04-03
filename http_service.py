import asyncio
import json
import os
import sys
from collections import deque

from flask import Flask, request
from loguru import logger

import chatbot
from bot import handle_message
from config import Config
from pojo.Constants import Constants

sys.path.append(os.getcwd())

config = Config.load_config()
processed_messages = deque(maxlen=100)
app = Flask(__name__)


@app.route("/v1/chatbot/ask/<session_id>", methods=["post"])
async def chatgpt_v1_ask(session_id):
    return await ask(bot_id=session_id, api_version=Constants.V1_API.value)


@app.route("/v3/chatbot/ask/<session_id>", method=["post"])
async def chatgpt_v3_ask(session_id):
    return await ask(bot_id=session_id, api_version=Constants.V3_API.value)


@app.route("/poe/chatbot/ask/<bot_name>", method=["post"])
async def chatgpt_poe_ask(bot_name):
    return await ask(bot_id=bot_name, api_version=Constants.POE_API.value)


@app.route("/v_/chatbot/ask/{session_id}", method=["post"])
async def chatgpt_v_ask(session_id):
    return await ask(bot_id=session_id, api_version=None)


async def ask(bot_id=None, api_version: str = None):
    request_message = request.json.get("message")
    request_time = request.args.get("time")
    message = bot_id + "[" + request_time + "]: " + request_message
    logger.info("API[" + (api_version if api_version else "_") + "]: " + message)
    session_summary = ""
    if message in processed_messages:
        response = "skip"
    else:
        # JSONBody 是 dict 的子类，你可以直接其是一个 dict 来使用
        response, session_summary = await handle_message(bot_id=bot_id, message=request_message,
                                                         api_version=api_version)
        processed_messages.append(message)
    logger.info(response)
    response_obj = {"success": response}
    if session_summary != "":
        response_obj["session_summary"] = json.loads(session_summary)
    return response_obj


def main():
    task_list = [login_openai()]
    loops = asyncio.get_event_loop()
    loops.run_until_complete(asyncio.wait(task_list))
    app.run(host="0.0.0.0", port=8080, debug=True)


async def login_openai():
    try:
        logger.info("OpenAI 服务器登录中……")
        chatbot.setup()
    except Exception as e:
        logger.error("OpenAI 服务器失败！")
        exit(-1)


if __name__ == "__main__":
    main()
