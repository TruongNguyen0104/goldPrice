import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
from  util.utils import NOW, datetime
import re


## Constants
# Output directory and file paths
OUTPUT_DIR = os.path.join(os.getcwd(), "data")
CSV_FILENAME = os.path.join(OUTPUT_DIR, "gold_price.csv")
# NOW is in the format "04/03/2025 12:30:45"
ALTERNATIVE_FILENAME = os.path.join(
    OUTPUT_DIR, 
    f"gold_price_{datetime.strptime(NOW, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d_%H%M%S')}.csv"
)

# Load Telegram credentials from environment variables``
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

def scrapping_data(brand: str) -> pd.DataFrame:
    """
    Scrape gold price data from the given brand's webpage and return new rows.

    """

    URL = f"https://giavang.org/trong-nuoc/{brand}/"
    response = requests.get(URL)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        gold_price = soup.find('div', class_='gold-price-box')

        timestamp = NOW

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
                new_rows.append(new_row2)
        
        return new_rows

def extract_data(df: pd.DataFrame) -> None:
    """
    Extract data from the given DataFrame and save it to a CSV file.

    """
    try:
        df.to_csv(CSV_FILENAME, index=False, encoding='utf-8-sig', mode='a',
                   header=not os.path.exists(CSV_FILENAME))
        print('Data saved to CSV file.')

    except:
        print('Failed to save the data to the main CSV file. Saving to alternate file.')
        df.to_csv(ALTERNATIVE_FILENAME, index=False, encoding='utf-8-sig', mode='w')


    print('Save data completed.')

# Main function
def main() -> None:
    print('Starting scraping...')
    # Your scraping code here
    df = pd.DataFrame(columns=['Date','Brand','Type','Buy','Buy Change','Sell','Sell Change'])

        # URL of the webpage to scrape
    for brand in ['doji', 'pnj', 'sjc', 'phu-quy', 'bao-tin-minh-chau', 'bao-tin-manh-hai', 'mi-hong', 'ngoc-tham']:
        
        new_rows = scrapping_data(brand)
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True) 

        # Send message for DOJI brand
        if brand == 'doji':
            message_to_telegram(new_rows)

        
    #Extract data to CSV
    extract_data(df)
        
    print('Scraping completed.')


if __name__ == "__main__":
    main()
