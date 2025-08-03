import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
warnings.filterwarnings("ignore")

# Initialize Google Sheets client
def init_gsheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("AlgoTradingResults")  # Create or open spreadsheet
        return spreadsheet
    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")
        return None

# Log trade data to Google Sheets
def log_to_gsheets(spreadsheet, symbol, rule_df, agreed_df):
    try:
        # Worksheet for trade log
        try:
            ws_trade = spreadsheet.worksheet(f"{symbol}_Trades")
        except:
            ws_trade = spreadsheet.add_worksheet(title=f"{symbol}_Trades", rows=1000, cols=10)
        
        # Prepare trade log (rule-based and agreement trades)
        trade_data = rule_df[["Close", "Buy_Signal", "Trade_Return"]].copy()
        trade_data["Strategy"] = "Rule-Based"
        if agreed_df is not None and len(agreed_df) > 0:
            agreed_data = agreed_df[["Close", "Buy_Signal", "Trade_Return"]].copy()
            agreed_data["Strategy"] = "Agreement"
            trade_data = pd.concat([trade_data, agreed_data])
        
        trade_data.reset_index(inplace=True)
        trade_data["Trade_Return"] = trade_data["Trade_Return"].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "")
        ws_trade.update([trade_data.columns.values.tolist()] + trade_data.values.tolist())
        
        # Worksheet for summary P&L and win ratio
        try:
            ws_summary = spreadsheet.worksheet(f"{symbol}_Summary")
        except:
            ws_summary = spreadsheet.add_worksheet(title=f"{symbol}_Summary", rows=10, cols=5)
        
        # Calculate summary metrics
        summary_data = []
        if len(rule_df) > 0:
            total_trades_rule = len(rule_df)
            profitable_trades_rule = (rule_df["Trade_Return"] > 0).sum()
            win_ratio_rule = profitable_trades_rule / total_trades_rule if total_trades_rule > 0 else 0
            cumulative_return_rule = (1 + rule_df["Trade_Return"]).prod() - 1
            summary_data.append(["Rule-Based", total_trades_rule, f"{win_ratio_rule:.2%}", f"{cumulative_return_rule:.2%}"])
        
        if agreed_df is not None and len(agreed_df) > 0:
            total_trades_agreed = len(agreed_df)
            profitable_trades_agreed = (agreed_df["Trade_Return"] > 0).sum()
            win_ratio_agreed = profitable_trades_agreed / total_trades_agreed if total_trades_agreed > 0 else 0
            cumulative_return_agreed = (1 + agreed_df["Trade_Return"]).prod() - 1
            summary_data.append(["Agreement", total_trades_agreed, f"{win_ratio_agreed:.2%}", f"{cumulative_return_agreed:.2%}"])
        
        summary_df = pd.DataFrame(summary_data, columns=["Strategy", "Total Trades", "Win Ratio", "Cumulative Return"])
        ws_summary.update([summary_df.columns.values.tolist()] + summary_df.values.tolist())
        
        print(f"Logged data for {symbol} to Google Sheets")
    except Exception as e:
        print(f"Error logging to Google Sheets for {symbol}: {e}")

# Main function to log results for all stocks
def log_all_to_gsheets():
    spreadsheet = init_gsheets()
    if spreadsheet is None:
        return
    
    for symbol, rule_df, agreed_df in [
        ("INFY.NS", infy_rule_df, infy_agreed_df),
        ("RELIANCE.NS", reliance_rule_df, reliance_agreed_df),
        ("HDFCBANK.NS", hdfcbank_rule_df, hdfcbank_agreed_df)
    ]:
        if rule_df is not None:
            log_to_gsheets(spreadsheet, symbol, rule_df, agreed_df)
        else:
            print(f"Skipping {symbol}: No rule-based data available")

# Run Google Sheets logging
log_all_to_gsheets()
