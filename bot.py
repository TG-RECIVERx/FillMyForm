import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, Message
from playwright.async_api import async_playwright

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
      "As-salamu alaikum! Apnar Google Form automation bot ready ache. Shuru"
      " korar jonno `/t` command din."
  )


@dp.message(Command("t"))
async def cmd_t(message: Message, state: FSMContext):
  await state.set_state(FormAutomationStates.waiting_for_link)
  await message.answer("🔗 Doya kore apnar Google Form er link-ti ekhane din:")


@dp.message(FormAutomationStates.waiting_for_link)
async def process_form_link(message: Message, state: FSMContext):
  form_link = message.text.strip()
  await state.update_data(form_link=form_link)
  await state.set_state(FormAutomationStates.waiting_for_count)
  await message.answer(
      f"✅ Link pawa gese!\n`{form_link}`\n\nEkhon apni total koyti responses"
      " generate korte chan? (Jemon: 500, 1000 ba 2000)"
  )


@dp.message(FormAutomationStates.waiting_for_count)
async def process_response_count(message: Message, state: FSMContext):
  try:
    total_count = int(message.text.strip())
  except ValueError:
    await message.answer(
        "❌ Doya kore ekti valid number din (jemon: 1000):"
    )
    return

  data = await state.get_data()
  form_link = data.get("form_link")
  chat_id = message.chat.id

  await message.answer(
      f"🚀 Automation start hocche!\n• Form: `{form_link}`\n• Total Target:"
      f" `{total_count}` responses\n\nProcesing cholche, complete hole notification"
      " paben..."
  )
  await state.clear()

  # Background-e automation run korar jonno asyncio task start kora hocche
  asyncio.create_task(
      run_fillmyform_automation(chat_id, form_link, total_count)
  )


async def run_fillmyform_automation(chat_id: int, form_link: string, total_count: int):
  success_count = 0
  failed_count = 0

  # Prottek batch-e max 100 ta kore response generate kora hobe (website er limit onujayi)
  batch_size = 100
  batches = (total_count + batch_size - 1) // batch_size

  async with async_playwright() as p:
    # Headless=False dile browser samne open hoye kaj korbe, True dile background-e cholbe
    browser = await p.chromium.launch(headless=True)
    
    for i in range(batches):
      current_batch = min(batch_size, total_count - success_count - failed_count)
      if current_batch <= 0:
        break

      context = await browser.new_context()
      page = await context.new_page()

      try:
        # 1. FillMyForm website-e jaoya
        await page.goto("https://www.fillmyform.xyz/fill", timeout=60000)

        # 2. Google form link input kora
        await page.fill("#form-url", form_link)
        await page.click("button[type='submit']")

        # 3. Analyze hoye configure page-e jawar jonno wait kora
        await page.wait_for_url("**/fill/configure", timeout=30000)

        # 4. Number of responses box ba slider-e value set kora
        # Screenshot onujayi configure page-e input ba slider thake
        response_input = page.locator("#response-count")
        if await response_input.count() > 0:
          await response_input.fill(str(current_batch))
        else:
          # Jodi slider ba alternative element hoy
          pass

        # 5. Generate Responses button click kora
        generate_btn = page.locator("button:has-text('Generate')")
        await generate_btn.click()

        # Result ba success er jonno wait kora
        await page.wait_for_timeout(10000)  # Generation er somoy er jonno delay
        
        success_count += current_batch
      except Exception as e:
        failed_count += current_batch
        logging.error(f"Automation error in batch {i+1}: {e}")
      finally:
        await context.close()

    await browser.close()

  # Final Notification pathano
  await bot.send_message(
      chat_id,
      f"📊 **Automation Complete!**\n\n"
      f"• Target: {total_count}\n"
      f"• Successfully Generated: {success_count}\n"
      f"• Failed: {failed_count}\n\n"
      f"✅ Sob kaj sesh hoyeche bhai!",
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
