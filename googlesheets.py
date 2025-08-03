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
SPREADSHEET_ID = '1Odtz9zgIV2kHyymcCZgN-kZHjxYCnSeQwSqMYgfgIBw'
CREDENTIALS_FILE = 'credentials.json'
SYMBOLS = ["INFY.NS", "RELIANCE.NS", "HDFCBANK.NS"]
PERIOD = "5y"
MODEL_FILES = {
    "INFY.NS": "Stats/ML Trained/INFY_model.json",
    "RELIANCE.NS": "Stats/ML Trained/RELIANCE_model.json",
    "HDFCBANK.NS": "Stats/ML Trained/HDFCBANK_model.json"
}
TABS = {
    'trade_log': 'Trade Log',
    'summary_pnl': 'Summary P&L',
    'win_ratio': 'Win Ratio'
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
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet

# Create or get worksheet
def get_or_create_worksheet(spreadsheet, tab_name):
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=100, cols=20)
    return worksheet

# Append trade log to Google Sheet
def append_trade_log(sheet, symbol, data):
    headers = ['Date', 'Symbol', 'Close Price', 'RSI', 'MACD', 'SMA_20', 'EMA_20', 'Volatility', 'Trade Return']
    if not sheet.get_all_values():
        sheet.append_row(headers)
    
    values = []
    for index, row in data.iterrows():
        values.append([
            index.strftime('%Y-%m-%d %H:%M:%S%z'),
            symbol,
            float(row['Close']),  # Ensure float for JSON serialization
            float(row['RSI']),
            float(row['MACD']),
            float(row['SMA_20']),
            float(row['EMA_20']),
            float(row['Volatility']),
            float(row['Trade_Return'])
        ])
    
    sheet.append_rows(values)
    print(f"Appended {len(values)} trades for {symbol} to Trade Log")

# Append summary P&L to Google Sheet
def append_summary_pnl(sheet, symbol, total_trades, total_pnl, avg_return):
    headers = ['Symbol', 'Total Trades', 'Total P&L', 'Average Return']
    if not sheet.get_all_values():
        sheet.append_row(headers)
    
    values = [[symbol, int(total_trades), float(total_pnl), float(avg_return)]]
    sheet.append_rows(values)
    print(f"Appended P&L summary for {symbol} to Summary P&L")

# Append win ratio to Google Sheet
def append_win_ratio(sheet, symbol, profitable_trades, total_trades, win_ratio):
    headers = ['Symbol', 'Profitable Trades', 'Total Trades', 'Win Ratio']
    if not sheet.get_all_values():
        sheet.append_row(headers)
    
    values = [[symbol, int(profitable_trades), int(total_trades), f"{win_ratio:.2%}"]]
    sheet.append_rows(values)
    print(f"Appended win ratio for {symbol} to Win Ratio")

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
    
    total_trades = len(df_agreed)
    profitable_trades = (df_agreed["Trade_Return"] > 0).sum()
    win_ratio = profitable_trades / total_trades if total_trades > 0 else 0
    total_pnl = df_agreed["Trade_Return"].sum() if total_trades > 0 else 0
    avg_return = df_agreed["Trade_Return"].mean() if total_trades > 0 else 0
    
    print("\n=== Agreement Trade Details (ML and Rule-Based Both Yes) ===")
    print(f"Total Agreement Trades: {total_trades}")
    print(f"Profitable Trades: {profitable_trades}")
    print(f"Win Ratio: {win_ratio:.2%}")
    print(f"Total P&L: {total_pnl:.2%}")
    print(f"Average Return: {avg_return:.2%}")
    
    if total_trades > 0:
        spreadsheet = init_google_sheets()
        trade_log_sheet = get_or_create_worksheet(spreadsheet, TABS['trade_log'])
        summary_pnl_sheet = get_or_create_worksheet(spreadsheet, TABS['summary_pnl'])
        win_ratio_sheet = get_or_create_worksheet(spreadsheet, TABS['win_ratio'])
        
        append_trade_log(trade_log_sheet, symbol, df_agreed)
        append_summary_pnl(summary_pnl_sheet, symbol, total_trades, total_pnl, avg_return)
        append_win_ratio(win_ratio_sheet, symbol, profitable_trades, total_trades, win_ratio)
    
    df_agreed.to_csv(f"{symbol}_agreement_trades.csv")
    return df_agreed

# Run agreement analysis for all stocks
for symbol in SYMBOLS:
    if symbol in processed_data_dict:
        agreement_analysis_with_gsheets(processed_data_dict[symbol], symbol, MODEL_FILES[symbol])
    else:
        print(f"Error: Processed data for {symbol} not found.")