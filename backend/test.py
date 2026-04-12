import yfinance as yf
import pandas as pd
import datetime as dt
import mplfinance as mpf

symbol = "TCS.NS"
end = dt.date.today()
start = end - dt.timedelta(days=60)

df = yf.download(symbol, start=start, end=end)

# ---- FIX MULTIINDEX COLUMNS ----
df.columns = [col[0] for col in df.columns]   # keep only Open, High, Low, Close, Volume

# ---- Convert to numeric ----
numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ---- Drop rows with missing prices ----
df = df.dropna(subset=["Open", "High", "Low", "Close"])

# ---- Plot ----
mpf.plot(
    df,
    type="candle",
    style="charles",
    title=f"{symbol} - Last 2 Months",
    volume=True,
    mav=(5, 20)
)
