import pandas as pd

# === CONFIGURATION ===
FEE_RATE = 0.001      # 0.1%
SLIPPAGE = 0.0006     # 0.06%
START_BALANCE = 1000
THRESHOLD = 0.0005    # 0.05% momentum threshold
LOOKBACK = 5          # Lookback in candles

# === LOAD PRICE DATA ===
df = pd.read_csv("5min_data.csv", parse_dates=["time"], index_col="time")

# === INITIAL STATE ===
usd_balance = START_BALANCE
btc_balance = 0.0
in_usd = True
trade_log = []

# === BACKTEST LOOP ===
for i in range(LOOKBACK, len(df)):
    now = df.index[i]
    current_price = df["close"].iloc[i]
    past_price = df["close"].iloc[i - LOOKBACK]
    
    momentum = (current_price - past_price) / past_price

    print(f"⏳ {now} | Price: ${current_price:.2f} | Momentum: {momentum:+.5f}")

    if momentum > THRESHOLD and in_usd:
        # Buy BTC
        fee = usd_balance * FEE_RATE
        slip = usd_balance * SLIPPAGE
        usd_net = usd_balance - fee - slip
        btc_bought = usd_net / current_price

        btc_balance = btc_bought
        usd_balance = 0
        in_usd = False

        trade_log.append((now, "BUY", current_price, btc_bought))
        print(f"📈 BUY at ${current_price:.2f} | BTC: {btc_bought:.6f} | Fee: ${fee:.2f}")

    elif momentum < -THRESHOLD and not in_usd:
        # Sell BTC
        gross_usd = btc_balance * current_price
        fee = gross_usd * FEE_RATE
        slip = gross_usd * SLIPPAGE
        usd_net = gross_usd - fee - slip

        usd_balance = usd_net
        btc_balance = 0
        in_usd = True

        trade_log.append((now, "SELL", current_price, usd_net))
        print(f"📉 SELL at ${current_price:.2f} | USD: ${usd_net:.2f} | Fee: ${fee:.2f}")

# === FINAL BALANCE ===
final_value = usd_balance if in_usd else btc_balance * df["close"].iloc[-1]
pnl = final_value - START_BALANCE
pnl_pct = (pnl / START_BALANCE) * 100

print("\n========= 📊 BACKTEST SUMMARY =========")
print(f"Trades: {len(trade_log)}")
print(f"Final balance: ${final_value:.2f} (PnL: ${pnl:+.2f}, {pnl_pct:+.2f}%)")

# === Optional: Save trade log ===
trade_df = pd.DataFrame(trade_log, columns=["time", "action", "price", "amount"])
trade_df.to_csv("momentum_trades.csv", index=False)


 
