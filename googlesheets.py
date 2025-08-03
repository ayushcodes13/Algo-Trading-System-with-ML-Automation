import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import warnings
warnings.filterwarnings("ignore")

# Configuration
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'  # Replace with your Google Sheet ID
CREDENTIALS_FILE = 'stockbot-credentials.json'  # Path to your credentials JSON
SHEET_NAME = 'Sheet1'  # Adjust if your sheet has a different name
RANGE_NAME = f'{SHEET_NAME}!A1'

# Define backtest period (timezone-aware)
backtest_start = pd.to_datetime("2025-02-01", utc=True).tz_convert("Asia/Kolkata")
backtest_end = pd.to_datetime("2025-07-31", utc=True).tz_convert("Asia/Kolkata")

# Initialize Google Sheets API
def init_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    return sheet

# Append data to Google Sheet
def append_to_google_sheet(sheet, symbol, data):
    # Define headers
    headers = ['Date', 'Symbol', 'Close Price', 'RSI', 'MACD', 'SMA_20', 'EMA_20', 'Volatility', 'Trade Return']
    
    # Check if sheet is empty; if so, add headers
    if not sheet.get_all_values():
        sheet.append_row(headers)
    
    # Prepare data rows
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
    
    # Append data to sheet
    sheet.append_rows(values)
    print(f"Appended {len(values)} trades for {symbol} to Google Sheet")

# Agreement analysis with Google Sheets integration
def agreement_analysis_with_gsheets(processed_data, symbol, model_file):
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
    
    # Append to Google Sheet if trades exist
    if total_agreed > 0:
        sheet = init_google_sheets()
        append_to_google_sheet(sheet, symbol, df_agreed)
    
    # Save results to CSV (as in original code)
    df_agreed.to_csv(f"{symbol}_agreement_trades.csv")
    return df_agreed

# Run agreement analysis for all stocks
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
        agreement_analysis_with_gsheets(processed_data_dict[symbol], symbol, model_files[symbol])
    else:
        print(f"Error: Processed data for {symbol} not found.")