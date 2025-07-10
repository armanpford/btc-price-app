import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta

# === CONFIG ===
WALLET_FILE = "wallet.json"
TRADE_LOG = "trades.log"
TRADING_PAIR = "BTC-USDT"
FEE_RATE = 0.001         # 0.1%
SLIPPAGE_RATE = 0.0006   # 0.06%
UPDATE_INTERVAL = 10     # seconds
START_BALANCE = 1000.0

# === TIME ===
def malaysia_time():
    return datetime.now(timezone(timedelta(hours=8)))

# === FETCH PRICE ===
def fetch_price():
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={TRADING_PAIR}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return float(data["data"]["price"])
    except Exception as e:
        print(f"❌ Error fetching price: {e}")
        return None

# === WALLET ===
def load_wallet():
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, "r") as f:
            return json.load(f)
    return {
        "usd_balance": START_BALANCE,
        "btc_balance": 0.0,
        "start_time": malaysia_time().isoformat(),
        "total_fees": 0.0,
        "total_slippage": 0.0
    }

def save_wallet(wallet):
    with open(WALLET_FILE, "w") as f:
        json.dump(wallet, f, indent=2)

# === LOGGING ===
def log_trade(action, amount_btc, price, fee, slippage):
    timestamp = malaysia_time().isoformat()
    with open(TRADE_LOG, "a") as f:
        f.write(f"{timestamp} | {action.upper()} {amount_btc:.6f} BTC @ ${price:,.2f} | Fee: ${fee:.4f} | Slippage: ${slippage:.4f}\n")

# === TRADING ===
def simulate_trade(wallet, price, action="buy"):
    if action == "buy" and wallet["usd_balance"] > 0:
        usd = wallet["usd_balance"]
        fee = usd * FEE_RATE
        slippage = usd * SLIPPAGE_RATE
        net_usd = usd - fee - slippage
        btc_bought = net_usd / price

        wallet["usd_balance"] = 0.0
        wallet["btc_balance"] += btc_bought
        wallet["total_fees"] += fee
        wallet["total_slippage"] += slippage

        log_trade("buy", btc_bought, price, fee, slippage)

    elif action == "sell" and wallet["btc_balance"] > 0:
        btc = wallet["btc_balance"]
        gross_usd = btc * price
        fee = gross_usd * FEE_RATE
        slippage = gross_usd * SLIPPAGE_RATE
        net_usd = gross_usd - fee - slippage

        wallet["btc_balance"] = 0.0
        wallet["usd_balance"] += net_usd
        wallet["total_fees"] += fee
        wallet["total_slippage"] += slippage

        log_trade("sell", btc, price, fee, slippage)

# === DISPLAY ===
def display_wallet_summary(wallet, price):
    usd = wallet['usd_balance']
    btc = wallet['btc_balance']
    btc_value = btc * price
    total_value = usd + btc_value
    profit = total_value - START_BALANCE
    percent = (profit / START_BALANCE) * 100

    print("\n==================== 💼 WALLET SUMMARY ====================")
    print(f"📅 Started:       {wallet['start_time']}")
    print(f"💵 USD Balance:  ${usd:,.2f}")
    print(f"🪙 BTC Balance:  {btc:.6f} BTC")
    print(f"📈 BTC Price:    ${price:,.2f}")
    print(f"💰 Total Value:  ${total_value:,.2f}")
    print(f"📊 Profit/Loss:  ${profit:,.2f} ({percent:+.2f}%)")
    print(f"💸 Total Fees:   ${wallet['total_fees']:.4f}")
    print(f"📉 Slippage Loss: ${wallet['total_slippage']:.4f}")
    print("==========================================================\n")

def display_live_status(wallet, price):
    usd = wallet["usd_balance"]
    btc = wallet["btc_balance"]
    total = usd + (btc * price)
    print(f"🟡 {malaysia_time().strftime('%H:%M:%S')} | Price: ${price:,.2f} | USD: ${usd:.2f} | BTC: {btc:.6f} | Total: ${total:,.2f}")

# === STRATEGY: Simple Momentum ===
def should_buy(prices, wallet):
    return wallet["usd_balance"] > 0 and prices[-1] > prices[-2] > prices[-3]

def should_sell(prices, wallet):
    return wallet["btc_balance"] > 0 and prices[-1] < prices[-2] < prices[-3]

# === MAIN LOOP ===
def main():
    wallet = load_wallet()
    print("=" * 50)
    print("📊 BTC Momentum Bot Started")
    price = fetch_price()
    if not price:
        print("❌ Could not fetch initial price.")
        return

    display_wallet_summary(wallet, price)
    price_history = []

    try:
        while True:
            price = fetch_price()
            if price:
                price_history.append(price)
                if len(price_history) > 3:
                    display_live_status(wallet, price)

                    if should_buy(price_history, wallet):
                        simulate_trade(wallet, price, "buy")
                    elif should_sell(price_history, wallet):
                        simulate_trade(wallet, price, "sell")

                    save_wallet(wallet)
                    price_history = price_history[-3:]  # Keep only last 3 prices

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Stopping... Selling all BTC at market price")
        price = fetch_price()
        if price:
            simulate_trade(wallet, price, action="sell")
            display_wallet_summary(wallet, price)
            save_wallet(wallet)
        else:
            print("⚠️ Could not fetch final price.")

if __name__ == "__main__":
    main()



