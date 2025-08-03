# 📊 XGBoost Stock Trading Notebook Documentation

Welcome to the documentation for the Jupyter notebook **xgboost.ipynb**, which implements, visualizes, and compares both rule-based and machine learning (XGBoost) strategies for predicting next-day movement (up/down) of selected Indian stocks using technical indicators. This notebook is designed to help you explore the interplay between technical signals and modern ML models in stock trading.

---

## 🗂️ Index

1. [Overview](#overview)
2. [Data Collection & Initialization](#data-collection--initialization)
3. [Data Visualization](#data-visualization)
4. [Technical Indicator Preprocessing](#technical-indicator-preprocessing)
5. [Feature Engineering](#feature-engineering)
6. [Model Training & Backtesting](#model-training--backtesting)
    - [ML (XGBoost) Approach](#ml-xgboost-approach)
    - [Rule-Based Strategy](#rule-based-strategy)
7. [Agreement Analysis](#agreement-analysis)
8. [Evaluation Metrics](#evaluation-metrics)
9. [Trading Pipeline Flowchart](#trading-pipeline-flowchart)
10. [XGBoost Model API (Model Asset)](#xgboost-model-api-model-asset)
11. [Best Practices & Limitations](#best-practices--limitations)
12. [References](#references)

---

## 1. <a name="overview"></a>Overview

This notebook demonstrates a **quantitative trading pipeline** that answers the question:
> *Can simple technical signals be improved upon by machine learning for next-day price direction prediction?*

It does this across three large Indian stocks:
- **RELIANCE.NS** (Reliance Industries)
- **HDFCBANK.NS** (HDFC Bank)
- **INFY.NS** (Infosys)

The notebook fetches historical prices, computes technical indicators, creates trading signals, and compares a rule-based trading approach with an XGBoost classifier, then assesses where they agree (consensus signals).

---

## 2. <a name="data-collection--initialization"></a>Data Collection & Initialization

### Key Steps:

- **Imports**: yfinance, pandas, numpy, matplotlib, seaborn, plotly, scikit-learn, ta (technical analysis), xgboost, and utility modules.
- **Stock Selection**:
    ```python
    symbols = ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS"]
    ```
- **Fetching Metadata**:
    - Loops through each symbol, downloads metadata (name, market, sector), and prints it.
    - Uses yfinance `Ticker.info`.

**Example Output:**
```
Symbol: RELIANCE.NS
Name: RELIANCE INDUSTRIES LTD
Market: in_market
Sector: Energy
------------------------------
```

---

## 3. <a name="data-visualization"></a>Data Visualization

- **Price & Volume Chart**: For each symbol, fetches 5 years of historical OHLCV data and plots **Close price** and **Volume** on dual y-axes.
- **Tabular Preview**: Displays the first and last 5 rows for a 6-month window.

**Visualization Example:**

- The plot shows the evolution of price and volume, highlighting regime changes, trends, and volatility.

---

## 4. <a name="technical-indicator-preprocessing"></a>Technical Indicator Preprocessing

**For each stock, the notebook computes:**
- **RSI (14 days)**
- **MACD** and **MACD Signal**
- **SMA 20, SMA 50**
- **EMA 20**
- **Volatility**: 10-day rolling std of Close
- **Buy_Signal**: (RSI < 35) and (SMA_20 > SMA_50)
- **Target**: Next-day close > today’s close (binary classification)

**Returns a DataFrame with these features and signals.**

---

## 5. <a name="feature-engineering"></a>Feature Engineering

- **Feature Set**:
    - RSI, MACD, MACD_Signal, SMA_20, EMA_20, Volatility
- **Target**:
    - Next-day price movement (binary: 1 = up, 0 = down)
- **Rule-based Logic**:
    - Buy signal when RSI < 35 **and** SMA_20 > SMA_50

---

## 6. <a name="model-training--backtesting"></a>Model Training & Backtesting

### <a name="ml-xgboost-approach"></a>ML (XGBoost) Approach

- **Train/Test Split**:
    - **Train**: All data before 1 Feb 2025
    - **Test**: 1 Feb 2025 – 31 Jul 2025
- **Searches best XGBoost hyperparameters** via **TimeSeriesSplit** and precision scoring.
- **Metrics**: Accuracy, Precision, Recall, F1, Confusion Matrix.

**Example Output:**
```
Best Parameters: {'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 50}
Accuracy: 48.36%
Precision: 48.98%
Recall: 78.69%
F1-Score: 60.38%
```
- **Confusion Matrix**: Plotted for each stock.

### <a name="rule-based-strategy"></a>Rule-Based Strategy

- **Simulates trading** whenever the logic signal is True.
- **Trade_Return**: (next day's close – today’s close) / today’s close – 0.1% (transaction cost)
- **Performance metrics**: total trades, win ratio, average profit/loss, cumulative return.
- **Cumulative return plot**: Shows compounding of rule-based trades.

---

## 7. <a name="agreement-analysis"></a>Agreement Analysis

- **Consensus trades**: Days when both the ML model **and** the rule-based logic say 'buy'.
- **Agreement Metrics**:
    - Total agreement trades
    - Profitable agreement trades
    - Win ratio
    - Average return
    - Cumulative return plot for agreement-only trades

---

## 8. <a name="evaluation-metrics"></a>Evaluation Metrics

| Metric           | Description                                           |
|------------------|------------------------------------------------------|
| Accuracy         | Correct predictions / total predictions               |
| Precision        | Correct “up” predictions / all “up” predictions       |
| Recall           | Correct “up” predictions / all actual “up” instances  |
| F1-Score         | Harmonic mean of precision and recall                 |
| Win Ratio        | Profitable trades / total trades                      |
| Avg Profit/Loss  | Average % gain/loss per trade                         |
| Cumulative Return| Compound return from following the strategy           |

---

## 9. <a name="trading-pipeline-flowchart"></a>Trading Pipeline Flowchart

**Below is a diagram showing the pipeline from data preprocessing to trade execution.**

```mermaid
flowchart TD
    A[Raw Stock Price Data] --> B[Technical Indicator Calculation]
    B --> C[Feature Engineering]
    C --> D1[ML Model (XGBoost) Prediction]
    C --> D2[Rule-Based Logic Signal]
    D1 --> E[Signal Agreement Analysis]
    D2 --> E
    E --> F{Consensus?}
    F -- Yes --> G[Simulated Trade (Agreement)]
    F -- No --> H[No Trade]
    G --> I[Backtest Performance Metrics]
    H --> I
```

---

## 10. <a name="xgboost-model-api-model-asset"></a>XGBoost Model API (Model Asset)

For each stock, the trained XGBoost model is saved as a JSON asset (e.g., `INFY_model.json`). To use the model, load and call `predict()` with the 6-feature input.

```api
{
    "title": "Stock Direction Prediction (XGBoost Model)",
    "description": "Predicts next-day price direction (up/down) based on technical indicators.",
    "method": "POST",
    "baseUrl": "http://localhost:8501",
    "endpoint": "/predict",
    "headers": [
        {
            "key": "Content-Type",
            "value": "application/json",
            "required": true
        }
    ],
    "bodyType": "json",
    "requestBody": "{\n  \"RSI\": 31.27,\n  \"MACD\": -5.33,\n  \"MACD_Signal\": -4.21,\n  \"SMA_20\": 1567.32,\n  \"EMA_20\": 1571.88,\n  \"Volatility\": 11.09\n}",
    "responses": {
        "200": {
            "description": "Prediction result",
            "body": "{\n  \"prediction\": 0\n}"
        }
    }
}
```
*Here, 0 = down, 1 = up.*

---

## 11. <a name="best-practices--limitations"></a>Best Practices & Limitations

### Best Practices
- **Always use a strictly out-of-sample backtest period.**
- **Tune ML model hyperparameters using time-series cross-validation.**
- **Incorporate transaction costs in backtests.**
- **Compare ML with simple rules to avoid overfitting hype.**

### Limitations
- **No risk management:** Position sizing, stop-losses, and slippage not modeled.
- **No walk-forward retraining:** Models are not retrained during backtest.
- **No feature selection or ensembling:** Only basic technicals used.
- **No capital constraints or realistic brokerage simulation.**
- **Small sample in backtest window may not generalize.**

---

## 12. <a name="references"></a>References

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [TA-Lib & Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/en/latest/)
- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [Scikit-learn Metrics](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [Investopedia: RSI, MACD, SMA](https://www.investopedia.com/)

---

## 📝 Summary Table

| Stock         | ML Model Accuracy | Rule-Based Win Ratio | Agreement Trades | Agreement Win Ratio |
| ------------- | ---------------- | -------------------- | ---------------- | ------------------ |
| INFY.NS       | 48.36%           | 0.00%                | 2                | 0.00%              |
| RELIANCE.NS   | 50.82%           | 40.00%               | 3                | 33.33%             |
| HDFCBANK.NS   | 45.90%           | 0.00%                | 0                | 0.00%              |

---

## 📌 Key Takeaways

- **Both ML (XGBoost) and simple logic are very noisy for next-day direction, even when tuned and filtered.**
- **"Agreement" (consensus) trades are rare and not consistently profitable (in this test window).**
- **Visualization shows the signals are sparse and gains are often offset by losses, especially with transaction costs.**
- **Despite the power of ML, overfitting and limited predictability in short-term price movement remain major challenges.**

---

**This notebook provides a full, reproducible pipeline for technical trading ML research, and exposes the reality of predictive edge in liquid stocks. Feel free to use it as a base for deeper studies, adding more features, or more realistic trading simulation!**
