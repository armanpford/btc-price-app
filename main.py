from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import ccxt

app = FastAPI()

exchange = ccxt.kucoin()

@app.get("/", response_class=HTMLResponse)
async def get_btc_price():
    ticker = exchange.fetch_ticker("BTC/USDT")
    price = ticker['last']
    return f"""
    <html>
      <head><title>BTC Price</title></head>
      <body style='font-family:sans-serif;text-align:center;margin-top:50px;'>
        <h1>🟡 BTC/USDT Price</h1>
        <h2>${price:,.2f}</h2>
        <p>Live from KuCoin</p>
      </body>
    </html>
    """
