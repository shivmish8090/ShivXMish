from .. import bot, console
from ..modules.database import add_served_chat

from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated


@bot.on_chat_member_updated()
async def bot_added_to_group(client, event: ChatMemberUpdated):
    chat_id = event.chat.id
    
    if event.new_chat_member and event.new_chat_member.user.id == bot.id:
        await add_served_chat(chat_id)
        
    if event.chat.username:
        chat_link = f"https://t.me/{event.chat.username}"
        console.chat_links[chat_id] = chat_link
    else:
        try:
            chat_link = await bot.export_chat_invite_link(chat_id)
            console.chat_links[chat_id] = chat_link
        except Exception:
            pass

    if event.chat.id not in console.chat_admins:
        console.chat_admins[chat_id] = {}
    try:
        owners = filters.user()
        admins =  filters.user()
        async for m in client.get_chat_members(
            chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
        ):
            if m.status == enums.ChatMemberStatus.OWNER:
                if m.user.id not in owners:
                    owners.add(m.user.id)
            if m.user.id not in admins:
                admins.add(m.user.id)
        
        console.chat_admins[chat_id]["owners"] = owners
        console.chat_admins[chat_id]["admins"] = admins
    except Exception as e:
        pass
        
