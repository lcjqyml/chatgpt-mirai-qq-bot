import json
import os
import sys
from typing import Tuple

from loguru import logger
from requests.exceptions import SSLError

import chatbot
from config import Config
from pojo.Constants import InteractiveMode

sys.path.append(os.getcwd())

config = Config.load_config()


def get_session_summary(session):
    token_info = None
    if session.is_v3_api():
        token_info = f"{session.chatbot.bot.get_token_count(session.session_id)}/{session.chatbot.bot.max_tokens}"
    tmp_summary = {
        "api_version": session.api_version,
        "interactive_mode": session.interactive_mode.description() if session.interactive_mode else None,
        "token_info": token_info
    }
    return json.dumps(tmp_summary, default=ignore_none)


def ignore_none(value):
    # 忽略值为 None 的属性
    if value is None:
        return None
    else:
        return value


async def handle_message(bot_id: str, message: str, api_version: str = None) -> Tuple[str, str]:
    if not message.strip():
        return config.response.placeholder, ""

    session = chatbot.get_chat_session(bot_id, api_version)
    # ping
    if message.strip() in config.trigger.ping_command:
        return session.get_status(), ""

    # 回滚
    if message.strip() in config.trigger.rollback_command:
        resp = session.rollback_conversation()
        if resp:
            return config.response.rollback_success, get_session_summary(session)
        return config.response.rollback_fail, get_session_summary(session)

    # 队列满时拒绝新的消息
    if 0 < config.response.max_queue_size < session.chatbot.queue_size:
        return config.response.queue_full, get_session_summary(session)

    # 以下开始需要排队
    async with session.chatbot:
        try:
            # 重置会话
            if message.strip() in config.trigger.reset_command:
                session.reset_conversation()
                if session.is_chat_mode():
                    return config.response.reset_chat.format(system_prompt=session.get_system_prompt()), \
                           get_session_summary(session)
                elif session.is_qa_mode():
                    return config.response.reset_qa, get_session_summary(session)
                else:
                    return config.response.reset, get_session_summary(session)
            if session.is_v3_api():
                # 聊天模式
                if message.strip() in config.trigger.chat_command:
                    session.reset_conversation(interactive_mode=InteractiveMode.CHAT)
                    return config.response.reset_chat.format(
                        system_prompt=session.get_system_prompt()), get_session_summary(session)
                # qa模式
                if message.strip() in config.trigger.qa_command:
                    session.reset_conversation(interactive_mode=InteractiveMode.Q_A)
                    return config.response.reset_qa, get_session_summary(session)
            # 正常交流
            resp = await session.get_chat_response(message)
            interactive_mode_info = "interactive_mode[" + session.interactive_mode.value + "] - " \
                if session.interactive_mode else ""
            if resp:
                session_summary = get_session_summary(session)
                logger.debug(f"session_id[{bot_id}] - "
                             f"api_version[{session.api_version}] - "
                             f"{interactive_mode_info}"
                             f"chatbot_id[{session.chatbot.id}] - "
                             f"session_summary{session_summary}")
                return resp.strip(), session_summary
        except SSLError as e:
            logger.exception(e)
            return config.response.error_network_failure.format(exc=e), get_session_summary(session)
        except Exception as e:
            # Other un-handled exceptions
            if 'Too many requests' in str(e):
                return config.response.error_request_too_many.format(exc=e), get_session_summary(session)
            elif 'overloaded' in str(e) or 'Only one message at a time' in str(e):
                return config.response.error_server_overloaded.format(exc=e), get_session_summary(session)
            elif 'Unauthorized' in str(e):
                return config.response.error_session_authenciate_failed.format(exc=e), \
                       get_session_summary(session)
            logger.exception(e)
            return config.response.error_format.format(exc=e), get_session_summary(session)
    # 排队结束
