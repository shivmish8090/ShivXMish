from .. import bot, rgx


@bot.on_callback_query(rgx("close"))
async def close(client, query):
    try:
        await query.message.delete()
    except Exception:
        pass
