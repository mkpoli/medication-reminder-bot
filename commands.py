import logging
logger = logging.getLogger(__name__)

from __environ__ import PRODUCTION_MODE
from utils.command_util import Command, Parameter, reply
# from kana_convert import convert
from telegram import Update
from telegram.ext import CallbackContext
from typing import Any, Sequence
from calc_date import evaluate

# from pyparsing import 
def calc_time(update: Update, context: CallbackContext, command: Command, args: Sequence[Any]) -> None:
    result = evaluate(args['equation'])
    print(result)
    reply(
        update, context,
        str(result)
    )

def say(update: Update, context: CallbackContext, command: Command, args: Sequence[Any]) -> None:
    context.bot.send_message(text=args['content'], chat_id=args['chat_id'])

def getcontext(update: Update, context: CallbackContext, command: Command, args: Sequence[Any]) -> None:
    reply(
        update, context,
        str(update.effective_chat.id)
    )

def generate_version(version: str):
    def version_command(update: Update, context: CallbackContext, command: Command, args: Sequence[Any]) -> None:
        logger.debug('Asking Version, replying')
        reply(
            update, context,
            f"<pre>v{ version } { '[dev]' if not PRODUCTION_MODE else '' }</pre>",
        )
    return version_command
