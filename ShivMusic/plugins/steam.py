import aiofiles, aiohttp, base64, json, os, random, re, requests, asyncio

from .. import app, bot, call, cdz, console
from urllib.parse import urlparse
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream
from pytgcalls.types import AudioQuality, VideoQuality
from youtubesearchpython.__future__ import VideosSearch


def parse_query(query: str) -> str:
    if bool(
        re.match(
            r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/|live/)?([A-Za-z0-9_-]{11})(?:[?&].*)?$",
            query,
        )
    ):
        match = re.search(
            r"(?:v=|\/(?:embed|v|shorts|live)\/|youtu\.be\/)([A-Za-z0-9_-]{11})", query
        )
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"

    return query


def parse_tg_link(link: str):
    parsed = urlparse(link)
    path = parsed.path.strip("/")
    parts = path.split("/")

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


def seconds_to_hhmmss(seconds):
    if seconds < 3600:
        minutes = seconds // 60
        sec = seconds % 60
        return f"{minutes:02}:{sec:02}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        sec = seconds % 60
        return f"{hours:d}:{minutes:02}:{sec:02}"



async def make_thumbnail(image, title, channel, duration, output):
    return await create_music_thumbnail(image, title, channel, duration, output)


@bot.on_message(cdz(["play", "vplay"]) & ~filters.private)
async def start_stream_in_vc(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    chat_id = message.chat.id
    mention = (
        message.from_user.mention
        if message.from_user
        else f"[Anonymous User](https://t.me/{bot.username})"
    )
    replied = message.reply_to_message
    audio_telegram = replied.audio or replied.voice if replied else None
    video_telegram = replied.video or replied.document if replied else None

    if audio_telegram or video_telegram:
        return await message.reply_text(
            "**🥺 Sorry, I Can't Stream Telegram Media Files Right Now.**"
        )
    else:
        if len(message.command) < 2:
            return await message.reply_text(
                """
**🥀 Give Me Some Query To
Stream Audio Or Video❗...

ℹ️ Example:
≽ Audio: `/play yalgaar`
≽ Video: `/vplay yalgaar`**"""
            )
        query = parse_query(" ".join(message.command[1:]))
        try:
            aux = await message.reply_text("**🔄 Processing ✨...**")
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
        title = full_title[:30]
        id = video["id"]
        duration = video["duration"]
        if not duration:
            try:
                return await aux.edit("❌ I can't stream live-stream right now.")
            except Exception:
                return
        duration_sec = convert_to_seconds(duration)
        duration_mins = format_duration(duration_sec)
        image_path = video["thumbnails"][0]["url"].split("?")[0]
        channel = video["channel"]["name"]
        link = video["link"]
        xyz = os.path.join("downloads", f"{id}.mp3")
        if not os.path.exists(xyz):
            song_data = await fetch_song(id)
            if not song_data:
                try:
                    return await aux.edit(
                        "❌ Failed to process query, please try again."
                    )
                except Exception:
                    return
            song_url = song_data["link"]

            c_username, message_id = parse_tg_link(song_url)
            msg = await client.get_messages(c_username, message_id)
            try:
                try:
                    await aux.edit("**⬇️ Downloading ✨...**")
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
                return await aux.edit(f"❌ **Failed to stream**❗\n\n`{e}`")
            except Exception:
                return

    image_file = await generate_thumbnail(image_path)
    thumbnail = await make_thumbnail(
        image_file,
        full_title,
        channel,
        duration_sec,
        f"cache/{chat_id}_{id}_{message.id}.png",
    )

    try:
        await aux.delete()
    except Exception:
        pass

    pos = await call.add_to_queue(
        chat_id, media_stream, title, duration_mins, thumbnail, mention
    )
    status = (
        "✅ **Started Streaming in VC.**"
        if pos == 0
        else f"✅ **Added To Queue At: #{pos}**"
    )
    caption = f"""
{status}

**❍ Title:** [{title}...]({link})
**❍ Duration:** {duration_mins}
**❍ Requested By:** {mention}"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🗑️ Close",
                    callback_data="close",
                ),
            ]
        ]
    )
    try:
        await message.reply_photo(
            photo=thumbnail, caption=caption, has_spoiler=True, reply_markup=buttons
        )
    except Exception:
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

            stream_type = "Audio" if not video_stream else "Video"

            log_message = f"""
🎉 **{mention} Just Played A Song.**

📍 **Chat:** {chat_name}
💬 **Chat Link:** {chat_link}
♂️ **Chat ID:** {chat_id}
👤 **Requested By:** {req_user}
🆔 **User ID:** `{user_id}`
🔎 **Query:** {query}
🎶 **Title:** [{title}...]({link})
⏱️ **Duration:** {duration_mins}
📡 **Stream Type:** {stream_type}"""
            await bot.send_photo(
                console.LOG_GROUP_ID, photo=thumbnail, caption=log_message
            )
        except Exception:
            pass

