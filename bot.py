import asyncio
import logging
import random
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, Message

TOKEN = "9270668766:AAF3d_DtG_LZHTO-rgJYKnWZHUcFXjqKFqQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()


class FormAutomationStates(StatesGroup):
  waiting_for_link = State()
  waiting_for_count = State()


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "As-salamu alaikum! Direct Form Submitter Bot ready ache. `/t` command"
      " diye shuru korun."
  )


@dp.message(Command("t"))
async def cmd_t(message: Message, state: FSMContext):
  await state.set_state(FormAutomationStates.waiting_for_link)
  await message.answer(
      "🔗 Doya kore apnar Google Form er link-ti (jemon `.../viewform` ba"
      " `.../formResponse`) ekhane din:"
  )


@dp.message(FormAutomationStates.waiting_for_link)
async def process_form_link(message: Message, state: FSMContext):
  form_link = message.text.strip()
  await state.update_data(form_link=form_link)
  await state.set_state(FormAutomationStates.waiting_for_count)
  await message.answer(
      f"✅ Link sothikvabe pawa gese!\n`{form_link}`\n\nEkhon apni eksathe"
      " total koyti responses pathate chan? (Jemon: 500, 1000 ba 2000)"
  )


@dp.message(FormAutomationStates.waiting_for_count)
async def process_response_count(message: Message, state: FSMContext):
  try:
    total_count = int(message.text.strip())
  except ValueError:
    await message.answer("❌ Doya kore ekti valid number din (jemon: 1000):")
    return

  data = await state.get_data()
  form_link = data.get("form_link")
  chat_id = message.chat.id

  await message.answer(
      f"🚀 Fast Automation start hocche!\n• Target: `{total_count}` responses\n⏳"
      " Background-e request pathano hocche, shesh hole notification paben..."
  )
  await state.clear()

  # Background task run kora
  asyncio.create_task(send_bulk_form_requests(chat_id, form_link, total_count))


async def send_bulk_form_requests(chat_id: int, form_link: string, total_count: int):
  success_count = 0
  failed_count = 0

  # Viewform URL ke formResponse URL-e convert kora
  if "viewform" in form_link:
    post_url = form_link.replace("viewform", "formResponse")
  else:
    post_url = form_link

  # Example dummy payload entries (Apnar form er entry id gulo ekhane thakbe)
  # Jemon: "entry.12345678": "Mahin"
  
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  for i in range(total_count):
    try:
      # Ekhane apnar form er field data pass korte parben
      payload = {
          # "entry.XXXXX": "Sample Answer"
      }
      
      response = requests.post(post_url, data=payload, headers=headers, timeout=10)
      if response.status_code == 200 or response.status_code == 302:
        success_count += 1
      else:
        failed_count += 1
    except Exception as e:
      failed_count += 1

    # Chotto ekta sleep rakhte paren jate server block na kore
    await asyncio.sleep(0.1)

  # Final notification
  await bot.send_message(
      chat_id,
      f"📊 **Bulk Submission Complete!**\n\n"
      f"• Target: {total_count}\n"
      f"• Successful: {success_count}\n"
      f"• Failed: {failed_count}\n\n"
      f"✅ Sob kaj sesh bhai!",
  )


async def main():
  await bot.set_my_commands([
      BotCommand(command="start", description="Bot shuru korun"),
      BotCommand(command="t", description="Form automation shuru korun"),
  ])
  print("Bot successfully running...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())
