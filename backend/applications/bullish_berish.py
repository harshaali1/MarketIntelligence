from flask import Flask, request
from flask_restful import Api, Resource
from flask_cors import CORS 
import yfinance as yf
import pandas as pd
import traceback

# -------------------------------
# CONFIG
# -------------------------------
OBV_LOOKBACK = 20
RSI_PERIOD = 14

# -------------------------------
# TECHNICAL ANALYZER CLASS
# -------------------------------
class TechnicalAnalyzer:
    """Fetches stock data, calculates RSI & OBV, returns simple signal."""

    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.data = None

    def fetch_data(self):
        # Fetch data for 1 year
        df = yf.download(self.ticker, period="1y", progress=False, auto_adjust=False)
        if df.empty:
            raise ValueError(f"Could not fetch data for ticker: {self.ticker}")

        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Keep only necessary columns
        if 'Close' not in df.columns or 'Volume' not in df.columns:
            raise ValueError(f"'Close' or 'Volume' column missing for {self.ticker}")

        self.data = df[['Close', 'Volume']].dropna()

    def calculate_rsi(self):
        delta = self.data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(RSI_PERIOD).mean()
        avg_loss = loss.rolling(RSI_PERIOD).mean()
        rs = avg_gain / avg_loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def calculate_obv_change(self):
        obv = [0]
        for i in range(1, len(self.data)):
            if self.data['Close'].iloc[i] > self.data['Close'].iloc[i-1]:
                obv.append(obv[-1] + self.data['Volume'].iloc[i])
            elif self.data['Close'].iloc[i] < self.data['Close'].iloc[i-1]:
                obv.append(obv[-1] - self.data['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        self.data['OBV'] = obv
        return self.data['OBV'].iloc[-1] - self.data['OBV'].iloc[-OBV_LOOKBACK]

    def generate_signal(self):
        current_rsi = self.data['RSI'].iloc[-1]
        obv_change = self.calculate_obv_change()
        
        # --- MODIFIED NUANCED SIGNAL LOGIC ---
        
        # 1. Determine Signal/Action based on combined indicators
        if current_rsi <= 30:
            # Oversold condition (potential bounce)
            if obv_change > 0:
                signal = "Strong Bullish"
                action = "Oversold with increasing volume flow. Consider accumulating a position."
            else:
                signal = "Bullish (Weak)"
                action = "Oversold, but volume is not confirming a bounce yet. Monitor closely for reversal signs."
        
        elif current_rsi >= 70:
            # Overbought condition (potential pullback)
            if obv_change < 0:
                signal = "Strong Bearish"
                action = "Overbought with negative volume divergence. Consider booking profits or initiating a cautious short."
            else:
                signal = "Bearish (Weak)"
                action = "Overbought, but volume is still supporting the price. Maintain positions, but watch for a decline in volume."
        
        else:
            # Neutral RSI Zone (30 < RSI < 70) - Most common case for advisory signals
            if obv_change > 0:
                signal = "Neutral to Bullish"
                action = "RSI is neutral, but volume trend is positive. Suitable for holding or taking a small exploratory position, manage risk tightly."
            elif obv_change < 0:
                signal = "Neutral to Bearish"
                action = "RSI is neutral, but volume trend is negative. Avoid new entry, and be prepared to reduce existing positions."
            else:
                signal = "Neutral"
                action = "No clear trend or strong momentum detected. Maintain patience, hold existing positions, and wait for confirmation."

        # 2. Generate Commentary
        commentary = f"RSI: {current_rsi:.2f} "
        commentary += f"({'Oversold' if current_rsi<=30 else 'Overbought' if current_rsi>=70 else 'Neutral'}). "
        commentary += f"OBV trend (20 days): {'upwards' if obv_change>0 else 'downwards' if obv_change<0 else 'flat'}."

        # Log the calculated values for debugging
        print(f"--- Signal for {self.ticker} ---")
        print(f"RSI: {current_rsi:.2f}")
        print(f"OBV Change (20 days): {obv_change}")
        print(f"Signal: {signal}")
        print(f"Action: {action}")
        print("----------------------------")


        return {
            "ticker": self.ticker,
            "current_price": float(self.data['Close'].iloc[-1]), 
            "signal": signal,
            "suggested_action": action,
            "commentary": commentary
        }

# -------------------------------
# FLASK RESOURCE
# -------------------------------
class TechnicalSignal(Resource):
    def get(self):
        stock_ticker = request.args.get("stock", "").upper()
        if not stock_ticker:
            return {"error": "Stock ticker is required"}, 400

        try:
            analyzer = TechnicalAnalyzer(stock_ticker)
            analyzer.fetch_data()
            analyzer.calculate_rsi()
            result = analyzer.generate_signal()
            return result, 200
        except Exception as e:
            print("❌ Error:", e)
            traceback.print_exc()
            return {"error": f"Failed to generate signal: {str(e)}"}, 500

