import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
  """Calculate standard 14-period Relative Strength Index (RSI)."""
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
  """Calculate Average True Range (ATR), volatility percentage, and trailing stop recommendations."""
  high = df["High"]
  low = df["Low"]
  close = df["Close"].shift(1)

  tr1 = high - low
  tr2 = (high - close).abs()
  tr3 = (low - close).abs()

  tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
  atr = tr.rolling(period).mean().iloc[-1]

  curr_price = float(df["Close"].iloc[-1])
  atr_pct = (atr / curr_price) * 100

  # Strategic Risk Envelope: 2x ATR Trailing Stop
  atr_stop_2x = curr_price - (2 * atr)

  return {
      "atr_val": float(round(atr, 2)),
      "atr_pct": float(round(atr_pct, 2)),
      "atr_stop_2x": float(round(atr_stop_2x, 2)),
  }


def evaluate_trend_and_action(df: pd.DataFrame) -> dict:
  """Multi-indicator rule engine combining Price Action, SMAs, RVOL, RSI, MACD, and ATR.

  Outputs Matrix-Aligned Actions, Reasons, and ATR Trailing Stop level.
  """
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

  inst_buying = rvol >= 1.25 and curr_price >= float(df["Open"].iloc[-1])
  inst_selling = rvol >= 1.25 and curr_price < float(df["Open"].iloc[-1])
  weak_volume = rvol < 0.85

  # RSI
  rsi = calculate_rsi(prices)

  # ATR & Trailing Stop Calculation
  atr_data = calculate_atr(df)

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

  # Specific RSI & MACD Commentary
  if rsi >= 70:
    rsi_commentary = f"RSI Overbought ({rsi:.1f}) — pullback expected"
  elif rsi <= 30:
    rsi_commentary = f"RSI Oversold ({rsi:.1f}) — deep value zone"
  else:
    rsi_commentary = f"RSI Neutral ({rsi:.1f})"

  if macd_cross_up:
    macd_commentary = "MACD Bullish Crossover (Momentum Turning Up)"
  elif macd_bullish:
    macd_commentary = "MACD Positive Momentum"
  else:
    macd_commentary = "MACD Negative Momentum / Pullback"

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

  # Matrix-Aligned Action Logic
  is_bull_trend = curr_price > sma_200 and sma_50 > sma_200

  if is_bull_trend:
    if rsi >= 70:
      action = "PAUSE BUYS"
      reason = "RSI Overbought (≥70)"
      badge = "warning"
    elif inst_selling:
      action = "PAUSE BUYS"
      reason = f"Institutional Distribution Volume (RVOL {rvol:.1f}x)"
      badge = "warning"
    elif (
        curr_price <= (sma_20 * 1.01)
        and rsi <= 55
        and (inst_buying or macd_cross_up)
    ):
      action = "ACCUMULATE"
      reason = f"Institutional Dip Support (RVOL {rvol:.1f}x)"
      badge = "success"
    elif weak_volume:
      action = "HOLD"
      reason = f"Low Volume / Retail Churn (RVOL {rvol:.1f}x)"
      badge = "info"
    else:
      action = "HOLD"
      reason = f"Trend Intact (RVOL {rvol:.1f}x)"
      badge = "info"
  elif curr_price <= sma_50 and curr_price > sma_200:
    action = "HOLD"
    reason = "Consolidating Between 50 & 200 SMA"
    badge = "info"
  else:
    action = "TRIM / DEFENSIVE"
    reason = (
        f"Institutional Selling (RVOL {rvol:.1f}x)"
        if inst_selling
        else "Below 200 SMA / Downtrend"
    )
    badge = "error"

  return {
      "curr_price": curr_price,
      "sma_20": round(sma_20, 2),
      "sma_50": round(sma_50, 2),
      "sma_200": round(sma_200, 2),
      "rsi": rsi,
      "rvol": round(rvol, 2),
      "atr_val": atr_data["atr_val"],
      "atr_pct": atr_data["atr_pct"],
      "atr_stop": atr_data["atr_stop_2x"],
      "macd_bullish": macd_bullish,
      "rsi_commentary": rsi_commentary,
      "macd_commentary": macd_commentary,
      "action": action,
      "reason": reason,
      "badge": badge,
      "above_200": curr_price > sma_200,
      "golden_alignment": sma_50 > sma_200,
      "cross_20_50": cross_20_50,
      "cross_50_200": cross_50_200,
  }


def create_interactive_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
  """Generates clean 4-panel Plotly Chart with isolated, row-specific headers."""
  df = df.copy()

  df["SMA_20"] = df["Close"].rolling(20).mean()
  df["SMA_50"] = df["Close"].rolling(50).mean()
  df["SMA_200"] = df["Close"].rolling(200).mean()

  df["Vol_SMA_20"] = df["Volume"].rolling(20).mean()
  df["RVOL"] = df["Volume"] / df["Vol_SMA_20"]

  delta = df["Close"].diff()
  gain = delta.where(delta > 0, 0.0)
  loss = -delta.where(delta < 0, 0.0)
  avg_gain = gain.ewm(alpha=1 / 14, min_periods=14).mean()
  avg_loss = loss.ewm(alpha=1 / 14, min_periods=14).mean()
  rs = avg_gain / avg_loss
  df["RSI"] = 100 - (100 / (1 + rs))

  ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
  ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
  df["MACD"] = ema_12 - ema_26
  df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
  df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

  fig = make_subplots(
      rows=4,
      cols=1,
      shared_xaxes=True,
      vertical_spacing=0.04,
      row_heights=[0.45, 0.15, 0.20, 0.20],
      subplot_titles=(
          f"<b>{ticker} Price & SMAs</b> (Red: 20 SMA | Yellow: 50 SMA |"
          " Green: 200 SMA)",
          "<b>Volume</b> (Light Blue: 20-Day Avg Volume | Bright Color: High"
          " RVOL ≥1.25x)",
          "<b>MACD (12, 26, 9)</b> (Blue: MACD Line | Orange: Signal Line)",
          "<b>RSI (14)</b> (Pink: 14-Period RSI Line)",
      ),
  )

  # Row 1: Price Candlestick & SMAs
  fig.add_trace(
      go.Candlestick(
          x=df.index,
          open=df["Open"],
          high=df["High"],
          low=df["Low"],
          close=df["Close"],
          name="Price",
          showlegend=False,
      ),
      row=1,
      col=1,
  )

  # 20 SMA -> Red
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["SMA_20"],
          line=dict(color="#FF1744", width=1.5),
          name="20 SMA",
          showlegend=False,
      ),
      row=1,
      col=1,
  )

  # 50 SMA -> Yellow
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["SMA_50"],
          line=dict(color="#FFD600", width=1.5),
          name="50 SMA",
          showlegend=False,
      ),
      row=1,
      col=1,
  )

  # 200 SMA -> Green
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["SMA_200"],
          line=dict(color="#00E676", width=2.0),
          name="200 SMA",
          showlegend=False,
      ),
      row=1,
      col=1,
  )

  # Row 2: Volume Subplot
  vol_colors = []
  for close, open_p, rvol in zip(df["Close"], df["Open"], df["RVOL"]):
    if close >= open_p:
      vol_colors.append("#00E676" if rvol >= 1.25 else "#26a69a")
    else:
      vol_colors.append("#FF1744" if rvol >= 1.25 else "#ef5350")

  fig.add_trace(
      go.Bar(
          x=df.index,
          y=df["Volume"],
          marker_color=vol_colors,
          name="Volume",
          showlegend=False,
      ),
      row=2,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["Vol_SMA_20"],
          line=dict(color="#29B6F6", width=1.5, dash="dot"),
          name="20D Vol Avg",
          showlegend=False,
      ),
      row=2,
      col=1,
  )

  # Row 3: MACD Subplot
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["MACD"],
          line=dict(color="#1E90FF", width=1.5),
          name="MACD",
          showlegend=False,
      ),
      row=3,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["MACD_Signal"],
          line=dict(color="#FFA500", width=1.5),
          name="Signal",
          showlegend=False,
      ),
      row=3,
      col=1,
  )
  hist_colors = [
      "#26a69a" if val >= 0 else "#ef5350" for val in df["MACD_Hist"].fillna(0)
  ]
  fig.add_trace(
      go.Bar(
          x=df.index,
          y=df["MACD_Hist"],
          marker_color=hist_colors,
          name="Histogram",
          showlegend=False,
      ),
      row=3,
      col=1,
  )

  # Row 4: RSI Subplot
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["RSI"],
          line=dict(color="#D87093", width=1.5),
          name="RSI (14)",
          showlegend=False,
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
      annotation_position="top right",
  )
  fig.add_hline(
      y=30,
      line_dash="dash",
      line_color="green",
      row=4,
      col=1,
      annotation_text="Oversold (30)",
      annotation_position="bottom right",
  )

  fig.update_layout(
      height=850,
      xaxis_rangeslider_visible=False,
      template="plotly_white",
      showlegend=False,
      margin=dict(l=20, r=20, t=30, b=20),
  )

  return fig
