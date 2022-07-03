from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, run_async

import Altron.modules.sql.approve_sql as sql
from Altron import DRAGONS, dispatcher
from Altron.modules.disable import DisableAbleCommandHandler
from Altron.modules.helper_funcs.chat_status import user_admin
from Altron.modules.helper_funcs.extraction import extract_user
from Altron.modules.log_channel import loggable


@loggable
@user_admin
@run_async
def approve(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return
    if member.status == "administrator" or member.status == "creator":
        message.reply_text(
            "User is already admin - locks, blocklists, and antiflood already don't apply to them."
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) is already approved in {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.approve(message.chat_id, user_id)
    message.reply_text(
        f"✅ 𝐀ᴘᴘʀᴏᴠᴇᴅ ᴜsᴇʀ ɪɴ **{chat_title}**\n𝐔sᴇʀ: [{member.user['first_name']}](tg://user?id={member.user['id']})\n\nThey will now be ignored by automated admin actions like locks, blocklists, and antiflood.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return


@loggable
@user_admin
@run_async
def disapprove(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text("This user is an admin, they can't be unapproved.")
        return ""
    if not sql.is_approved(message.chat_id, user_id):
        message.reply_text(f"{member.user['first_name']} isn't approved yet!")
        return ""
    sql.disapprove(message.chat_id, user_id)
    message.reply_text(
        f"❌ 𝐔ɴ-𝐀ᴘᴘʀᴏᴠᴇᴅ ᴜsᴇʀ ɪɴ {chat_title}\n𝐔sᴇʀ: {member.user['first_name']}"
    )
    return


@user_admin
@run_async
def approved(update):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "𝐓ʜᴇ ғᴏʟʟᴏᴡɪɴɢ ᴜsᴇʀs ᴀʀᴇ ᴀᴘᴘʀᴏᴠᴇᴅ.\n\n"
    approved_users = sql.list_approved(message.chat_id)
    for i in approved_users:
        member = chat.get_member(int(i.user_id))
        msg += f"➤ {member.user['first_name']} : `{i.user_id}`\n"
    if msg.endswith("approved.\n"):
        message.reply_text(f"No users are approved in {chat_title}.")
        return
    else:
        message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@user_admin
@run_async
def approval(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = chat.get_member(int(user_id))
    if not user_id:
        message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"𝐔sᴇʀ: {member.user['first_name']}\n𝐀ᴘᴘʀᴏᴠᴀʟ: ✅"
        )
    else:
        message.reply_text(
            f"𝐔sᴇʀ: {member.user['first_name']}\n𝐀ᴘᴘʀᴏᴠᴀʟ: ❌"
        )


@run_async
def unapproveall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in DRAGONS:
        update.effective_message.reply_text(
            "Only the chat owner can unapprove all users at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⚠️ Confirm", callback_data="unapproveall_user"
                    ),
                    InlineKeyboardButton(
                        text="❌ Cancel", callback_data="unapproveall_cancel"
                    )
                ]
            ]
        )
        update.effective_message.reply_text(
            f"Are you sure you would like to unapprove ALL users in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@run_async
def unapproveall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "unapproveall_user":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            approved_users = sql.list_approved(chat.id)
            users = [int(i.user_id) for i in approved_users]
            for user_id in users:
                sql.disapprove(chat.id, user_id)

        if member.status == "administrator":
            query.answer("Only owner of the chat can do this.")

        if member.status == "member":
            query.answer("You need to be admin to do this.")
    elif query.data == "unapproveall_cancel":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            message.edit_text("Removing of all approved users has been cancelled.")
            return ""
        if member.status == "administrator":
            query.answer("Only owner of the chat can do this.")
        if member.status == "member":
            query.answer("You need to be admin to do this.")


__help__ = """
𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:
  ➲ /approval: ᴄʜᴇᴄᴋ ᴀ ᴜꜱᴇʀ'ꜱ ᴀᴘᴘʀᴏᴠᴀʟ ꜱᴛᴀᴛᴜꜱ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ.
  ➲ /approve: ᴀᴘᴘʀᴏᴠᴇ ᴏꜰ ᴀ ᴜꜱᴇʀ. ʟᴏᴄᴋꜱ, ʙʟᴀᴄᴋʟɪꜱᴛꜱ, ᴀɴᴅ ᴀɴᴛɪꜰʟᴏᴏᴅ ᴡᴏɴ'ᴛ ᴀᴘᴘʟʏ ᴛᴏ ᴛʜᴇᴍ ᴀɴʏᴍᴏʀᴇ.
  ➲ /unapprove: ᴜɴᴀᴘᴘʀᴏᴠᴇ ᴏꜰ ᴀ ᴜꜱᴇʀ. ᴛʜᴇʏ ᴡɪʟʟ ɴᴏᴡ ʙᴇ ꜱᴜʙᴊᴇᴄᴛ ᴛᴏ ʟᴏᴄᴋꜱ, ʙʟᴀᴄᴋʟɪꜱᴛꜱ, ᴀɴᴅ ᴀɴᴛɪꜰʟᴏᴏᴅ ᴀɢᴀɪɴ.
  ➲ /approved: ʟɪꜱᴛ ᴀʟʟ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ.
  ➲ /unapproveall: ᴜɴᴀᴘᴘʀᴏᴠᴇ ᴀʟʟ ᴜꜱᴇʀꜱ ɪɴ ᴀ ᴄʜᴀᴛ. ᴛʜɪꜱ ᴄᴀɴɴᴏᴛ ʙᴇ ᴜɴᴅᴏɴᴇ.
"""

APPROVE = DisableAbleCommandHandler("approve", approve)
DISAPPROVE = DisableAbleCommandHandler("unapprove", disapprove)
APPROVED = DisableAbleCommandHandler("approved", approved)
APPROVAL = DisableAbleCommandHandler("approval", approval)
UNAPPROVEALL = DisableAbleCommandHandler("unapproveall", unapproveall)
UNAPPROVEALL_BTN = CallbackQueryHandler(unapproveall_btn, pattern=r"unapproveall_.*")

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(APPROVED)
dispatcher.add_handler(APPROVAL)
dispatcher.add_handler(UNAPPROVEALL)
dispatcher.add_handler(UNAPPROVEALL_BTN)

__mod_name__ = "Aᴘᴘʀᴏᴠᴇ"
__handlers__ = [APPROVE, DISAPPROVE, APPROVED, APPROVAL]
