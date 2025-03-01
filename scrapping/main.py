import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import re

# Get current time in GMT+7
gmt_plus_7 = timezone(timedelta(hours=7))
TODAY = datetime.now(gmt_plus_7).strftime("%Y-%m-%d-%H%M%S")  # Get the current date and time

output_dir = os.path.join(os.getcwd(), "data")
csv_filename = os.path.join(output_dir, "gold_price.csv")
alternate_csv_filename = os.path.join(output_dir, f"gold_price_{TODAY}.csv")

# Load Telegram credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Function to escape special characters for Telegram MarkdownV2
def escape_markdown(text):
    if not isinstance(text, str):
        text = str(text)  # Convert to string if not already

    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# Function to send Telegram message
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials are missing!")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "MarkdownV2"
    }

    response = requests.post(telegram_url, json=payload)
    try:
        res_json = response.json()
        if res_json.get("ok"):
            print("Message sent successfully!")
        else:
            print(f"Failed to send message: {res_json}")
    except:
        print("Error parsing Telegram response.")

# Function to send one message for both new rows
def message_to_telegram(rows):
    if not rows:
        return  # No data to send

    message = "📢 *Gold Price Update* 🏆\n"

    for index, row in enumerate(rows):
        if index == 0:  # First row → Include Date & Brand
            message += (
                f"\n🗓 *Date:* {escape_markdown(row['Date'])}\n"
                f"🏢 *Brand:* {escape_markdown(row['Brand'])}\n"
                f"\n"
            )

        message += (
            f"💎 *Type:* {escape_markdown(row['Type'])}\n"
            f"💰 *Buy Price:* {escape_markdown(row['Buy'])}\n"
            f"   📈 Change: {escape_markdown(row['Buy Change'])}\n"  # Separated Buy Change
            f"💵 *Sell Price:* {escape_markdown(row['Sell'])}\n"
            f"   📉 Change: {escape_markdown(row['Sell Change'])}\n"  # Separated Sell Change
            f"\n"
        )

    send_telegram_message(message)
    time.sleep(5)

df = pd.DataFrame(columns=['Date','Brand','Type','Buy','Buy Change','Sell','Sell Change'])

# URL of the webpage to scrape
for brand in ['doji', 'pnj', 'sjc', 'phu-quy', 'bao-tin-minh-chau', 'bao-tin-manh-hai', 'mi-hong', 'ngoc-tham']:
    
    url = f"https://giavang.org/trong-nuoc/{brand}/"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        timestamp = soup.find('h1', class_='box-headline highlight')
        gold_price = soup.find('div', class_='gold-price-box')

        timestamp = timestamp.text.split(' ')[-1] + ' ' + timestamp.text.split(' ')[-2]

        if gold_price:
            gold_price = gold_price.getText().strip().split('\n')
            gold_price = list(filter(None, gold_price))  # Remove empty strings

            new_rows = []

            # First row
            new_row = {
                'Date': timestamp,
                'Brand': brand.upper(),
                'Type': "Bullion" if "Miếng" in gold_price[0] else "Ring",
                'Buy': gold_price[2],
                'Buy Change': gold_price[3],
                'Sell': gold_price[5],
                'Sell Change': gold_price[6]
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)  # Use concat instead of append
            new_rows.append(new_row)

            # Second row (if available)
            if len(gold_price) > 7:
                new_row2 = {
                    'Date': timestamp,  # This will be ignored in the message
                    'Brand': brand.upper(),  # This will be ignored in the message
                    'Type': "Bullion" if "Miếng" in gold_price[7] else "Ring",
                    'Buy': gold_price[9],
                    'Buy Change': gold_price[10],
                    'Sell': gold_price[12],
                    'Sell Change': gold_price[13]
                }
                df = pd.concat([df, pd.DataFrame([new_row2])], ignore_index=True)
                new_rows.append(new_row2)

            # Send one message for both rows
            if brand == 'doji':
                message_to_telegram(new_rows)

        else:
            print('Gold price not found.')
    else:
        print('Failed to retrieve the webpage.')

try:
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig', mode='a', header=not os.path.exists(csv_filename))
    print('Data saved to CSV file.')
except:
    print('Failed to save the data to the main CSV file. Saving to alternate file.')
    df.to_csv(alternate_csv_filename, index=False, encoding='utf-8-sig', mode='w')
