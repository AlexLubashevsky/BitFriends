from telegram.ext import Application, CommandHandler
import asyncio
import json
import os
import requests
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token
TOKEN = '7223957499:AAHc1BFIAyh9rF8uK7pgD8TuxfWE8um8Ec4'
DATA_FILE = 'bitfriends_data.json'
SOL_RECEIVER = '4WF1wGepvyZ8sL9iTnLs7skvCqpDgiZPM9zTeUfk5nkQ'
ETH_RECEIVER = '0x7C52A0C0b097134Dd2719bf26f63831a5bd20D44'
ETHERSCAN_API_KEY = 'YOUR_ETHERSCAN_API_KEY'  # <-- Replace with your Etherscan API key

# Example skin data (replace URLs with your own images if desired)
SKINS = {
    'default': {
        'name': 'Default',
        'price': 0,
        'sol_price': 0,
        'eth_price': 0,
        'img': 'https://i.imgur.com/8Km9tLL.png'
    },
    'cat': {
        'name': 'Cat',
        'price': 50,
        'sol_price': 0.01,  # 0.01 SOL
        'eth_price': 0.0005,  # 0.0005 ETH
        'img': 'https://i.imgur.com/J5LVHEL.png'
    },
    'fox': {
        'name': 'Fox',
        'price': 100,
        'sol_price': 0.02,  # 0.02 SOL
        'eth_price': 0.001,  # 0.001 ETH
        'img': 'https://i.imgur.com/2yaf2wb.png'
    }
}

# Helper functions for data persistence

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def get_user_pet(user_id, data):
    if str(user_id) not in data:
        data[str(user_id)] = {
            'hunger': 50,
            'happiness': 50,
            'skin': 'default',
            'coins': 100,  # Give new users some coins to start
            'owned_skins': ['default']
        }
    # Ensure new fields are present for old users
    pet = data[str(user_id)]
    if 'owned_skins' not in pet:
        pet['owned_skins'] = ['default']
    if 'coins' not in pet:
        pet['coins'] = 100
    return pet

# Solana transaction verification (simple, public RPC)
def verify_solana_payment(tx_signature, expected_amount, skin_key):
    # Use Solana public RPC to fetch transaction details
    url = f"https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [tx_signature, "json"]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        tx = resp.json().get('result')
        if not tx:
            return False, "Transaction not found."
        # Check if the transaction sent expected_amount SOL to SOL_RECEIVER
        meta = tx.get('meta', {})
        if meta.get('err') is not None:
            return False, "Transaction failed."
        # Find transfer to our address
        post_balances = tx['meta']['postTokenBalances'] if 'postTokenBalances' in tx['meta'] else []
        # For simplicity, check inner instructions for SOL transfer
        for inst in tx['transaction']['message']['instructions']:
            if 'parsed' in inst:
                parsed = inst['parsed']
                if parsed['type'] == 'transfer' and parsed['info']['destination'] == SOL_RECEIVER:
                    lamports = int(parsed['info']['lamports'])
                    sol = lamports / 1_000_000_000
                    if sol >= expected_amount:
                        return True, "Payment verified."
        # Fallback: check pre/post balances (not as reliable)
        return False, "No matching SOL transfer found."
    except Exception as e:
        return False, f"Error verifying transaction: {e}"

# Ethereum transaction verification using Etherscan API
def verify_eth_payment(tx_hash, expected_amount):
    url = f"https://api.etherscan.io/api"
    params = {
        'module': 'proxy',
        'action': 'eth_getTransactionByHash',
        'txhash': tx_hash,
        'apikey': ETHERSCAN_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        result = resp.json().get('result')
        if not result:
            return False, "Transaction not found."
        to_addr = result.get('to', '').lower()
        value_wei = int(result.get('value', '0'), 16)
        value_eth = value_wei / 1e18
        if to_addr != ETH_RECEIVER.lower():
            return False, "Transaction not sent to the correct address."
        if value_eth < expected_amount:
            return False, f"Transaction value too low. Sent: {value_eth} ETH, required: {expected_amount} ETH."
        return True, "Payment verified."
    except Exception as e:
        return False, f"Error verifying transaction: {e}"

# Command handlers

async def start(update, context):
    web_app_url = "https://your-web-app-url.com"  # Replace with your deployed web app URL
    keyboard = [
        [KeyboardButton(text="Start BitFriends", web_app=WebAppInfo(url=web_app_url))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to BitFriends! Tap the button below to start caring for your pet.",
        reply_markup=reply_markup
    )

async def status(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    skin = pet['skin']
    msg = (f"🐶 Pet Status:\n"
           f"Hunger: {pet['hunger']}\n"
           f"Happiness: {pet['happiness']}\n"
           f"Skin: {SKINS[skin]['name']}\n"
           f"Coins: {pet['coins']}")
    await update.message.reply_photo(SKINS[skin]['img'], caption=msg)

async def feed(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    if pet['hunger'] >= 100:
        await update.message.reply_text('Your pet is already full!')
        return
    pet['hunger'] = min(100, pet['hunger'] + 20)
    save_data(data)
    await update.message.reply_text('You fed your pet! 🍖 Hunger +20')

async def play(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    pet['happiness'] = min(100, pet['happiness'] + 15)
    pet['hunger'] = max(0, pet['hunger'] - 10)
    save_data(data)
    await update.message.reply_text('You played with your pet! 🎾 Happiness +15, Hunger -10')

async def shop(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    msg = '🛍️ Pet Skin Shop:\n'
    for key, skin in SKINS.items():
        owned = '✅ Owned' if key in pet['owned_skins'] else f"💰 {skin['price']} coins / {skin['sol_price']} SOL / {skin['eth_price']} ETH"
        msg += f"\n{skin['name']} - {owned}"
        await update.message.reply_photo(skin['img'], caption=f"{skin['name']}\nPrice: {skin['price']} coins / {skin['sol_price']} SOL / {skin['eth_price']} ETH" if skin['price'] > 0 else 'Default skin')
    await update.message.reply_text(msg)

async def buy_skin(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    if len(context.args) != 1:
        await update.message.reply_text('Usage: /buy_skin <skin_name>')
        return
    skin_key = context.args[0].lower()
    if skin_key not in SKINS:
        await update.message.reply_text('That skin does not exist.')
        return
    if skin_key in pet['owned_skins']:
        await update.message.reply_text('You already own this skin!')
        return
    price = SKINS[skin_key]['price']
    sol_price = SKINS[skin_key]['sol_price']
    eth_price = SKINS[skin_key]['eth_price']
    if pet['coins'] >= price and price > 0:
        pet['coins'] -= price
        pet['owned_skins'].append(skin_key)
        save_data(data)
        await update.message.reply_text(f"You bought the {SKINS[skin_key]['name']} skin! Use /set_skin {skin_key} to equip it.")
    else:
        msg = f"Not enough coins!\nTo buy this skin, you can pay with either:\n"
        if sol_price > 0:
            msg += f"\n<b>Solana:</b> Send {sol_price} SOL to <code>{SOL_RECEIVER}</code> and use /confirm_payment {skin_key} <tx_signature>"
        if eth_price > 0:
            msg += f"\n<b>Ethereum:</b> Send {eth_price} ETH to <code>{ETH_RECEIVER}</code> and use /confirm_payment_eth {skin_key} <tx_hash>"
        await update.message.reply_text(msg, parse_mode='HTML')

async def confirm_payment(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    if len(context.args) != 2:
        await update.message.reply_text('Usage: /confirm_payment <skin_name> <tx_signature>')
        return
    skin_key = context.args[0].lower()
    tx_signature = context.args[1]
    if skin_key not in SKINS:
        await update.message.reply_text('That skin does not exist.')
        return
    if skin_key in pet['owned_skins']:
        await update.message.reply_text('You already own this skin!')
        return
    sol_price = SKINS[skin_key]['sol_price']
    ok, msg = verify_solana_payment(tx_signature, sol_price, skin_key)
    if ok:
        pet['owned_skins'].append(skin_key)
        save_data(data)
        await update.message.reply_text(f"Payment verified! You now own the {SKINS[skin_key]['name']} skin. Use /set_skin {skin_key} to equip it.")
    else:
        await update.message.reply_text(f"Payment not verified: {msg}")

async def confirm_payment_eth(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    if len(context.args) != 2:
        await update.message.reply_text('Usage: /confirm_payment_eth <skin_name> <tx_hash>')
        return
    skin_key = context.args[0].lower()
    tx_hash = context.args[1]
    if skin_key not in SKINS:
        await update.message.reply_text('That skin does not exist.')
        return
    if skin_key in pet['owned_skins']:
        await update.message.reply_text('You already own this skin!')
        return
    eth_price = SKINS[skin_key]['eth_price']
    ok, msg = verify_eth_payment(tx_hash, eth_price)
    if ok:
        pet['owned_skins'].append(skin_key)
        save_data(data)
        await update.message.reply_text(f"ETH payment verified! You now own the {SKINS[skin_key]['name']} skin. Use /set_skin {skin_key} to equip it.")
    else:
        await update.message.reply_text(f"ETH payment not verified: {msg}")

async def set_skin(update, context):
    user_id = update.effective_user.id
    data = load_data()
    pet = get_user_pet(user_id, data)
    if len(context.args) != 1:
        await update.message.reply_text('Usage: /set_skin <skin_name>')
        return
    skin_key = context.args[0].lower()
    if skin_key not in SKINS:
        await update.message.reply_text('That skin does not exist.')
        return
    if skin_key not in pet['owned_skins']:
        await update.message.reply_text('You do not own this skin!')
        return
    pet['skin'] = skin_key
    save_data(data)
    await update.message.reply_text(f"Skin set to {SKINS[skin_key]['name']}!")
    await update.message.reply_photo(SKINS[skin_key]['img'], caption=f"Your pet now looks like this!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('feed', feed))
    app.add_handler(CommandHandler('play', play))
    app.add_handler(CommandHandler('shop', shop))
    app.add_handler(CommandHandler('buy_skin', buy_skin))
    app.add_handler(CommandHandler('set_skin', set_skin))
    app.add_handler(CommandHandler('confirm_payment', confirm_payment))
    app.add_handler(CommandHandler('confirm_payment_eth', confirm_payment_eth))
    app.run_polling()

if __name__ == '__main__':
    main()
