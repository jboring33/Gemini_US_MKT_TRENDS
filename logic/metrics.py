import pandas as pd
import plotly.graph_objects as go


def create_interactive_chart(df, ticker):
  fig = go.Figure()

  # Clean, reliable Hollow Candlestick styling
  fig.add_trace(
      go.Candlestick(
          x=df.index,
          open=df["Open"],
          high=df["High"],
          low=df["Low"],
          close=df["Close"],
          name=f"{ticker} Price",
          increasing=dict(
              line=dict(color="#26a69a", width=1.5),
              fillcolor="rgba(255,255,255,0)",  # Transparent fill for hollow green
          ),
          decreasing=dict(
              line=dict(color="#ef5350", width=1.5),
              fillcolor="#ef5350",  # Solid fill for down red
          ),
      )
  )

  # Moving Averages
  if "SMA_20" in df.columns:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_20"],
            name="20 SMA",
            line=dict(color="orange", width=1.5),
        )
    )
  if "SMA_50" in df.columns:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_50"],
            name="50 SMA",
            line=dict(color="blue", width=1.5),
        )
    )
  if "SMA_200" in df.columns:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_200"],
            name="200 SMA",
            line=dict(color="black", width=2),
        )
    )

  fig.update_layout(
      title=f"{ticker} Technical Chart",
      yaxis_title="Price ($)",
      xaxis_rangeslider_visible=False,
      template="plotly_white",
      height=550,
      margin=dict(l=20, r=20, t=40, b=20),
      dragmode="zoom",
      hovermode="x unified",
  )

  fig.update_xaxes(fixedrange=False)
  fig.update_yaxes(fixedrange=False)

  return fig


def evaluate_trend_and_action(df):
  """Evaluates market data and returns dictionary of metrics & signals."""
  # Ensure clean numeric columns
  for col in ["Open", "High", "Low", "Close", "Volume"]:
    if col in df.columns:
      df[col] = pd.to_numeric(df[col], errors="coerce")

  # Calculate moving averages
  df["SMA_20"] = df["Close"].rolling(20).mean()
  df["SMA_50"] = df["Close"].rolling(50).mean()
  df["SMA_200"] = df["Close"].rolling(200).mean()

  # Calculate RSI (14)
  delta = df["Close"].diff()
  gain = (delta.where(delta > 0, 0)).rolling(14).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  df["RSI"] = rsi

  # Calculate MACD
  ema12 = df["Close"].ewm(span=12, adjust=False).mean()
  ema26 = df["Close"].ewm(span=26, adjust=False).mean()
  macd = ema12 - ema26
  signal = macd.ewm(span=9, adjust=False).mean()
  df["MACD"] = macd
  df["MACD_Signal"] = signal

  # Calculate RVOL (20-day baseline)
  vol_20_sma = df["Volume"].rolling(20).mean()
  rvol = (
      df["Volume"].iloc[-1] / vol_20_sma.iloc[-1]
      if vol_20_sma.iloc[-1] > 0
      else 1.0
  )

  curr_price = float(df["Close"].iloc[-1])
  sma200_val = (
      float(df["SMA_200"].iloc[-1])
      if not pd.isna(df["SMA_200"].iloc[-1])
      else curr_price
  )
  above_200 = curr_price > sma200_val
  curr_rsi = (
      float(df["RSI"].iloc[-1]) if not pd.isna(df["RSI"].iloc[-1]) else 50.0
  )
  macd_bullish = float(df["MACD"].iloc[-1]) > float(df["MACD_Signal"].iloc[-1])

  # Crossover Detections
  cross_20_50 = None
  cross_50_200 = None
  if (
      df["SMA_20"].iloc[-2] < df["SMA_50"].iloc[-2]
      and df["SMA_20"].iloc[-1] >= df["SMA_50"].iloc[-1]
  ):
    cross_20_50 = "⚡ Bullish 20/50 Crossover"
  elif (
      df["SMA_20"].iloc[-2] > df["SMA_50"].iloc[-2]
      and df["SMA_20"].iloc[-1] <= df["SMA_50"].iloc[-1]
  ):
    cross_20_50 = "⚠️ Bearish 20/50 Crossover"

  if (
      df["SMA_50"].iloc[-2] < df["SMA_200"].iloc[-2]
      and df["SMA_50"].iloc[-1] >= df["SMA_200"].iloc[-1]
  ):
    cross_50_200 = "🚀 Golden Cross (50/200)"
  elif (
      df["SMA_50"].iloc[-2] > df["SMA_200"].iloc[-2]
      and df["SMA_50"].iloc[-1] <= df["SMA_200"].iloc[-1]
  ):
    cross_50_200 = "💀 Death Cross (50/200)"

  # Recommendation Matrix
  if above_200 and rsi_val_check(curr_rsi) != "overbought" and macd_bullish:
    action = "ACCUMULATE"
    badge = "success"
    reason = "Trend Intact & Bullish Momentum"
  elif above_200:
    action = "HOLD"
    badge = "info"
    reason = (
        f"Trend Intact (RVOL {rvol:.1f}x)"
        if rvol >= 0.85
        else f"Low Volume / Retail Churn (RVOL {rvol:.1f}x)"
    )
  elif not above_200 and macd_bullish:
    action = "PAUSE BUYS"
    badge = "warning"
    reason = "Below 200 SMA (Rebound Rally)"
  else:
    action = "TRIM / DEFENSIVE"
    badge = "error"
    reason = "Deteriorating Trend & Negative Momentum"

  return {
      "curr_price": curr_price,
      "action": action,
      "badge": badge,
      "reason": reason,
      "above_200": above_200,
      "rsi": round(curr_rsi, 2),
      "rvol": round(rvol, 2),
      "macd_bullish": macd_bullish,
      "cross_20_50": cross_20_50,
      "cross_50_200": cross_50_200,
  }


def rsi_val_check(val):
  if val >= 70:
    return "overbought"
  elif val <= 30:
    return "oversold"
  return "neutral"
