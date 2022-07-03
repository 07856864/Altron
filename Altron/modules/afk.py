import time
from Altron import dispatcher
from Altron.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from Altron.helper_extra.mongo import db
from Altron.modules.sql import afk_sql as sql
from Altron.modules.users import get_user_id
from telegram import MessageEntity, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, MessageHandler, run_async

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


usersdb = db.users
async def is_afk1(user_id: int) -> bool:
    user = usersdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time


@run_async
def afk(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user

    if not user:  # ignore channels
        return

    if user.id in [777000, 1087968824]:
        return

    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text("{} ɪꜱ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ".format(fname))
    except BadRequest:
        pass


@run_async
def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    user_id = message.from_user.id
    reasondb = is_afk1(user_id)
    timeafk = reasondb["time"]
    seenago = get_readable_time((int(time.time() - timeafk)))

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            update.effective_message.reply_text(f"{firstname} ɪꜱ ʙᴀᴄᴋ ᴏɴʟɪɴᴇ\n\nʏᴏᴜ ᴡᴇʀᴇ ᴀᴡᴀʏ ꜰᴏʀ: `{seenago}`")
        except:
            return


@run_async
def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type != MessageEntity.MENTION:
                return

            user_id = get_user_id(message.text[ent.offset : ent.offset + ent.length])
            if not user_id:
                # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                return

            if user_id in chk_users:
                return
            chk_users.append(user_id)

            try:
                chat = bot.get_chat(user_id)
            except BadRequest:
                print("Error: Could not fetch userid {} for AFK module".format(user_id))
                return
            fst_name = chat.first_name

            check_afk(update, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, user_id, fst_name, userc_id)


def check_afk(update, user_id, fst_name, userc_id):
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        if int(userc_id) == int(user_id):
            return

        reasondb = is_afk1(user_id)
        timeafk = reasondb["time"]
        seenago = get_readable_time((int(time.time() - timeafk)))
        if not user.reason:
            res = f"{fst_name} ɪꜱ ᴀꜰᴋ\n\nʟᴀꜱᴛ ꜱᴇᴇɴ : `{seenago}`"
            update.effective_message.reply_text(res)
        else:
            res = f"{fst_name}  ɪꜱ ᴀꜰᴋ\nʀᴇᴀꜱᴏɴ : `{user.reason}`\n\nʟᴀꜱᴛ ꜱᴇᴇɴ : `{seenago}`"
            update.effective_message.reply_text(res)



AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"^(?i)brb(.*)$"), afk, friendly="afk"
)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_afk)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

__mod_name__ = "Aғᴋ"
__command_list__ = ["afk"]
__help__ = """
𝗔𝘄𝗮𝘆 𝗙𝗿𝗼𝗺 𝗞𝗲𝘆𝗯𝗼𝗮𝗿𝗱:
  ➲ /afk <Reason>: ꜰᴏʀ ᴀᴡᴀʏ ꜰʀᴏᴍ ᴋᴇʏʙᴏᴀʀᴅ ᴏʀ ᴜɴᴀᴠᴀɪʟᴀʙɪʟɪᴛʏ ᴏꜰ ᴜꜱᴇʀ
"""
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
