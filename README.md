# TradeSync-ML-vs-Rule-Based-Trading-System

Overview
This project automates the generation and logging of stock trading signals for three Indian stocks (INFY.NS, RELIANCE.NS, HDFCBANK.NS) using a combination of machine learning (XGBoost) and rule-based strategies. The script fetches historical stock data, processes technical indicators, identifies agreement trades (where ML and rule-based signals align), and logs results to a Google Sheet with three tabs: Trade Log, Summary P&L, and Win Ratio. The project is designed for backtesting over a specified period (February 1, 2025, to July 31, 2025) and is intended for use in a financial analysis or internship presentation context.
Features

Data Fetching: Retrieves 5 years of historical stock data using yfinance for INFY.NS, RELIANCE.NS, and HDFCBANK.NS.
Technical Indicators: Calculates RSI, MACD, SMA (20, 50), EMA (20), and Volatility for signal generation.
Trading Signals: Combines rule-based signals (RSI < 35, SMA_20 > SMA_50) with ML predictions (XGBoost models).
Google Sheets Automation:
Trade Log: Logs detailed trade signals (Date, Symbol, Close Price, RSI, MACD, SMA_20, EMA_20, Volatility, Trade Return).
Summary P&L: Logs per-stock metrics (Symbol, Total Trades, Total P&L, Average Return).
Win Ratio: Logs per-stock win metrics (Symbol, Profitable Trades, Total Trades, Win Ratio).


Output: Saves agreement trades to CSV files (e.g., INFY.NS_agreement_trades.csv) and logs metrics to the console.

Prerequisites

Python 3.10+
Dependencies: Install via pip install gspread oauth2client pandas numpy yfinance ta xgboost
Google Cloud Setup:
Enable the Google Sheets API in your Google Cloud project (Google Cloud Console).
Create a service account and download the JSON key file as credentials.json.
Share the target Google Sheet (https://docs.google.com/spreadsheets/d/1Odtz9zgIV2kHyymcCZgN-kZHjxYCnSeQwSqMYgfgIBw) with the service account’s client_email (Editor permissions).


Model Files: Pre-trained XGBoost models in /Stats/ML Trained/:
INFY_model.json
RELIANCE_model.json
HDFCBANK_model.json


Directory Structure:Stock market project/
├── googlesheets.py
├── credentials.json
├── Stats/
│   └── ML Trained/
│       ├── INFY_model.json
│       ├── RELIANCE_model.json
│       └── HDFCBANK_model.json
├── INFY.NS_agreement_trades.csv (output)
├── RELIANCE.NS_agreement_trades.csv (output)
└── output.txt (console output)



Setup

Clone or Download:
Place googlesheets.py in /Users/your_username/Desktop/Stock market project/.


Install Dependencies:pip install gspread oauth2client pandas numpy yfinance ta xgboost


Set Up Google Sheets:
Ensure the Google Sheet (https://docs.google.com/spreadsheets/d/1Odtz9zgIV2kHyymcCZgN-kZHjxYCnSeQwSqMYgfgIBw) is shared with the client_email from credentials.json.
Verify the Google Sheets API is enabled in your Google Cloud project (ID: 207754761869).


Prepare Model Files:
Ensure XGBoost model files are in /Stats/ML Trained/. If missing, train models using your training script and save them:infy_model.save_model("Stats/ML Trained/INFY_model.json")
reliance_model.save_model("Stats/ML Trained/RELIANCE_model.json")
hdfcbank_model.save_model("Stats/ML Trained/HDFCBANK_model.json")




Activate Virtual Environment (if using):source "/Users/your_username/Desktop/Stock market project/venv/bin/activate"



Usage

Run the Script:"/Users/your_username/Desktop/Stock market project/venv/bin/python" "/Users/your_username/Desktop/Stock market project/googlesheets.py" > output.txt


Output:
Console: Displays data fetching, preprocessing, and agreement analysis metrics (e.g., Total Trades, Win Ratio, Total P&L, Average Return).
Google Sheet: Populates three tabs:
Trade Log: Detailed trade signals (e.g., 2 trades for INFY.NS, 3 for RELIANCE.NS).
Summary P&L: Per-stock P&L metrics (e.g., INFY.NS: -0.33% total P&L, RELIANCE.NS: 19.30% total P&L).
Win Ratio: Per-stock win metrics (e.g., INFY.NS: 0/2, 0%; RELIANCE.NS: 1/3, 33.33%).


CSV Files: Saves trade details to INFY.NS_agreement_trades.csv and RELIANCE.NS_agreement_trades.csv.


Clear Google Sheet Tabs (optional, to avoid duplicates):
Delete or clear Trade Log, Summary P&L, and Win Ratio tabs before rerunning to start fresh.



Sample Output

Console Output (saved to output.txt):Fetching data for INFY.NS
Processed data for INFY.NS: 1191 rows
Data from 2020-10-12 00:00:00+05:30 to 2025-08-01 00:00:00+05:30
...
=== Agreement Analysis for INFY.NS ===
Total Agreement Trades: 2
Profitable Trades: 0
Win Ratio: 0.00%
Total P&L: -0.33%
Average Return: -0.17%
Appended 2 trades for INFY.NS to Trade Log
Appended P&L summary for INFY.NS to Summary P&L
Appended win ratio for INFY.NS to Win Ratio
...
=== Agreement Analysis for RELIANCE.NS ===
Total Agreement Trades: 3
Profitable Trades: 1
Win Ratio: 33.33%
Total P&L: 19.30%
Average Return: 6.43%
...
=== Agreement Analysis for HDFCBANK.NS ===
Total Agreement Trades: 0
Profitable Trades: 0
Win Ratio: 0.00%
Total P&L: 0.00%


Google Sheet (https://docs.google.com/spreadsheets/d/1Odtz9zgIV2kHyymcCZgN-kZHjxYCnSeQwSqMYgfgIBw):
Trade Log:Date,Symbol,Close Price,RSI,MACD,SMA_20,EMA_20,Volatility,Trade Return
2025-07-25 00:00:00+0530,INFY.NS,1515.699951,32.41530826,-11.68512472,1595.995001,1583.630166,24.72885802,-0.0008020394288
2025-07-28 00:00:00+0530,INFY.NS,1516,32.516792,-15.45198857,1591.704999,1577.189198,30.6678026,-0.002517182604
2025-04-07 00:00:00+0530,RELIANCE.NS,1165.699951,31.04122502,-3.849582624,1252.377496,1241.519657,40.77167865,0.2109757296
2025-07-22 00:00:00+0530,RELIANCE.NS,1412.800049,32.10038514,-2.034868081,1496.495007,1476.586946,33.92219675,-0.01593494969
2025-07-25 00:00:00+0530,RELIANCE.NS,1391.699951,30.41672261,-14.49091179,1483.554999,1458.100057,38.04836209,-0.002077818533


Summary P&L:Symbol,Total Trades,Total P&L,Average Return
INFY.NS,2,-0.0033192220328,-0.0016596110164
RELIANCE.NS,3,0.1929629614,0.06432098713
HDFCBANK.NS,0,0.0,0.0


Win Ratio:Symbol,Profitable Trades,Total Trades,Win Ratio
INFY.NS,0,2,0.00%
RELIANCE.NS,1,3,33.33%
HDFCBANK.NS,0,0,0.00%





Troubleshooting

TypeError: int64 not JSON serializable:
Resolved by converting int64 values to Python int in append_win_ratio.
If persists, check other numeric fields and convert to float or int.


PermissionError:
Ensure the Google Sheet is shared with the client_email from credentials.json.
Verify the Google Sheets API is enabled in the Google Cloud project (ID: 207754761869).


Model Not Found:
Confirm model files exist in /Stats/ML Trained/. Regenerate using your training script if missing.


No Data Fetched:
Test yfinance:import yfinance as yf
print(yf.Ticker("INFY.NS").history(period="5y").head())


Ensure internet connectivity and correct symbols (INFY.NS, not INFY).


No Trades for HDFCBANK.NS:
Expected (0 trades). To generate trades, adjust rsi_threshold in preprocess_stock (e.g., rsi_threshold=40).



Notes

Security: Keep credentials.json private. Share the Google Sheet as Viewer for submission.
Duplicates: Clear Google Sheet tabs before rerunning to avoid duplicate rows.
Assignment Context: Designed for an internship presentation, demonstrating automated trade signal logging to Google Sheets with detailed metrics.

Author

Devayush Rout
Created: August 2025
Purpose: Internship project for stock trading signal automation
