from pyrogram import filters

from .. import bot, call, cdx
from ..modules.helpers import AdminsOnlyWrapper


@bot.on_message(cdx("end") & ~filters.private)
@AdminsOnlyWrapper
async def stop_vc_stream(client, message):
    try:
        await message.delete()
    except:
        pass
    chat_id = message.chat.id
    queued = call.queue.get(chat_id)
    if not queued:
        return await message.reply_text("**❌ Nothing Streaming.**")
    await call.close_stream(chat_id)
    return await message.reply_text("**❎ Streaming Stopped.**")




