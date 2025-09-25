import aiofiles, aiohttp, base64, json, os, random, re, requests, yt_dlp

from .. import app, bot, call, cdz, console
from .thumbnail import create_thumbnail
from urllib.parse import urlparse
from io import BytesIO

from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream
from pytgcalls.types import AudioQuality, VideoQuality
from youtubesearchpython.__future__ import VideosSearch


def parse_query(query: str) -> str:
    if bool(re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/|live/)?([A-Za-z0-9_-]{11})(?:[?&].*)?$', query)):
        match = re.search(r'(?:v=|\/(?:embed|v|shorts|live)\/|youtu\.be\/)([A-Za-z0-9_-]{11})', query)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
        
    return query


def parse_tg_link(link: str):
    parsed = urlparse(link)
    path = parsed.path.strip('/')
    parts = path.split('/')
    
    if len(parts) >= 2:
        return str(parts[0]), int(parts[1])
        
    return None, None


async def fetch_song(query: str):
    url = "http://82.180.147.88:1470/song"
    params = {"query": query}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                try:
                    return await response.json()
                except Exception:
                    return {}
                
            return {}

def convert_to_seconds(duration: str) -> int:
    parts = list(map(int, duration.split(":")))
    total = 0
    multiplier = 1

    for value in reversed(parts):
        total += value * multiplier
        multiplier *= 60

    return total


def format_duration(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if sec > 0 or not parts:
        parts.append(f"{sec}s")

    return " ".join(parts)


@bot.on_message(cdz(["play", "vplay"]) & ~filters.private)
async def start_stream_in_vc(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    chat_id = message.chat.id
    mention = (
        message.from_user.mention
        if message.from_user else
        f"<a href=https://t.me/{bot.username}>ᴀɴᴏɴʏᴍᴏᴜꜱ ᴜꜱᴇʀ</a>"
    )
    replied = message.reply_to_message
    audio_telegram = replied.audio or replied.voice if replied else None
    video_telegram = replied.video or replied.document if replied else None
    
    if audio_telegram or video_telegram:
        try:
            aux = await message.reply_text("<b>🔄 Processing ✨...</b>")
        except Exception:
            pass
        if audio_telegram:
            id = audio_telegram.file_unique_id
            full_title = audio_telegram.title or audio_telegram.file_name
            try:
                file_name = (
                    audio_telegram.file_unique_id
                    + "."
                    + (
                        (audio_telegram.file_name.split(".")[-1])
                        if (not isinstance(audio_telegram, Voice))
                        else "ogg"
                    )
                )
            except:
                file_name = audio_telegram.file_unique_id + "." + "ogg"
            file_name = os.path.join(
                os.path.realpath("downloads"), file_name
            )
            duration_sec = audio_telegram.duration
            video_stream = False
        if video_telegram:
            id = video_telegram.file_unique_id
            full_title = video_telegram.title or video_telegram.file_name
            try:
                file_name = (
                    video_telegram.file_unique_id
                    + "."
                    + (video_telegram.file_name.split(".")[-1])
                )
            except:
                file_name = video_telegram.file_unique_id + "." + "mp4"
            file_name = os.path.join(
                os.path.realpath("downloads"), file_name
            )
            duration_sec = video_telegram.duration
            video_stream = True
        if not os.path.exists(file_name):
            try:
                try:
                    await aux.edit("📥")
                except Exception:
                    pass
                await replied.download(file_name=file_name)
            except Exception:
                try:
                    return await aux.edit("❌ Failed to download, please try again.")
                except Exception:
                    return
                    
            while not os.path.exists(file_name):
                await asyncio.sleep(0.5)
        
        file_path = file_name
        title = full_title[:25]
        duration_mins = format_duration(duration_sec)
        views = "None"
        image_path = "ERAVIBES/resource/thumbnail.png"
        channellink = (
            f"https://t.me/{message.chat.username}"
            if message.chat.username
            else "Telegram Channel"
        )
        channel = message.chat.title
        link = replied.link
        
    else:
        if len(message.command) < 2:
            return await message.reply_text(
                f"""
**🥀 𝐆ɪᴠᴇ 𝐌ᴇ  𝐒ᴏᴍᴇ 𝐐ᴜᴇʀʏ To
𝐏ʟᴀʏ 𝐀ᴜᴅɪᴏ 𝐕ɪᴅᴇᴏ❗...

ℹ️ 𝐄xᴀᴍᴘʟᴇs:
≽ 𝐀ᴜᴅɪᴏ: `/play siya ram`
≽ 𝐕ɪᴅᴇᴏ: `/vplay siya ram`**"""
            )
        query = parse_query(" ".join(message.command[1:]))
        try:
            aux = await message.reply_text("<b>🔄 Processing ✨...</b>")
        except Exception:
            pass
        video_stream = True if message.command[0].startswith("v") else False

        search = VideosSearch(query, limit=1)
        result = (await search.next())["result"]

        if not result:
            try:
                return await aux.edit("❌ No results found.")
            except Exception:
                return

        video = result[0]
        full_title = video["title"]
        title = full_title[:25]
        id = video["id"]
        duration = video["duration"]
        if not duration:
            try:
                return await aux.edit("❌ I can't stream live-stream right now.")
            except Exception:
                return
        duration_sec = convert_to_seconds(duration)
        duration_mins = format_duration(duration_sec)
        views = video["viewCount"]["short"]
        image_path = video["thumbnails"][0]["url"].split("?")[0]
        channellink = video["channel"]["link"]
        channel = video["channel"]["name"]
        link = video["link"]
        xyz = os.path.join("downloads", f"{id}.mp3")
        if not os.path.exists(xyz):
            song_data = await fetch_song(query)
            if not song_data:
                try:
                    return await aux.edit("❌ Failed to process query, please try again.")
                except Exception:
                    return
            song_url = song_data["link"]
            
            c_username, message_id = parse_tg_link(song_url)
            msg = await client.get_messages(c_username, message_id)
            try:
                try:
                    await aux.edit("📥")
                except Exception:
                    pass
                await msg.download(file_name=xyz)
            except Exception:
                try:
                    return await aux.edit("❌ Failed to download, please try again.")
                except Exception:
                    return
                    
            while not os.path.exists(xyz):
                await asyncio.sleep(0.5)
                
        file_path = xyz

    
    media_stream = (
        MediaStream(
            media_path=file_path,
            video_flags=MediaStream.Flags.IGNORE,
            audio_parameters=AudioQuality.STUDIO,
        )
        if not video_stream
        else MediaStream(
            media_path=file_path,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
        )
    )
    
    if chat_id not in call.queue:
        try:
            try:
                await call.start_stream(chat_id, media_stream)
            except NoActiveGroupCall:
                try:
                    return await aux.edit("❌ No active vc found to stream.")
                except Exception:
                    return
            except TelegramServerError:
                try:
                    return await aux.edit(
                        "⚠️**Telegram server error!**\nPlease try again shortly."
                    )
                except Exception:
                    return
        except Exception as e:
            try:
                return await aux.edit(
                    f"❌ **Failed to stream**❗\n\n`{e}`"
                )
            except Exception:
                return

    if 'duration' in locals():
        duration_str = duration
    else:
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes:02d}:{seconds:02d}"
    
    results = {
        "title": full_title,
        "id": id,
        "duration": duration_str,
        "views": views if views != "None" else "N/A",
        "channel": channel
    }
    
    user_id = message.from_user.id if message.from_user else bot.id
    thumbnail = await create_thumbnail(results["id"])
        
    try:
        await aux.delete()
    except:
        pass
        
    pos = await call.add_to_queue(chat_id, media_stream, title, duration_mins, thumbnail, mention)
    stream_type = "Audio" if not video_stream else "Video"
    status = (
        "✅ 𝐒ᴛᴀʀᴛᴇᴅ 𝐒ᴛʀᴇᴀᴍɪɴɢ"
        if pos == 0
        else f"✅ 𝐀ᴅᴅᴇᴅ 𝐐ᴜᴇᴜᴇ #{pos}"
    )
    caption = f"""
<blockquote><b>{status}</b></blockquote>
<blockquote><b>❍ Tɪᴛʟᴇ ➥ </b> <a href={link}>{title}</a>
<b>❍ Dᴜʀᴀᴛɪᴏɴ ➥ </b> {duration_mins}
<b>❍ Sᴛʀᴇᴀᴍ Tʏᴘᴇ ➥ </b> {stream_type}
<b>❍ ʙʏ ➥ </b> {mention}</blockquote> 
"""
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("❖ ᴛᴧᴘ тᴏ sᴇᴇ ᴍᴧɪᴄ ❖", url=f"https://t.me/{bot.me.username}?startgroup=true")],
        [
            InlineKeyboardButton("˹ ᴜᴘᴅᴧᴛᴇ ˼", url="https://t.me/net_pro_max"),
            InlineKeyboardButton("˹ sᴜᴘᴘᴏꝛᴛ ˼", url="https://t.me/+ifTJa6EmP4A1MTA9")
        ],
        [InlineKeyboardButton("〆 ᴄʟᴏsᴇ 〆", callback_data="force_close")]
    ])
    try:
        await message.reply_photo(photo=thumbnail, caption=caption, has_spoiler=False, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        pass

    if chat_id != console.LOG_GROUP_ID:
        try:
            chat_name = message.chat.title
            if message.chat.username:
                chat_link = f"@{message.chat.username}"
            elif chat_id in console.chat_links:
                clink = console.chat_links[chat_id]
                chat_link = f"[Private Chat]({clink})"
            else:
                try:
                    new_link = await client.export_chat_invite_link(chat_id)
                    console.chat_links[chat_id] = new_link
                    chat_link = f"[Private Chat]({new_link})"
                except Exception:
                    chat_link = "N/A"
        

            if message.from_user:
                if message.from_user.username:
                    req_user = f"@{message.from_user.username}"
                else:
                    req_user = message.from_user.mention
                user_id = message.from_user.id
            elif message.sender_chat:
                if message.sender_chat.username:
                    req_user = f"@{message.sender_chat.username}"
                else:
                    req_user = message.sender_chat.title
                user_id = message.sender_chat.id
            else:
                req_user = "Anonymous User"
                user_id = "N/A"

            log_message = f"""
**❖ {mention} ɪꜱ ᴘʟᴀʏ ʟᴏɢ ❖**

**● ᴄʜᴀᴛ ɪᴅ ➥** `{chat_id}`
**● ᴄʜᴀᴛ ɴᴀᴍᴇ ➥** {chat_name}
**● ᴄʜᴀᴛ ʟɪɴᴋ ➥** {chat_link}

**● ᴜsᴇʀ ɪᴅ ➥** `{user_id}`
**● ɴᴀᴍᴇ ➥** {req_user}

**● ǫᴜᴇʀʏ ➥** {query}
**● ᴛɪᴛʟᴇ ➥** [{title}]({link})
**● ᴅᴜʀᴀᴛɪᴏɴ ➥** {duration_mins}
**● sᴛʀᴇᴀᴍᴛʏᴘᴇ ➥** {stream_type}
"""
            await bot.send_message(console.LOG_GROUP_ID, text=log_message, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʏᴛ ʟɪɴᴋ", url=link)]]))
        except Exception as e:
            print(f"Error sending log message: {e}")
            pass

