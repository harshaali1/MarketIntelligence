import yfinance as yf
import pandas as pd
import json
import math
import numpy as np
from flask import request, Response
from flask_restful import Resource


# ---------------------------
# Helper: recursive sanitizer (UNCHANGED)
# ---------------------------
def _is_nan_like(x):
    """Return True for float('nan'), numpy.nan, inf, -inf."""
    try:
        if isinstance(x, (float, int, np.floating, np.integer)):
            return not math.isfinite(float(x))
    except Exception:
        pass
    try:
        if isinstance(x, (np.floating, np.integer)):
            return not np.isfinite(x)
    except Exception:
        pass
    return False


def sanitize_for_json(obj):
    """
    Recursively walk through obj (dict/list/tuple/scalar) and replace:
      - NaN, inf, -inf (including numpy types) -> None
    Also convert numpy scalars/arrays to Python native types where possible.
    """
    if obj is None or isinstance(obj, (bool, str)):
        return obj

    if isinstance(obj, (int, float)):
        if _is_nan_like(obj):
            return None
        return obj

    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        py = obj.item()
        return sanitize_for_json(py)

    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]

    if isinstance(obj, pd.Series):
        return [sanitize_for_json(v) for v in obj.tolist()]

    if isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict(orient="records"))

    if isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())

    try:
        if hasattr(obj, "item"):
            return sanitize_for_json(obj.item())
    except Exception:
        pass

    return str(obj)


def make_json_response(payload, status=200):
    """
    Sanitize payload and return a Flask Response with strict JSON (no NaN allowed).
    """
    safe_payload = sanitize_for_json(payload)
    body = json.dumps(safe_payload, allow_nan=False) 
    return Response(body, status=status, mimetype="application/json")


# ============================================================
#                     STOCK CHART CLASS (REVISED get_price_data)
# ============================================================
class StockChart:
    def __init__(self, ticker: str):
        self.raw_ticker = ticker.upper().strip()
        self.yf_ticker = self._format_ticker(self.raw_ticker)
        self.data = None
        # Moving Average periods remain 20 and 50 days
        self.MA_PERIODS = [20, 50] 

    def _format_ticker(self, ticker: str) -> str:
        if not any(ticker.endswith(suffix) for suffix in [".NS", ".BO", ".L", ".PA"]):
            return ticker + ".NS"
        return ticker

    def fetch_data(self):
        df = yf.download(
            self.yf_ticker,
            period="1y", 
            interval="1d",
            progress=False
        )

        if df.empty:
            raise ValueError(f"Could not fetch data for ticker: {self.raw_ticker} (Tried: {self.yf_ticker})")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if not {"Close", "Volume"}.issubset(set(df.columns)):
            raise ValueError("Essential columns (Close, Volume) missing.")

        for period in self.MA_PERIODS:
            df[f"MA_{period}"] = df["Close"].rolling(window=period).mean().round(2)

        self.data = df.tail(180).copy()

    def get_price_data(self):
        """
        Generates data for a smooth, filled price line chart.
        """
        labels = self.data.index.strftime("%Y-%m-%d").tolist()
        return {
            "labels": labels, 
            "datasets": [{
                "label": f"{self.raw_ticker} Close Price", 
                "data": self.data["Close"].tolist(),
                # Use a slightly softer color scheme for the area
                "backgroundColor": "rgba(0, 102, 204, 0.2)", # Light Blue Fill
                "borderColor": "rgb(0, 102, 204)",          # Solid Blue Line
                "fill": True,
                "tension": 0.4, # <-- Increased tension for smoother curve
                "pointRadius": 0, # <-- Removed points for cleaner look
            }]
        }

    def get_volume_data(self):
        labels = self.data.index.strftime("%Y-%m-%d").tolist()
        return {
            "labels": labels, 
            "datasets": [{
                "label": f"{self.raw_ticker} Volume", 
                "data": self.data["Volume"].tolist(),
                "backgroundColor": "rgba(153, 102, 255, 0.8)", 
                "borderColor": "rgba(153, 102, 255, 1)",      
                "type": "bar",
            }]
        }

    def get_dma_data(self):
        labels = self.data.index.strftime("%Y-%m-%d").tolist()
        
        datasets = [
            {
                "label": "20-Day MA", 
                "data": self.data["MA_20"].tolist(), 
                "borderColor": "rgb(46, 204, 113)", 
                "fill": False,
                "tension": 0.4, 
                "pointRadius": 0, 
            },
            {
                "label": "50-Day MA", 
                "data": self.data["MA_50"].tolist(), 
                "borderColor": "rgb(255, 165, 0)", 
                "fill": False,
                "tension": 0.4, 
                "pointRadius": 0, 
            },
            {
                "label": f"{self.raw_ticker} Price", 
                "data": self.data["Close"].tolist(),
                "borderColor": "rgb(0, 102, 204)", 
                "fill": False,
                "tension": 0.4,
                "borderWidth": 1.5, 
                "pointRadius": 0, 
            }
        ]
        return {"labels": labels, "datasets": datasets}


# ============================================================
# API Resources using make_json_response(...) (UNCHANGED)
# ============================================================

class PriceChartAPI(Resource):
    def get(self):
        ticker = request.args.get("stock", "").strip()
        if not ticker:
            return make_json_response({"error": "Stock ticker is required"}, status=400)

        try:
            sc = StockChart(ticker)
            sc.fetch_data()
            return make_json_response(sc.get_price_data(), status=200)
        except Exception as e:
            return make_json_response({"error": str(e)}, status=500)


class VolumeChartAPI(Resource):
    def get(self):
        ticker = request.args.get("stock", "").strip()
        if not ticker:
            return make_json_response({"error": "Stock ticker is required"}, status=400)

        try:
            sc = StockChart(ticker)
            sc.fetch_data()
            return make_json_response(sc.get_volume_data(), status=200)
        except Exception as e:
            return make_json_response({"error": str(e)}, status=500)


class DMAChartAPI(Resource):
    def get(self):
        ticker = request.args.get("stock", "").strip()
        if not ticker:
            return make_json_response({"error": "Stock ticker is required"}, status=400)

        try:
            sc = StockChart(ticker)
            sc.fetch_data()
            return make_json_response(sc.get_dma_data(), status=200)
        except Exception as e:
            return make_json_response({"error": str(e)}, status=500)