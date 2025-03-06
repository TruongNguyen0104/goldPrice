import asyncio
from flask import Flask
import threading
import os
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from util.utils import NOW

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

def start_flask_app():
    port = int(os.getenv("PORT", 10000))  # Use Render-assigned port
    app.run(host="0.0.0.0", port=port)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=start_flask_app)
flask_thread.daemon = True
flask_thread.start()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def escape_md(text):
    escape_chars = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        URL = "https://webgia.com/gia-vang/doji/"
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                if response.status != 200:
                    await update.message.reply_text("Price not found. Website returned an error.")
                    return
                page_content = await response.text()
        
        soup = BeautifulSoup(page_content, "html.parser")
        row = soup.find("td", string="Nhẫn tròn 999 Hưng Thịnh Vượng")

        if not row:
            await update.message.reply_text("Could not find the gold price information.")
            return

        row = row.find_parent("tr")
        tds = row.find_all("td")

        if len(tds) < 7:
            await update.message.reply_text("Error parsing price data.")
            return

        hcm_price = {
            "Mua vào": escape_md(tds[-2].get_text(strip=True)),
            "Bán ra": escape_md(tds[-1].get_text(strip=True)),
        }

        message = (
            f"\U0001F4E2 *DOJI Gold Price Update* \U0001F3C6\n"
            f"\U0001F4C5 *Date:* {escape_md(NOW)}\n\n"
            f"\U0001F4B0 *Mua vào:* {hcm_price['Mua vào']}\n"
            f"\U0001F4B0 *Bán ra:* {hcm_price['Bán ra']}\n"
        )

        await update.message.reply_text(message, parse_mode="MarkdownV2")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))
    
    print("Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    try:
        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=start_flask_app)
        flask_thread.daemon = True
        flask_thread.start()

        # Use existing event loop instead of asyncio.run()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
