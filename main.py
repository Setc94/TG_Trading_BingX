import os
import re
import requests
from dotenv import load_dotenv
from telethon import TelegramClient, events
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Read variables from .env
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
bingx_api_key = os.getenv("BINGX_API_KEY")
bingx_api_secret = os.getenv("BINGX_API_SECRET")
telegram_channel_id = int(os.getenv("TELEGRAM_CHANNEL_ID"))

# Initialize Telegram client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

def parse_message(text):
    # Parse the message to extract required information
    try:
        symbol = re.search(r"([A-Z]+USDT)", text).group(1)
        buy_price = re.search(r"Entry:\s*(\d+\.?\d*)", text).group(1)
        target1 = re.search(r"Target 1:\s*(\d+\.?\d*)", text).group(1)
        stop_loss = re.search(r"Stop Loss:\s*(\d+\.?\d*)", text).group(1)
        return symbol, float(buy_price), float(target1), float(stop_loss)
    except AttributeError:
        return None

def open_trade(symbol, buy_price, target1, stop_loss, amount, leverage):
    url = "https://api.bingx.com/api/v1/order/place"  # Ensure to use the sandbox URL
    headers = {
        'X-BX-APIKEY': bingx_api_key,
        'X-BX-SIGNATURE': bingx_api_secret,
    }
    payload = {
        "symbol": symbol,
        "side": "BUY",
        "type": "LIMIT",
        "quantity": amount,
        "price": buy_price,
        "stopPrice": stop_loss,
        "leverage": leverage,
        "takeProfitPrice": target1
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def log_trade(result, success, message):
    with open("trade_log.txt", "a") as file:
        log_entry = f"{datetime.now()} - Result: {result} - Success: {success} - Message: {message}\n"
        file.write(log_entry)

@client.on(events.NewMessage(chats=telegram_channel_id))
async def handler(event):
    message = event.message.message
    if "Normal" in message:  # Check if the message contains the word "Volume"
        parsed = parse_message(message)
        if parsed:
            symbol, buy_price, target1, stop_loss = parsed
            amount = 100  # Set the amount to use for each trade
            leverage = 10  # Set the leverage
            try:
                result = open_trade(symbol, buy_price, target1, stop_loss, amount, leverage)
                if result.get("status") == "success":
                    log_trade(result, True, "Trade opened successfully")
                else:
                    log_trade(result, False, result.get("message", "Failed to open trade"))
            except Exception as e:
                log_trade({}, False, f"Error: {str(e)}")

if __name__ == '__main__':
    print("Bot is running...")
    client.run_until_disconnected()
