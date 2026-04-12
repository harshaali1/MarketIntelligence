from flask import jsonify
from flask_restful import Resource
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt

class CandleData(Resource):
    def get(self, symbol):
        try:
            print(f"\n=== BACKEND: Fetching {symbol} ===")
            
            # ---- Date Range ----
            end = dt.date.today()
            start = end - dt.timedelta(days=60)
            
            # ---- Fetch Data ----
            df = yf.download(symbol, start=start, end=end, progress=False)
            
            print(f"Downloaded shape: {df.shape}")

            if df.empty:
                return {"error": f"No data for '{symbol}'"}, 400

            # ---- Fix MultiIndex ----
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

            # ---- Convert numeric ----
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # ---- Indicators (SMA5, SMA20) ----
            df["SMA5"] = df["Close"].rolling(5).mean()
            df["SMA20"] = df["Close"].rolling(20).mean()
            
            # ---- CRITICAL: Replace NaN with None BEFORE dropping rows ----
            # This way early rows with NaN SMA values become null in JSON
            df = df.replace({np.nan: None})
            
            # Optional: If you want to drop rows where OHLC data is missing
            # but keep rows where only SMA is None, do selective dropna:
            df = df.dropna(subset=["Open", "High", "Low", "Close"])

            if df.empty:
                return {"error": "No valid data after cleaning"}, 400

            # ---- Reset index ----
            df.reset_index(inplace=True)
            df["Date"] = df["Date"].astype(str)

            # ---- Create JSON payload ----
            # Orient='records' creates list of dicts
            records = df.to_dict(orient="records")
            
            print(f"Returning {len(records)} records")
            print(f"Sample record: {records[0] if records else 'None'}")

            return {
                "symbol": symbol,
                "count": len(records),
                "data": records
            }

        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}, 500