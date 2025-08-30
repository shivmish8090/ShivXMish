from pyrogram import filters

from .. import bot, call, cdx
from ..modules.helpers import AdminsOnlyWrapper


@bot.on_message(cdx("pause") & ~filters.private)
@AdminsOnlyWrapper
async def pause_vc_stream(client, message):
    chat_id = message.chat.id
    queued = call.queue.get(chat_id)
    if not queued:
        return await message.reply_text("**❌ Nothing Streaming.**")
    is_stream = await call.is_stream_off(chat_id)
    if is_stream:
        return await message.reply_text("**✅ Stream already Paused.**")
    try:
        await call.pause_stream(chat_id)
    except Exception:
        return await message.reply_text("**❌ Failed to pause stream❗**")
    await call.stream_off(chat_id)
    return await message.reply_text("**✅ Stream now Paused.**")




