import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
  """Calculate standard 14-period RSI."""
  delta = prices.diff()
  gain = delta.where(delta > 0, 0.0)
  loss = -delta.where(delta < 0, 0.0)

  avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
  avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

  if avg_loss.iloc[-1] == 0:
    return 100.0

  rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
  return float(round(100 - (100 / (1 + rs)), 2))


def calculate_atr(df: pd.DataFrame, period: int = 14) -> dict:
  """Calculate Average True Range (ATR) & volatility percentage."""
  high = df["High"]
  low = df["Low"]
  close = df["Close"].shift(1)

  tr1 = high - low
  tr2 = (high - close).abs()
  tr3 = (low - close).abs()

  tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
  atr = tr.rolling(period).mean().iloc[-1]

  curr_price = df["Close"].iloc[-1]
  atr_pct = (atr / curr_price) * 100

  return {"atr_val": float(round(atr, 2)), "atr_pct": float(round(atr_pct, 2))}


def evaluate_trend_and_action(df: pd.DataFrame) -> dict:
  """Evaluates SMAs, RSI, and Crossovers to issue conservative Buy/Hold/Trim signals."""
  prices = df["Close"]
  curr_price = float(prices.iloc[-1])

  sma_20 = float(prices.rolling(20).mean().iloc[-1])
  sma_50 = float(prices.rolling(50).mean().iloc[-1])
  sma_200 = float(prices.rolling(200).mean().iloc[-1])

  # Previous day values for Crossover detection
  sma_20_prev = float(prices.rolling(20).mean().iloc[-2])
  sma_50_prev = float(prices.rolling(50).mean().iloc[-2])
  sma_200_prev = float(prices.rolling(200).mean().iloc[-2])

  rsi = calculate_rsi(prices)

  # Crossover Logic
  cross_20_50 = None
  if sma_20_prev < sma_50_prev and sma_20 > sma_50:
    cross_20_50 = "🟢 Bullish 20/50 Cross (Recent)"
  elif sma_20_prev > sma_50_prev and sma_20 < sma_50:
    cross_20_50 = "🔴 Bearish 20/50 Cross (Recent)"

  cross_50_200 = None
  if sma_50_prev < sma_200_prev and sma_50 > sma_200:
    cross_50_200 = "🚀 GOLDEN CROSS (50 crossed > 200 SMA)"
  elif sma_50_prev > sma_200_prev and sma_50 < sma_200:
    cross_50_200 = "⚠️ DEATH CROSS (50 crossed < 200 SMA)"

  # Conservative Rule Engine
  if curr_price > sma_50 and sma_50 > sma_200:
    if rsi > 72:
      action = "HOLD / PAUSE BUYS (Overbought)"
      badge = "warning"
    else:
      action = "ACCUMULATE / HOLD (Bullish Trend)"
      badge = "success"
  elif curr_price <= sma_50 and curr_price > sma_200:
    action = "NEUTRAL / DCA ONLY"
    badge = "info"
  else:
    action = "TRIM / DEFENSIVE POSITION"
    badge = "error"

  return {
      "curr_price": curr_price,
      "sma_20": round(sma_20, 2),
      "sma_50": round(sma_50, 2),
      "sma_200": round(sma_200, 2),
      "rsi": rsi,
      "action": action,
      "badge": badge,
      "above_200": curr_price > sma_200,
      "golden_alignment": sma_50 > sma_200,
      "cross_20_50": cross_20_50,
      "cross_50_200": cross_50_200,
  }


def create_interactive_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
  """Generates a 3-panel Plotly Chart: Price+SMAs+Volume, MACD & Histogram, and RSI."""
  df = df.copy()

  # Calculate Indicators
  df["SMA_20"] = df["Close"].rolling(20).mean()
  df["SMA_50"] = df["Close"].rolling(50).mean()
  df["SMA_200"] = df["Close"].rolling(200).mean()

  # RSI
  delta = df["Close"].diff()
  gain = delta.where(delta > 0, 0.0)
  loss = -delta.where(delta < 0, 0.0)
  avg_gain = gain.ewm(alpha=1 / 14, min_periods=14).mean()
  avg_loss = loss.ewm(alpha=1 / 14, min_periods=14).mean()
  rs = avg_gain / avg_loss
  df["RSI"] = 100 - (100 / (1 + rs))

  # MACD
  ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
  ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
  df["MACD"] = ema_12 - ema_26
  df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
  df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

  # Plotly Subplots
  fig = make_subplots(
      rows=3,
      cols=1,
      shared_xaxes=True,
      vertical_spacing=0.04,
      row_heights=[0.55, 0.25, 0.20],
      subplot_titles=(
          f"{ticker} Price & SMAs (20/50/200)",
          "MACD (12, 26, 9) & Histogram Crossovers",
          "RSI (14)",
      ),
  )

  # Row 1: Candlestick & SMAs
  fig.add_trace(
      go.Candlestick(
          x=df.index,
          open=df["Open"],
          high=df["High"],
          low=df["Low"],
          close=df["Close"],
          name="Price",
      ),
      row=1,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["SMA_20"],
          line=dict(color="#FFA500", width=1.5),
          name="20 SMA",
      ),
      row=1,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["SMA_50"],
          line=dict(color="#1E90FF", width=1.5),
          name="50 SMA",
      ),
      row=1,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["SMA_200"],
          line=dict(color="#8A2BE2", width=2),
          name="200 SMA",
      ),
      row=1,
      col=1,
  )

  # Row 2: MACD
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["MACD"],
          line=dict(color="#1E90FF", width=1.5),
          name="MACD Line",
      ),
      row=2,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["MACD_Signal"],
          line=dict(color="#FFA500", width=1.5),
          name="Signal Line",
      ),
      row=2,
      col=1,
  )

  hist_colors = [
      "#26a69a" if val >= 0 else "#ef5350" for val in df["MACD_Hist"].fillna(0)
  ]
  fig.add_trace(
      go.Bar(
          x=df.index, y=df["MACD_Hist"], marker_color=hist_colors, name="Hist"
      ),
      row=2,
      col=1,
  )

  # Row 3: RSI
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["RSI"],
          line=dict(color="#D87093", width=1.5),
          name="RSI (14)",
      ),
      row=3,
      col=1,
  )
  fig.add_hline(
      y=70,
      line_dash="dash",
      line_color="red",
      row=3,
      col=1,
      annotation_text="Overbought (70)",
  )
  fig.add_hline(
      y=30,
      line_dash="dash",
      line_color="green",
      row=3,
      col=1,
      annotation_text="Oversold (30)",
  )

  # Layout settings
  fig.update_layout(
      height=750,
      xaxis_rangeslider_visible=False,
      template="plotly_white",
      showlegend=True,
      margin=dict(l=20, r=20, t=40, b=20),
  )

  return fig
