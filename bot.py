"""
Coded by @syedmahinislam
High-Performance Asynchronous Google Form Bulk Submitter Bot
"""

import asyncio
import logging
import random
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

# Coded by @syedmahinislam
TOKEN = "9270668766:AAGXcC5PMLexQc5QuLWKUkZaM-nODWWEUaw"

bot = Bot(token=TOKEN)
dp = Dispatcher()


class FormStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_count = State()


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Welcome to Fast Form Submitter Bot!\n\n"
        "Send `/t` command to start form automation.\n\n"
        "<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )


@dp.message(Command("t"))
async def cmd_t(message: Message, state: FSMContext):
    await state.set_state(FormStates.waiting_for_link)
    await message.answer(
        "🔗 Please send your Google Form <b>'forms.gle'</b> or <b>'viewform'</b> link:\n\n"
        "<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )


@dp.message(FormStates.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    link = message.text.strip()
    
    # Handle short links or viewform conversion
    if "forms.gle" in link:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link, allow_redirects=True, timeout=10) as resp:
                    link = str(resp.url)
        except Exception:
            pass

    if "viewform" in link:
        link = link.replace("viewform", "formResponse")
    elif "formResponse" not in link:
        link = link.split("?")[0] + "/formResponse"

    await state.update_data(form_link=link)
    await state.set_state(FormStates.waiting_for_count)
    await message.answer(
        f"✅ Link received and configured successfully!\n`{link}`\n\n"
        "🔢 Now, enter the total number of responses you want to generate (e.g., 1000, 2000):\n\n"
        "<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )


@dp.message(FormStates.waiting_for_count)
async def process_count(message: Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number (e.g., 1000):")
        return

    data = await state.get_data()
    form_link = data.get("form_link")
    chat_id = message.chat.id

    status_msg = await message.answer(
        f"🚀 Initializing high-speed bulk submission...\n"
        f"• Target: <b>{count}</b> responses\n"
        f"• Status: Starting direct payload delivery...\n\n"
        f"<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )
    await state.clear()

    asyncio.create_task(run_bulk_submitter(chat_id, status_msg.message_id, form_link, count))


async def run_bulk_submitter(chat_id: int, msg_id: int, post_url: str, total: int):
    # Apnar form er field entry IDs ebong possible options gulo ekhane define kora holo
    form_data_mapping = {
        "entry.1291578592": ["Bashay", "Tor nanir heday"],
        "entry.394595566": ["10-20", "20-30", "30-40", "40+"],
        "entry.1848189587": ["Madarchod", "Bainchod", "Khankir pola"]
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with aiohttp.ClientSession() as session:
        success = 0
        failed = 0
        chunk_size = 50  # Concurrent batch size for blazing fast speed

        for i in range(0, total, chunk_size):
            current_batch = min(chunk_size, total - (success + failed))
            tasks = []

            for _ in range(current_batch):
                payload = {entry: random.choice(options) for entry, options in form_data_mapping.items()}
                tasks.append(send_request(session, post_url, payload, headers))

            results = await asyncio.gather(*tasks)
            for res in results:
                if res:
                    success += 1
                else:
                    failed += 1

            completed = success + failed
            percent = (completed / total) * 100
            remaining = total - completed

            try:
                await bot.edit_message_text(
                    f"🚀 <b>Bulk Submission in Progress...</b>\n\n"
                    f"• Target: <b>{total}</b>\n"
                    f"• Sent: <b>{completed} / {total}</b>\n"
                    f"• Remaining: <b>{remaining}</b>\n"
                    f"• Progress: <b>{percent:.1f}%</b> ⏳\n\n"
                    f"<i>Coded by @syedmahinislam</i>",
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML"
                )
            except Exception:
                pass

        await bot.edit_message_text(
            f"📊 <b>Bulk Submission Complete!</b>\n\n"
            f"• Target: <b>{total}</b>\n"
            f"• Successful: <b>{success}</b>\n"
            f"• Failed: <b>{failed}</b>\n"
            f"• Progress: <b>100%</b> ✅\n\n"
            f"<i>Coded by @syedmahinislam</i>",
            chat_id=chat_id,
            message_id=msg_id,
            parse_mode="HTML"
        )


async def send_request(session, url, payload, headers):
    try:
        async with session.post(url, data=payload, headers=headers, timeout=10) as response:
            return response.status in [200, 302]
    except Exception:
        return False


# Dummy Web Server for Render Port Binding
async def handle_ping(request):
    return web.Response(text="Bot is running successfully! Coded by @syedmahinislam")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    print("Bot starting... Coded by @syedmahinislam")
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
