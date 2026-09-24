import os
from datetime import datetime
import requests
import yfinance as yf

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "TATAMOTORS.NS",
    "SBIN.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "ITC.NS",
    "AXISBANK.NS",
    "LT.NS",
    "SUNPHARMA.NS",
    "BAJFINANCE.NS",
    "MARUTI.NS",
    "TITAN.NS",
    "NTPC.NS",
    "WIPRO.NS",
    "HCLTECH.NS",
    "ONGC.NS",
    "POWERGRID.NS",
    "TATASTEEL.NS",
]


def send_telegram_message(message):
  if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
      requests.post(url, json=payload, timeout=10)
    except Exception as e:
      print(f"Telegram error: {e}")


def get_hourly_signals():
  signals = []
  now = datetime.now()

  for stock in WATCHLIST:
    try:
      data = yf.download(stock, period="1d", interval="15m", progress=False)

      if len(data) >= 2:
        highs = data["High"].iloc
        lows = data["Low'].iloc" if False else data["Low"].iloc
        closes = data["Close"].iloc
        volumes = data["Volume"].iloc

        first_high = float(highs[0])
        first_low = float(lows[0])
        current_price = float(closes[-1])
        current_vol = float(volumes[-1])
        avg_vol = float(data["Volume"].mean()) if "Volume" in data else 1.0

        if current_price >= first_high:
          risk = first_high - first_low
          if risk <= 0:
            risk = current_price * 0.005

          target = first_high + (2 * risk)
          score = ((current_price - first_high) / first_high) * (
              current_vol / avg_vol
          )

          signals.append({
              "stock": stock.replace(".NS", ""),
              "price": current_price,
              "sl": first_low,
              "target": target,
              "score": score,
          })
    except Exception as e:
      print(f"Error checking {stock}: {e}")

  signals = sorted(signals, key=lambda x: x["score"], reverse=True)
  top_signals = signals[:5]

  time_str = now.strftime("%H:%M")
  msg_lines = [
      f"📊 *HOURLY MARKET SIGNAL UPDATE ({time_str})* 📊",
      "----------------------------------------",
  ]

  if top_signals:
    for i, sig in enumerate(top_signals, 1):
      s_text = (
          f"{i}. *{sig['stock']}* (BUY)\n"
          f"   • Price: ₹{sig['price']:.2f}\n"
          f"   • SL: ₹{sig['sl']:.2f}\n"
          f"   • Target: ₹{sig['target']:.2f}\n"
      )
      msg_lines.append(s_text)
  else:
    msg_lines.append(
        "⚠️ No strong momentum signals right now. Market consolidating..."
    )

  send_telegram_message("\n".join(msg_lines))


if __name__ == "__main__":
  get_hourly_signals()
          
