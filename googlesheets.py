import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import warnings
from xgboost.ipynb import processed_infy, processed_reliance, processed_hdfcbank  # Assuming these are preprocessed DataFrames
from googleapiclient.discovery import build
from google.oauth2 import service_account
import requests
import json

warnings.filterwarnings("ignore")

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'  # Replace with your Google Sheet ID
RANGE_NAME = 'Sheet1!A1'  # Adjust sheet name and range as needed
CREDENTIALS_FILE = 'credentials.json'  # Path to your Google API credentials JSON

# Telegram setup
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your Telegram bot token
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'  # Replace with your Telegram chat ID

# Define backtest period (timezone-aware)
backtest_start = pd.to_datetime("2025-02-01", utc=True).tz_convert("Asia/Kolkata")
backtest_end = pd.to_datetime("2025-07-31", utc=True).tz_convert("Asia/Kolkata")

# Initialize Google Sheets API
def init_google_sheets():
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

# Append data to Google Sheet
def append_to_google_sheet(spreadsheets, symbol, data):
    headers = ['Date', 'Symbol', 'Close Price', 'RSI', 'MACD', 'SMA_20', 'EMA_20', 'Volatility', 'Trade Return']
    values = [headers] if not spreadsheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute().get('values') else []
    
    for index, row in data.iterrows():
        values.append([
            index.strftime('%Y-%m-%d %H:%M:%S%z'),
            symbol,
            row['Close'],
            row['RSI'],
            row['MACD'],
            row['SMA_20'],
            row['EMA_20'],
            row['Volatility'],
            row['Trade_Return']
        ])
    
    body = {'values': values}
    spreadsheets.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"Appended {len(data)} trades for {symbol} to Google Sheet")

# Send Telegram notification
def send_telegram_message(symbol, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for index, row in data.iterrows():
        message = (
            f"🚨 Trade Signal for {symbol}\n"
            f"Date: {index.strftime('%Y-%m-%d %H:%M:%S%z')}\n"
            f"Close Price: {row['Close']:.2f} INR\n"
            f"Trade Return: {row['Trade_Return']*100:.2f}%\n"
            f"RSI: {row['RSI']:.2f}\n"
            f"MACD: {row['MACD']:.2f}\n"
            f"SMA_20: {row['SMA_20']:.2f}\n"
            f"EMA_20: {row['EMA_20']:.2f}\n"
            f"Volatility: {row['Volatility']:.2f}"
        )
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Sent Telegram notification for {symbol} trade on {index.strftime('%Y-%m-%d')}")
        else:
            print(f"Failed to send Telegram notification for {symbol}: {response.text}")

# Modified agreement analysis to include Google Sheets and Telegram
def agreement_analysis_with_notifications(processed_data, symbol, model_file):
    print(f"\n=== Agreement Analysis for {symbol} ===")
    
    # Filter for backtest period
    test = processed_data[(processed_data.index >= backtest_start) & (processed_data.index <= backtest_end)]
    
    if len(test) == 0:
        print(f"Error: No data available for {symbol} in backtest period.")
        return None
    
    print(f"Test data points: {len(test)}")
    
    # Load ML model
    try:
        model = XGBClassifier()
        model.load_model(model_file)
        print(f"Loaded ML model for {symbol}")
    except:
        print(f"Error: ML model for {symbol} not found. Run training first.")
        return None
    
    # Generate ML predictions
    features = ["RSI", "MACD", "MACD_Signal", "SMA_20", "EMA_20", "Volatility"]
    test["ML_Prediction"] = model.predict(test[features])
    
    # Agreement trades (ML and rule-based both say yes)
    df_agreed = test[(test["ML_Prediction"] == 1) & (test["Buy_Signal"] == 1)].copy()
    df_agreed["Trade_Return"] = ((df_agreed["Close"].shift(-1) - df_agreed["Close"]) / 
                                 df_agreed["Close"] - 0.001)  # 0.1% transaction cost
    df_agreed = df_agreed.dropna(subset=["Trade_Return"])
    
    # Agreement metrics
    total_agreed = len(df_agreed)
    profitable_agreed = (df_agreed["Trade_Return"] > 0).sum()
    win_ratio_agreed = profitable_agreed / total_agreed if total_agreed > 0 else 0
    avg_return_agreed = df_agreed["Trade_Return"].mean() if total_agreed > 0 else 0
    
    print("\n=== Agreement Trade Details (ML and Rule-Based Both Yes) ===")
    print(f"Total Agreement Trades: {total_agreed}")
    print(f"Profitable Trades: {profitable_agreed}")
    print(f"Win Ratio: {win_ratio_agreed:.2%}")
    print(f"Avg Return: {avg_return_agreed:.2%}")
    
    # Plot cumulative returns
    if total_agreed > 0:
        plt.figure(figsize=(10, 5))
        plt.plot(df_agreed.index, (1 + df_agreed["Trade_Return"]).cumprod(),
                 label="Agreement Strategy", color="blue")
        plt.title(f"Agreement Strategy Cumulative Returns - {symbol} (Feb-Jul 2025)")
        plt.xlabel("Date")
        plt.ylabel("Growth")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"{symbol}_agreement_returns.png", dpi=300, bbox_inches='tight')
        plt.show()
    
    # Google Sheets and Telegram integration
    if total_agreed > 0:
        spreadsheets = init_google_sheets()
        append_to_google_sheet(spreadsheets, symbol, df_agreed)
        send_telegram_message(symbol, df_agreed)
    
    # Save results
    df_agreed.to_csv(f"{symbol}_agreement_trades.csv")
    return df_agreed

# Run agreement analysis with notifications for all stocks
symbols = ["INFY.NS", "RELIANCE.NS", "HDFCBANK.NS"]
model_files = {
    "INFY.NS": "INFY_model.json",
    "RELIANCE.NS": "RELIANCE_model.json",
    "HDFCBANK.NS": "HDFCBANK_model.json"
}
processed_data_dict = {
    "INFY.NS": processed_infy,
    "RELIANCE.NS": processed_reliance,
    "HDFCBANK.NS": processed_hdfcbank
}

for symbol in symbols:
    if processed_data_dict.get(symbol) is not None:
        agreement_analysis_with_notifications(processed_data_dict[symbol], symbol, model_files[symbol])
    else:
        print(f"Error: Processed data for {symbol} not found.")