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
  """Multi-indicator rule engine combining Price Trend, RSI, MACD, and Institutional Volume (RVOL)."""
  prices = df["Close"]
  volumes = df["Volume"]
  curr_price = float(prices.iloc[-1])

  # SMAs
  sma_20 = float(prices.rolling(20).mean().iloc[-1])
  sma_50 = float(prices.rolling(50).mean().iloc[-1])
  sma_200 = float(prices.rolling(200).mean().iloc[-1])

  sma_20_prev = float(prices.rolling(20).mean().iloc[-2])
  sma_50_prev = float(prices.rolling(50).mean().iloc[-2])
  sma_200_prev = float(prices.rolling(200).mean().iloc[-2])

  # Relative Volume (RVOL) - Institutional Engagement Metric
  vol_20_avg = float(volumes.rolling(20).mean().iloc[-1])
  curr_vol = float(volumes.iloc[-1])
  rvol = curr_vol / vol_20_avg if vol_20_avg > 0 else 1.0

  # Institutional Flags
  inst_buying = rvol >= 1.25 and curr_price >= float(df["Open"].iloc[-1])
  inst_selling = rvol >= 1.25 and curr_price < float(df["Open"].iloc[-1])
  weak_volume = rvol < 0.85

  # RSI
  rsi = calculate_rsi(prices)

  # MACD
  ema_12 = prices.ewm(span=12, adjust=False).mean()
  ema_26 = prices.ewm(span=26, adjust=False).mean()
  macd_line = ema_12 - ema_26
  signal_line = macd_line.ewm(span=9, adjust=False).mean()

  curr_macd = float(macd_line.iloc[-1])
  curr_signal = float(signal_line.iloc[-1])
  prev_macd = float(macd_line.iloc[-2])
  prev_signal = float(signal_line.iloc[-2])

  macd_bullish = curr_macd > curr_signal
  macd_cross_up = prev_macd < prev_signal and curr_macd > curr_signal

  # Crossover Checks
  cross_20_50 = None
  if sma_20_prev < sma_50_prev and sma_20 > sma_50:
    cross_20_50 = "🟢 Bullish 20/50 Cross"
  elif sma_20_prev > sma_50_prev and sma_20 < sma_50:
    cross_20_50 = "🔴 Bearish 20/50 Cross"

  cross_50_200 = None
  if sma_50_prev < sma_200_prev and sma_50 > sma_200:
    cross_50_200 = "🚀 GOLDEN CROSS (50 > 200 SMA)"
  elif sma_50_prev > sma_200_prev and sma_50 < sma_200:
    cross_50_200 = "⚠️ DEATH CROSS (50 < 200 SMA)"

  # -------------------------------------------------------------------------
  # Action Logic with Institutional Volume Screening
  # -------------------------------------------------------------------------
  is_bull_trend = curr_price > sma_200 and sma_50 > sma_200

  if is_bull_trend:
    if rsi >= 70:
      action = "PAUSE BUYS (RSI Overbought)"
      badge = "warning"
    elif inst_selling:
      action = "PAUSE BUYS (Institutional Distribution Volume)"
      badge = "warning"
    elif (
        curr_price <= (sma_20 * 1.01)
        and rsi <= 55
        and (inst_buying or macd_cross_up)
    ):
      action = f"ACCUMULATE (Institutional Dip Support | RVOL {rvol:.1f}x)"
      badge = "success"
    elif weak_volume:
      action = f"HOLD (Low Volume / Retail Churn | RVOL {rvol:.1f}x)"
      badge = "info"
    else:
      action = f"HOLD (Trend Intact | RVOL {rvol:.1f}x)"
      badge = "info"
  elif curr_price <= sma_50 and curr_price > sma_200:
    action = "NEUTRAL / DCA ONLY"
    badge = "info"
  else:
    if inst_selling:
      action = f"TRIM / DEFENSIVE (Institutional Distribution | RVOL {rvol:.1f}x)"
      badge = "error"
    else:
      action = "TRIM / DEFENSIVE POSITION"
      badge = "error"

  return {
      "curr_price": curr_price,
      "sma_20": round(sma_20, 2),
      "sma_50": round(sma_50, 2),
      "sma_200": round(sma_200, 2),
      "rsi": rsi,
      "rvol": round(rvol, 2),
      "macd_bullish": macd_bullish,
      "action": action,
      "badge": badge,
      "above_200": curr_price > sma_200,
      "golden_alignment": sma_50 > sma_200,
      "cross_20_50": cross_20_50,
      "cross_50_200": cross_50_200,
  }


def create_interactive_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
  """Generates a 4-panel Plotly Chart with Institutional Volume Average & Visual Highlighting."""
  df = df.copy()

  # Moving Averages
  df["SMA_20"] = df["Close"].rolling(20).mean()
  df["SMA_50"] = df["Close"].rolling(50).mean()
  df["SMA_200"] = df["Close"].rolling(200).mean()

  # Volume Metrics
  df["Vol_SMA_20"] = df["Volume"].rolling(20).mean()
  df["RVOL"] = df["Volume"] / df["Vol_SMA_20"]

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
      rows=4,
      cols=1,
      shared_xaxes=True,
      vertical_spacing=0.03,
      row_heights=[0.45, 0.15, 0.20, 0.20],
      subplot_titles=(
          f"{ticker} Price & SMAs (20/50/200)",
          "Volume & 20-Day Avg (Institutional Threshold: >1.25x)",
          "MACD (12, 26, 9)",
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

  # Row 2: Volume Bars + 20-Day Avg Overlay
  vol_colors = []
  for close, open_p, rvol in zip(df["Close"], df["Open"], df["RVOL"]):
    if close >= open_p:
      # Bright green for institutional volume breakout, muted green for standard
      vol_colors.append("#00E676" if rvol >= 1.25 else "#26a69a")
    else:
      # Bright red for institutional distribution, muted red for standard
      vol_colors.append("#FF1744" if rvol >= 1.25 else "#ef5350")

  fig.add_trace(
      go.Bar(
          x=df.index, y=df["Volume"], marker_color=vol_colors, name="Volume"
      ),
      row=2,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["Vol_SMA_20"],
          line=dict(color="#29B6F6", width=1.5, dash="dot"),
          name="20-Day Vol Avg",
      ),
      row=2,
      col=1,
  )

  # Row 3: MACD
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["MACD"],
          line=dict(color="#1E90FF", width=1.5),
          name="MACD Line",
      ),
      row=3,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["MACD_Signal"],
          line=dict(color="#FFA500", width=1.5),
          name="Signal Line",
      ),
      row=3,
      col=1,
  )
  hist_colors = [
      "#26a69a" if val >= 0 else "#ef5350" for val in df["MACD_Hist"].fillna(0)
  ]
  fig.add_trace(
      go.Bar(
          x=df.index, y=df["MACD_Hist"], marker_color=hist_colors, name="Hist"
      ),
      row=3,
      col=1,
  )

  # Row 4: RSI
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["RSI"],
          line=dict(color="#D87093", width=1.5),
          name="RSI (14)",
      ),
      row=4,
      col=1,
  )
  fig.add_hline(
      y=70,
      line_dash="dash",
      line_color="red",
      row=4,
      col=1,
      annotation_text="Overbought (70)",
  )
  fig.add_hline(
      y=30,
      line_dash="dash",
      line_color="green",
      row=4,
      col=1,
      annotation_text="Oversold (30)",
  )

  fig.update_layout(
      height=850,
      xaxis_rangeslider_visible=False,
      template="plotly_white",
      showlegend=True,
      margin=dict(l=20, r=20, t=40, b=20),
  )

  return fig
