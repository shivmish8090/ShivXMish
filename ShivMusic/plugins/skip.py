from pyrogram import filters

from .. import bot, call, cdx
from ..modules.helpers import AdminsOnlyWrapper


@bot.on_message(cdx("skip") & ~filters.private)
@AdminsOnlyWrapper
async def skip_vc_stream(client, message):
    chat_id = message.chat.id
    queued = call.queue.get(chat_id)
    if not queued:
        return await message.reply_text("**❌ Nothing streaming❗**")
    return await call.change_stream(chat_id)







