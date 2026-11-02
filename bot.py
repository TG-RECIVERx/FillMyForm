"""
Coded by @syedmahinislam
High-Performance Asynchronous Google Form Bulk Submitter Bot (Auto Dynamic Parser)
"""

import asyncio
import logging
import random
import os
import re
import aiohttp
from aiohttp import web
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

# Coded by @syedmahinislam
TOKEN = "9270668766:AAFWBC93VvWyYBKBBnksbxsLQU4XQMEDYGc"

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
        "🔗 Please send your Google Form link (e.g., `forms.gle` or `viewform` link):\n\n"
        "<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )


@dp.message(FormStates.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    link = message.text.strip()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Resolve forms.gle short links
    if "forms.gle" in link:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link, headers=headers, allow_redirects=True, timeout=10) as resp:
                    link = str(resp.url)
        except Exception:
            pass

    if "viewform" not in link:
        link = link.split("?")[0] + "/viewform"

    await state.update_data(form_link=link)
    await state.set_state(FormStates.waiting_for_count)
    await message.answer(
        f"✅ Link resolved successfully!\n`{link}`\n\n"
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
        f"• Status: Automatically analyzing form fields...\n\n"
        f"<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )
    await state.clear()

    asyncio.create_task(run_bulk_submitter(chat_id, status_msg.message_id, form_link, count))


async def run_bulk_submitter(chat_id: int, msg_id: int, form_link: str, total: int):
    post_url = form_link.replace("viewform", "formResponse")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(form_link, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    await bot.edit_message_text(
                        "❌ Failed to load Google Form. Please check if the link is public.",
                        chat_id=chat_id, message_id=msg_id
                    )
                    return
                html = await resp.text()
        except Exception as e:
            await bot.edit_message_text(f"❌ Error connecting to form: {str(e)}", chat_id=chat_id, message_id=msg_id)
            return

        # Dynamic Extraction of Entry IDs and options from form HTML
        soup = BeautifulSoup(html, "html.parser")
        form_data_mapping = {}

        # Find all inputs or radio options with entry names
        for tag in soup.find_all(attrs={"name": True}):
            name = tag["name"]
            if name.startswith("entry."):
                if name not in form_data_mapping:
                    form_data_mapping[name] = []
                val = tag.get("data-value") or tag.get("value")
                if val and val not in form_data_mapping[name] and val != "__other_option__":
                    form_data_mapping[name].append(val)

        # Fallback if no options extracted via data-value
        for entry in form_data_mapping:
            if not form_data_mapping[entry]:
                form_data_mapping[entry] = ["Yes", "No", "Test Value", "A", "B", "1"]

        if not form_data_mapping:
            await bot.edit_message_text("❌ No entry fields found automatically. Please check the link.", chat_id=chat_id, message_id=msg_id)
            return

        success = 0
        failed = 0
        chunk_size = 50  # High-speed batch processing

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
