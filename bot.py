"""
Coded by @syedmahinislam
High-Performance Asynchronous Google Form Bulk Submitter Bot
"""

import asyncio
import logging
import random
import aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

# Coded by @syedmahinislam
TOKEN = "9270668766:AAF3d_DtG_LZHTO-rgJYKnWZHUcFXjqKFqQ"

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
        "🔗 Please send your Google Form <b>'viewform'</b> link:\n\n"
        "<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )


@dp.message(FormStates.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if "viewform" not in link:
        await message.answer("❌ Invalid link! Please send a valid Google Form <b>viewform</b> link.")
        return
    
    await state.update_data(form_link=link)
    await state.set_state(FormStates.waiting_for_count)
    await message.answer(
        "✅ Link received successfully!\n\n"
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
        f"• Status: Analyzing form fields...\n\n"
        f"<i>Coded by @syedmahinislam</i>",
        parse_mode="HTML"
    )
    await state.clear()

    # Background task for live progress updates
    asyncio.create_task(run_bulk_submitter(chat_id, status_msg.message_id, form_link, count))


async def run_bulk_submitter(chat_id: int, msg_id: int, form_link: str, total: int):
    post_url = form_link.replace("viewform", "formResponse")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(form_link, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    await bot.edit_message_text(
                        "❌ Failed to load Google Form. Please check the link.",
                        chat_id=chat_id, message_id=msg_id
                    )
                    return
                html = await resp.text()
        except Exception as e:
            await bot.edit_message_text(f"❌ Error: {str(e)}", chat_id=chat_id, message_id=msg_id)
            return

        soup = BeautifulSoup(html, "html.parser")
        entry_names = [tag["name"] for tag in soup.find_all(attrs={"name": True}) if tag["name"].startswith("entry.")]

        if not entry_names:
            await bot.edit_message_text("❌ No entry fields found in this form.", chat_id=chat_id, message_id=msg_id)
            return

        success = 0
        failed = 0
        chunk_size = 50  # Concurrent requests chunk size for high speed

        for i in range(0, total, chunk_size):
            current_batch = min(chunk_size, total - (success + failed))
            tasks = []

            for _ in range(current_batch):
                payload = {entry: random.choice(["Yes", "No", "Good", "Excellent", "1", "Test", "A", "B"]) for entry in entry_names}
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

            # Live update every batch
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

        # Final Success Message
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


async def main():
    print("Bot started successfully... Coded by @syedmahinislam")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
