import asyncio
import logging
import random
import re
import requests
from bs4 import BeautifulSoup
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
      "As-salamu alaikum! Smart Form Submitter Bot ready ache. `/t` command"
      " diye shuru korun."
  )


@dp.message(Command("t"))
async def cmd_t(message: Message, state: FSMContext):
  await state.set_state(FormAutomationStates.waiting_for_link)
  await message.answer(
      "🔗 Doya kore apnar Google Form er link-ti (jemon `.../viewform`) ekhane"
      " din:"
  )


@dp.message(FormAutomationStates.waiting_for_link)
async def process_form_link(message: Message, state: FSMContext):
  form_link = message.text.strip()
  
  # Link sothik kina ba entry extract kora jacche kina check kora
  if "viewform" not in form_link:
    await message.answer("❌ Doya kore ekti valid Google Form 'viewform' link din:")
    return

  await state.update_data(form_link=form_link)
  await state.set_state(FormAutomationStates.waiting_for_count)
  await message.answer(
      f"✅ Link sothikvabe pawa gese!\n\nEkhon apni eksathe total koyti"
      " responses pathate chan? (Jemon: 500, 1000 ba 2000)"
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
      f"🚀 Form analyze ebong bulk submission start hocche!\n• Target:"
      f" `{total_count}` responses\n⏳ Kaj cholche, shesh hole notification"
      " paben..."
  )
  await state.clear()

  asyncio.create_task(extract_and_send_requests(chat_id, form_link, total_count))


async def extract_and_send_requests(chat_id: int, form_link: str, total_count: int):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    # 1. Google Form page fetch kore entry IDs ber kora
    response = requests.get(form_link, headers=headers, timeout=15)
    if response.status_code != 200:
      await bot.send_message(chat_id, "❌ Google Form-ti load kora jayni. Link check korun.")
      return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Form er post URL banano
    post_url = form_link.replace("viewform", "formResponse")

    # Form er input fields / entries khuje ber kora
    # Google form entries usually 'entry.XXXXXXXXX' namer hoy
    entry_names = set()
    for tag in soup.find_all(attrs={"name": True}):
      name = tag["name"]
      if name.startswith("entry."):
        entry_names.add(name)

    if not entry_names:
      await bot.send_message(chat_id, "❌ Form er kono entry field pawa jayni. Link-ti public kina check korun.")
      return

    success_count = 0
    failed_count = 0

    # 2. Bulk Request Loop
    for _ in range(total_count):
      payload = {}
      for entry in entry_names:
        # Protibar random data ba test text generate kora
        payload[entry] = random.choice(["Yes", "No", "Good", "Excellent", "1", "Test Response", "A", "B"])

      try:
        res = requests.post(post_url, data=payload, headers=headers, timeout=10)
        if res.status_code in [200, 302]:
          success_count += 1
        else:
          failed_count += 1
      except Exception:
        failed_count += 1

      await asyncio.sleep(0.02)  # Fast ebong safe interval

    # Final Notification
    await bot.send_message(
        chat_id,
        f"📊 **Bulk Submission Complete!**\n\n"
        f"• Total Target: {total_count}\n"
        f"• Successful: {success_count}\n"
        f"• Failed: {failed_count}\n\n"
        f"✅ Sob kaj sesh bhai!",
    )

  except Exception as e:
    await bot.send_message(chat_id, f"❌ Error: {str(e)}")


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
