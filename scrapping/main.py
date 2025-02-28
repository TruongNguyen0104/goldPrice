import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
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

message_template = (
            "📢 *Gold Price Update* 🏆\n"
            "🗓 *Date:* {date}\n"
            "🏢 *Brand:* {brand}\n"
            "💎 *Type:* {gold_type}\n"
            "💰 *Buy Price:* {buy_price} {buy_change}\n"
            "💵 *Sell Price:* {sell_price} {sell_change}\n"
        )


# Function to escape special characters for Telegram MarkdownV2
def escape_markdown(text):
    if not isinstance(text, str):
        text = str(text)  # Convert to string if not already

    # Escape all Telegram MarkdownV2 special characters
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


def message_to_telegram(row):
        message = message_template.format(
            date=escape_markdown(row["Date"]),
            brand=escape_markdown(row["Brand"]),
            gold_type=escape_markdown(row["Type"]),
            buy_price=escape_markdown(row["Buy"]),
            buy_change=escape_markdown(row["Buy Change"]),
            sell_price=escape_markdown(row["Sell"]),
            sell_change=escape_markdown(row["Sell Change"])
        )

        send_telegram_message(message)


df = pd.DataFrame(columns=['Date','Brand','Type','Buy','Buy Change','Sell','Sell Change'])   # Create a new DataFrame to store the data

# URL of the webpage to scrape
for brand in ['doji','pnj','sjc','phu-quy','bao-tin-minh-chau','bao-tin-manh-hai','mi-hong','ngoc-tham']:
    
    url = f"https://giavang.org/trong-nuoc/{brand}/"

    # Send a GET request to the webpage
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the webpage
        soup = BeautifulSoup(response.content, 'html.parser')

       # Find the element on the webpage
        timestamp = soup.find('h1', class_='box-headline highlight')  # Get the timestamp
        gold_price = soup.find('div', class_='gold-price-box')  #Get the gold price
        
        timestamp = timestamp.text.split(' ')[-1] + ' ' + timestamp.text.split(' ')[-2]
        # Check if the element exists
        if gold_price:
            gold_price = gold_price.getText().strip().split('\n')
            gold_price = list(filter(None ,gold_price)) # Remove empty strings from the list

            """ the data to the DataFrame
                bullion vs ring
            """
            new_row = {
                'Date': timestamp,
                'Brand': brand.upper(),
                'Type': "Bullion" if "Miếng" in gold_price[0] else "Ring",
                'Buy': gold_price[2],
                'Buy Change': gold_price[3],
                'Sell': gold_price[5],
                'Sell Change': gold_price[6]
            }
            
            df = df.append(new_row, ignore_index=True)
            send_telegram_message(new_row)
            
            if len(gold_price) > 7:
                new_row2 = {
                    'Date': timestamp,
                    'Brand': brand.upper(),
                    'Type': "Bullion" if "Miếng" in gold_price[7] else "Ring",
                    'Buy': gold_price[9],
                    'Buy Change': gold_price[10],
                    'Sell': gold_price[12],
                    'Sell Change': gold_price[13]
                }
                df = df.append(new_row2, ignore_index=True)
                send_telegram_message(new_row2)  
        else:
            print('Gold price not found.')
    else:
        print('Failed to retrieve the webpage.')
try:
    df.to_csv(csv_filename, index=False,encoding='utf-8-sig',mode='a', header=not os.path.exists(csv_filename))  # Save the data to a CSV file
    print('Data saved to CSV file.')
except:
    print('Failed to save the data to the main CSV file. System will try to save the data to a new CSV file.')
    df.to_csv(alternate_csv_filename, index=False,encoding='utf-8-sig', mode='w')  # Save the data to a CSV file
 
