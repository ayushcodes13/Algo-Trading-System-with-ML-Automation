import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from xgboost import XGBClassifier
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import warnings
warnings.filterwarnings("ignore")

# Configuration
SPREADSHEET_ID = '1Odtz9zgIV2kHyymcCZgN-kZHjxYCnSeQwSqMYgfgIBw'  # Replace with your Google Sheet ID
CREDENTIALS_FILE = 'credentials.json'  # Path to your credentials JSON
SHEET_NAME = 'Sheet1'  # Adjust if your sheet has a different name
RANGE_NAME = f'{SHEET_NAME}!A1'
SYMBOLS = ["INFY.NS", "RELIANCE.NS", "HDFCBANK.NS"]
PERIOD = "5y"
MODEL_FILES = {
    "INFY.NS": "Stats/ML Trained/INFY_model.json",
    "RELIANCE.NS": "Stats/ML Trained/RELIANCE_model.json",
    "HDFCBANK.NS": "Stats/ML Trained/HDFCBANK_model.json"
}

# Define backtest period (timezone-aware)
backtest_start = pd.to_datetime("2025-02-01", utc=True).tz_convert("Asia/Kolkata")
backtest_end = pd.to_datetime("2025-07-31", utc=True).tz_convert("Asia/Kolkata")

# Preprocessing function
def preprocess_stock(df, rsi_threshold=35):
    df = df.copy()
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
    df["MACD"] = MACD(df["Close"]).macd()
    df["MACD_Signal"] = MACD(df["Close"]).macd_signal()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["Volatility"] = df["Close"].rolling(window=10).std()
    df["Buy_Signal"] = ((df["RSI"] < rsi_threshold) & (df["SMA_20"] > df["SMA_50"])).astype(int)
    df["Logic_Signal"] = df["Buy_Signal"]
    df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    df.index = pd.to_datetime(df.index).tz_convert("Asia/Kolkata")
    return df.dropna()

# Fetch and preprocess data
processed_data_dict = {}
for symbol in SYMBOLS:
    print(f"\nFetching data for {symbol}")
    data = yf.Ticker(symbol).history(period=PERIOD)
    if data.empty:
        print(f"Error: No data retrieved for {symbol}")
        continue
    processed_data = preprocess_stock(data)
    processed_data_dict[symbol] = processed_data
    print(f"Processed data for {symbol}: {len(processed_data)} rows")
    print(f"Data from {processed_data.index.min()} to {processed_data.index.max()}")
    print(f"Index timezone: {processed_data.index.tz}")

# Initialize Google Sheets API
def init_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    return sheet

# Append data to Google Sheet
def append_to_google_sheet(sheet, symbol, data):
    headers = ['Date', 'Symbol', 'Close Price', 'RSI', 'MACD', 'SMA_20', 'EMA_20', 'Volatility', 'Trade Return']
    if not sheet.get_all_values():
        sheet.append_row(headers)
    
    values = []
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
    
    sheet.append_rows(values)
    print(f"Appended {len(values)} trades for {symbol} to Google Sheet")

# Agreement analysis with Google Sheets integration
def agreement_analysis_with_gsheets(processed_data, symbol, model_file):
    print(f"\n=== Agreement Analysis for {symbol} ===")
    
    test = processed_data[(processed_data.index >= backtest_start) & (processed_data.index <= backtest_end)]
    
    if len(test) == 0:
        print(f"Error: No data available for {symbol} in backtest period.")
        return None
    
    print(f"Test data points: {len(test)}")
    
    try:
        model = XGBClassifier()
        model.load_model(model_file)
        print(f"Loaded ML model for {symbol}")
    except:
        print(f"Error: ML model for {symbol} not found. Run training first.")
        return None
    
    features = ["RSI", "MACD", "MACD_Signal", "SMA_20", "EMA_20", "Volatility"]
    test["ML_Prediction"] = model.predict(test[features])
    
    df_agreed = test[(test["ML_Prediction"] == 1) & (test["Buy_Signal"] == 1)].copy()
    df_agreed["Trade_Return"] = ((df_agreed["Close"].shift(-1) - df_agreed["Close"]) / 
                                df_agreed["Close"] - 0.001)
    df_agreed = df_agreed.dropna(subset=["Trade_Return"])
    
    total_agreed = len(df_agreed)
    profitable_agreed = (df_agreed["Trade_Return"] > 0).sum()
    win_ratio_agreed = profitable_agreed / total_agreed if total_agreed > 0 else 0
    avg_return_agreed = df_agreed["Trade_Return"].mean() if total_agreed > 0 else 0
    
    print("\n=== Agreement Trade Details (ML and Rule-Based Both Yes) ===")
    print(f"Total Agreement Trades: {total_agreed}")
    print(f"Profitable Trades: {profitable_agreed}")
    print(f"Win Ratio: {win_ratio_agreed:.2%}")
    print(f"Avg Return: {avg_return_agreed:.2%}")
    
    if total_agreed > 0:
        sheet = init_google_sheets()
        append_to_google_sheet(sheet, symbol, df_agreed)
    
    df_agreed.to_csv(f"{symbol}_agreement_trades.csv")
    return df_agreed

# Run agreement analysis for all stocks
for symbol in SYMBOLS:
    if symbol in processed_data_dict:
        agreement_analysis_with_gsheets(processed_data_dict[symbol], symbol, MODEL_FILES[symbol])
    else:
        print(f"Error: Processed data for {symbol} not found.")