# Metadata
from __environ__ import TOKEN, DEVELOPMENT_MODE
from __version__ import __version__
__botname__ = 'Medication Reminder'

# Imports
from pathlib import Path
from telegram import ParseMode
from telegram.ext import CommandHandler, Defaults, Updater, PicklePersistence
from utils.command_util import Command, Parameter, dumpall

from commands import calc_time, generate_version, say, getcontext
from reminder import Remindee, generate_remind
from medication import REGISTER_CONVERSATION, list_all

# Logging
import sys
import logging
from rainbow_logging_handler import RainbowLoggingHandler
root_logger = logging.getLogger()
root_logger.setLevel(level="DEBUG" if DEVELOPMENT_MODE else "INFO")
formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
fileHandler = logging.FileHandler("bot.log")
fileHandler.setFormatter(formatter)
streamHandler = RainbowLoggingHandler(sys.stdout)
streamHandler.setFormatter(formatter)
root_logger.addHandler(fileHandler)
root_logger.addHandler(streamHandler)
logger = logging.getLogger(__name__) 

def main():
    logger.info(f"Running {__botname__} BOT version {__version__}...")
    updater = Updater(
        defaults = Defaults(
            parse_mode = ParseMode.HTML,
            disable_notification=True,
            disable_web_page_preview=False
        ),
        token = TOKEN,
        use_context = True,
        persistence=PicklePersistence(Path(__file__).parent / "bot.db"),
    )
    dispatcher = updater.dispatcher

    # Register commands
    COMMANDS = [
        Command('version', generate_version(__version__), 'バージョン表示', []),
        Command('calc', calc_time, '時間計算', [Parameter('equation', str, '公式')], last_ignore_space=True),
        Command('say', say, '說話', [
            Parameter('chat_id', str, '聊天ID'),
            Parameter('content', str, '聊天內容')
        ], last_ignore_space=True),
        Command('getcontext', getcontext, '現實當前聊天詳情', []),
        Command('list', list_all, '列出已登記藥物', []),
        Command('dumpall', dumpall, '打印所有 BOT 數據', [])
    ]

    logger.debug('Registering Commands...')
    for command in COMMANDS:
        logger.debug(f'  { command.name } - { command.description }')
        dispatcher.add_handler(CommandHandler(command.name, command.get_handler()))

    dispatcher.add_handler(REGISTER_CONVERSATION)

    jobqueue = updater.job_queue

    if (remindees := dispatcher.bot_data.get('remindees')):
        for remindee in map(Remindee.from_dict, remindees.values()):
            from datetime import datetime
            from pytz import timezone
            jobqueue.run_daily(generate_remind(remindee), time=timezone('Asia/Tokyo').localize(datetime(1970, 1, 1, 0, 0)))

    logger.info("Starting Polling...")
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
