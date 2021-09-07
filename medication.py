from enum import IntEnum, auto
from reminder import Medication, Remindee, append_remindee, get_remindee, update_medications

from telegram import Update, user
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler
)

from utils.command_util import Command, Parameter, reply, NEWLINE

# Registration
class States(IntEnum):
    NEW_USER = auto()
    MEDICATION = auto()

def register(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    
    if update.effective_chat.type in ['group', 'supergroup'] and not update.effective_user.username:
        reply(
            update, context,
            f'因爲您未設置 Telegram 用戶名（username），所以無法在羣裏進行提醒！請您設置用戶名，或者私聊我來設置提醒。'
        )

    if (remindee := get_remindee(user_id, context)):
        reply(
            update, context,
            f'{remindee.nickname}，歡迎回來！{render_medication_list(remindee.medications)}{NEWLINE}'
            f'請使用 /add 來登記新的藥物，/del 來刪除既有的藥物，格式如下：（若想取消操作請使用 /cancel）'
        )
        context.user_data['new_medications'] = remindee.to_dict()['medications']
        ADD_COMMAND.print_usage(update)
        DEL_COMMAND.print_usage(update)
        return States.MEDICATION
    else:
        reply(
            update, context,
            f"您好呀～請問我應該怎麼稱呼您呀？（比如「{update.effective_user.full_name}樣」）"
        )
        return States.NEW_USER

def new_user(update: Update, context: CallbackContext) -> int:
    nickname = update.effective_message.text
    remindee = Remindee(nickname, [], update.effective_chat.id, update.effective_user.username)
    append_remindee(update.effective_user.id, remindee, context)
    context.user_data['new_medications'] = []
    reply(
        update, context,
        f'{nickname}，歡迎使用我！請在下面使用 /add 來登記藥物，格式如下：'
    )
    ADD_COMMAND.print_usage(update)
    return States.MEDICATION

def add_medication(update: Update, context: CallbackContext, command: Command, args: list) -> int:
    if not context.user_data.get('new_medications'):
        context.user_data['new_medications'] = []
    name = args['name']
    amount = args['amount']
    context.user_data['new_medications'].append(Medication(name, amount).to_dict())        
    reply(
        update, context,
        f"添加 {name} {amount} 成功！使用 /end 指令以結束輸入"
    )
    return States.MEDICATION

def del_medication(update: Update, context: CallbackContext, command: Command, args: list) -> int:
    if not context.user_data.get('new_medications'):
        context.user_data['new_medications'] = []
        return States.MEDICATION

    index: int = args['index']
    try:
        deleted = Medication.from_dict(context.user_data['new_medications'].pop(index - 1))
    except KeyError:
        reply(
            update, context,
            f'序號不合法！'
        )
        return States.MEDICATION

    reply(
        update, context,
        f"刪除 {deleted} 成功！使用 /end 指令以結束輸入"
    )
    return States.MEDICATION

def end_medication(update: Update, context: CallbackContext) -> None:
    if not (new_medications := context.user_data.get('new_medications')):
        reply(
            update, context,
            f'未添加任何新藥物！'
        )
        return ConversationHandler.END
    remindee = update_medications(update.effective_user.id, list(map(Medication.from_dict, new_medications)), context)
    reply(
        update, context,
        f'更新成功！{render_medication_list(remindee.medications)}'
    )
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    reply(
        update, context,
        f'操作已取消。'
    )
    return ConversationHandler.END

ADD_COMMAND = Command('add', add_medication, '添加藥物', [
                Parameter('name', str, '藥物名稱'),
                Parameter('amount', str, '藥物的量')    
            ])
DEL_COMMAND = Command('del', del_medication, '刪除藥物', [
                Parameter('index', int, '藥物序號')
            ])

REGISTER_CONVERSATION = ConversationHandler(
    entry_points=[
        CommandHandler('register', register)
    ],
    states={
        States.NEW_USER: [MessageHandler(Filters.regex('[^ @/]+'), new_user)],
        States.MEDICATION: [
            CommandHandler('add', ADD_COMMAND.get_handler()),
            CommandHandler('del', DEL_COMMAND.get_handler()),
            CommandHandler('end', end_medication)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel)
    ]
)

def render_medication_list(medications: list[Medication]) -> str:
    if not medications:
        return '您沒有任何藥物登記在冊，請使用 /register 指令登記！'
    else:
        medication_list = '\n'.join(f'{i + 1:>3}  <b>{medication.name}</b> {medication.amount}' for i, medication in enumerate(medications))
        return f'您現在擁有以下藥物登記在冊：{NEWLINE}{NEWLINE}{medication_list}'

def list_all(update: Update, context: CallbackContext, command: Command, args: list) -> None:
    if (remindee := get_remindee(update.effective_user.id, context)):
        reply(
            update, context,
            text=render_medication_list(remindee.medications)
        )
    else:
        reply(
            update, context,
            text="初次使用，請使用 /register 指令登記！"
        )
