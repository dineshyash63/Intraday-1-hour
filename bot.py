import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# உங்களது நேரடி டெலிகிராம் சாவி விவரங்கள் இணைக்கப்பட்டுள்ளன
TELEGRAM_BOT_TOKEN = "8462007353:AAFZsWmNgiVWBIPngaA5AEnHqzwWhMRl9hU"
TELEGRAM_CHAT_ID = "1147331498"

def send_telegram_alert(message):
    """டெலிகிராம் மூலம் நேரடியாக உங்கள் சாட்டுக்கு அலர்ட் அனுப்பும் ஃபங்ஷன்"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"[{datetime.now()}] Telegram alert sent successfully!")
        else:
            print(f"[{datetime.now()}] Failed to send telegram message. Response: {response.text}")
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def fetch_intraday_data(symbol):
    # இங்கே உங்கள் புரோக்கர் API லைவ் டேட்டாவை இணைக்கலாம்
    data = {
        'Close': [1000, 1005, 1012, 1015, 1020, 1028],
        'High': [1002, 1008, 1014, 1018, 1022, 1030],
        'Low': [998, 1003, 1009, 1011, 1016, 1024],
        'Volume': [60000, 75000, 130000, 90000, 160000, 210000],
        'VWAP': [1001, 1004, 1008, 1010, 1014, 1018]
    }
    df = pd.DataFrame(data)
    return df

def calculate_extreme_indicators(df):
    # இண்டிகேட்டர்கள் கணக்கீடு (EMA, RSI, Momentum)
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Momentum'] = df['Close'] - df['Close'].shift(2)
    return df

def generate_extreme_signal(df, symbol):
    """
    எந்தச் சூழலிலும் 'HOLD' சொல்லாமல், கட்டாயமாக ஒரு சிக்னலை (BUY அல்லது SELL) வெளியேற்றும் லாஜிக்.
    """
    latest = df.iloc[-1]
    current_price = latest['Close']
    
    ema_9 = latest['EMA_9']
    ema_20 = latest['EMA_20']
    vwap = latest['VWAP']
    rsi = latest['RSI'] if not np.isnan(latest['RSI']) else 50
    momentum = latest['Momentum'] if not np.isnan(latest['Momentum']) else 1
    
    bullish_score = 0
    bearish_score = 0
    
    if current_price > vwap: bullish_score += 2
    else: bearish_score += 2
    
    if ema_9 > ema_20: bullish_score += 2
    else: bearish_score += 2
    
    if rsi > 50: bullish_score += 2
    else: bearish_score += 2
    
    if momentum > 0: bullish_score += 1
    else: bearish_score += 1

    # கட்டாய சிக்னல் முடிவு
    if bullish_score >= bearish_score:
        signal = "BUY (EXTREME LONG / CALL)"
        reason = f"Bullish Dominance ({bullish_score}/7) | Price > VWAP & Momentum"
        sl = round(current_price * 0.994, 2)  # 0.6% Stop Loss
        tgt = round(current_price * 1.012, 2) # 1.2% Target
    else:
        signal = "SELL (EXTREME SHORT / PUT)"
        reason = f"Bearish Dominance ({bearish_score}/7) | Price < VWAP & Momentum"
        sl = round(current_price * 1.006, 2)
        tgt = round(current_price * 0.988, 2)
        
    return signal, reason, current_price, sl, tgt, bullish_score, bearish_score

def analyze_and_report(symbol):
    df = fetch_intraday_data(symbol)
    df = calculate_extreme_indicators(df)
    
    signal, reason, price, sl, tgt, b_score, br_score = generate_extreme_signal(df, symbol)
    
    report_message = (
        f"🔥 *EXTREME PRO INTRADAY SIGNAL* 🔥\n"
        f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📌 *Symbol:* {symbol}\n"
        f"💰 *Execution Price:* ₹{price}\n"
        f"⚡ *Forced Signal:* *{signal}*\n"
        f"📊 *Bullish Score:* {b_score} | *Bearish Score:* {br_score}\n"
        f"🛑 *Strict Stop Loss:* ₹{sl}\n"
        f"🎯 *Pro Target:* ₹{tgt}\n"
        f"📝 *Extreme Reason:* {reason}\n"
    )
    
    send_telegram_alert(report_message)
    print(f"[{datetime.now()}] Extreme hourly signal sent for {symbol}")

def job():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    # இந்திய பங்குச்சந்தை வேலை நேரங்கள் (திங்கள் - வெள்ளி, 09:15 முதல் 15:30 வரை)
    if now.weekday() < 5:
        if "09:15" <= current_time <= "15:30":
            print("Market active. Running Extreme Analysis...")
            analyze_and_report("RELIANCE")
        else:
            print("Market closed. Waiting for trading hours...")

if __name__ == "__main__":
    print("Extreme Pro Trading Bot Initialized & Ready...")
    
    # சோதனைக்காக உடனே ஒருமுறை ரன் ஆகி உங்கள் டெலிகிராமிற்கு மெசேஜ் அனுப்பும்
    job()
    
    # சரியாக ஒவ்வொரு 1 மணி நேரத்திற்கு ஒருமுறை (3600 விநாடிகள்) ரன் ஆகும்
    while True:
        time.sleep(3600)
        job()
        
