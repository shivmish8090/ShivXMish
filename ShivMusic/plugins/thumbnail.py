#
# Copyright (C) 2024 by MISH0009@Github, < https://github.com/MISH0009 >.
#
# This file is part of < https://github.com/MISH0009/DNS > project,
# and is released under the MIT License.
# Please see < https://github.com/MISH0009/DNS/blob/master/LICENSE >
#
# All rights reserved.



import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from youtubesearchpython.__future__ import VideosSearch

title_font = ImageFont.truetype("assets/font3.ttf", 35)
channel_font = ImageFont.truetype("assets/font2.ttf", 25)
duration_font = ImageFont.truetype("assets/font.ttf", 23)
watermark_font = ImageFont.truetype("assets/font.ttf", 20)

async def generate_simple_thumb(videoid, filename):
    if os.path.isfile(filename):
        return filename

    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    result = (await results.next())["result"][0]

    title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
    channel = result.get("channel", {}).get("name", "Unknown Channel")
    duration = result.get("duration", "0:00")
    views = result.get("viewCount", {}).get("text", "0 views")
    thumbnail_url = result["thumbnails"][0]["url"].split("?")[0]

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"cache/thumb_{videoid}.jpg", "wb") as f:
                    await f.write(await resp.read())

    try:
        base = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((1280, 720))
        background = base.filter(ImageFilter.GaussianBlur(radius=8))
        draw = ImageDraw.Draw(background)

        
        rect_width = 800
        rect_height = 700
        cx = (1280 - rect_width) // 2
        cy = (720 - rect_height) // 2

        control_img = Image.open("assets/cntrol.png").convert("RGBA").resize((rect_width, rect_height))
        background.paste(control_img, (cx, cy), control_img)

        song_thumb = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((180, 150))
        thumb_x = cx + (rect_width - 550) // 2
        thumb_y = cy + 150
        background.paste(song_thumb, (thumb_x, thumb_y), song_thumb)

        max_chars = 20
        title_words = title.split()
        short_title = ""
        total_chars = 0

        for word in title_words:
            if total_chars + len(word) + (1 if short_title else 0) <= max_chars:
                short_title += (" " if short_title else "") + word
                total_chars += len(word) + (1 if short_title else 0)
            else:
                break

        short_title = short_title.strip()
        if short_title != title:
            short_title += "....."

        draw.text((570, 160), f"{short_title}", font=title_font, fill="white")
        draw.text((570, 220), f"{channel}", font=channel_font, fill="white")
        draw.text((890, 365), f"{duration}", font=duration_font, fill="white")
        draw.text((570, 255), f"{views}", font=duration_font, fill="white")
        draw.text((590, 112), "", font=watermark_font, fill="white")

        background.save(filename)
        return filename

    except Exception as e:
        print(f"Error loading images: {e}")
        return None

async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
