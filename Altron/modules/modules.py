from Altron import dispatcher
from Altron.__main__ import (
    HELPABLE,
    IMPORTED,
)
from Altron.modules.helper_funcs.chat_status import sudo_plus
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, run_async


@run_async
@sudo_plus
def listmodules(update: Update, context: CallbackContext):
    message = update.effective_message
    module_list = []

    for helpable_module in HELPABLE:
        helpable_module_info = IMPORTED[helpable_module]
        file_info = IMPORTED[helpable_module_info.__mod_name__.lower()]
        file_name = file_info.__name__.rsplit("Altron.modules.", 1)[1]
        mod_name = file_info.__mod_name__
        module_list.append(f"- <code>{mod_name} ({file_name})</code>\n")
    module_list = "Following modules are loaded : \n\n" + "".join(module_list)
    message.reply_text(module_list, parse_mode=ParseMode.HTML)


LISTMODULES_HANDLER = CommandHandler("listmodules", listmodules)
dispatcher.add_handler(LISTMODULES_HANDLER)

__mod_name__ = "Modules"
