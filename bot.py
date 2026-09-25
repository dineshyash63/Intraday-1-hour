from datetime import datetime
import os
import pandas as pd
import requests
import yfinance as yf

# Telegram Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Large Watchlist to ensure hourly signals are always found
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
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
      requests.post(url, json=payload, timeout=10)
    except Exception as e:
      print(f"Telegram error: {e}")


def run_guaranteed_hourly_bot():
  signals = []
  time_str = datetime.now().strftime("%d-%m-%Y %H:%M")

  for stock in WATCHLIST:
    try:
      df = yf.download(stock, period="5d", interval="15m", progress=False)
      if df.empty or len(df) < 5:
        continue

      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      current_price = float(df["Close"].iloc[-1])
      prev_close = float(df["Close"].iloc[-2])
      high_price = float(df["High"].iloc[-1])
      low_price = float(df["Low"].iloc[-1])

      pct_change = ((current_price - prev_close) / prev_close) * 100
      action = "BUY" if pct_change >= 0 else "SELL"

      if action == "BUY":
        sl = low_price * 0.992
        target = current_price + ((current_price - sl) * 1.5)
      else:
        sl = high_price * 1.008
        target = current_price - ((sl - current_price) * 1.5)

      # Score based on absolute momentum to sort the best available stocks
      score = abs(pct_change)

      signals.append({
          "stock": stock.replace(".NS", ""),
          "action": action,
          "price": current_price,
          "change": pct_change,
          "sl": sl,
          "target": target,
          "score": score,
      })
    except Exception as e:
      print(f"Error processing {stock}: {e}")

  # Sort by highest momentum score to guarantee top 5 signals every hour
  signals = sorted(signals, key=lambda x: x["score"], reverse=True)
  top_signals = signals[:5]

  msg_lines = [
      "⚡ *GUARANTEED HOURLY TOP 5 SIGNALS* ⚡",
      f"🕒 *Time:* {time_str} IST",
      "----------------------------------------",
  ]

  if top_signals:
    for i, sig in enumerate(top_signals, 1):
      emoji = "🟢" if sig["action"] == "BUY" else "🔴"
      s_text = (
          f"{i}. {emoji} *{sig['stock']}* ({sig['action']})\n"
          f"   • Price: ₹{sig['price']:.2f} ({sig['change']:+.2f}%)\n"
          f"   • Stop Loss: ₹{sig['sl']:.2f}\n"
          f"   • Target: ₹{sig['target']:.2f}\n"
      )
      msg_lines.append(s_text)
  else:
    msg_lines.append(
        "⚠️ Hourly check completed. Fetching next market momentum..."
    )

  final_message = "\n".join(msg_lines)
  send_telegram_message(final_message)


if __name__ == "__main__":
  run_guaranteed_hourly_bot()
    
