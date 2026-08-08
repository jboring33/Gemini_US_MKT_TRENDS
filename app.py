from datetime import datetime
import pandas as pd
import pytz
import streamlit as st
import yfinance as yf

from config.settings import CACHE_TTL, PRIMARY_TICKERS, VOLATILITY_TICKER
from logic.macro_data import get_macro_indicators
from logic.metrics import (
    calculate_atr,
    calculate_moving_averages,
    calculate_rsi,
)

# Page Config
st.set_page_config(
    page_title="Market Dashboard (SPY / DIA / QQQ)",
    page_icon="📈",
    layout="wide",
)

# Timezone Setup
TIMEZONE = pytz.timezone("US/Eastern")
NOW = datetime.now(TIMEZONE)

# -----------------------------------------------------------------------------
# Data Fetching
# -----------------------------------------------------------------------------


@st.cache_data(ttl=CACHE_TTL)
def load_market_data():
  """Fetch 1-year historical data for SPY, DIA, QQQ and VIX."""
  tickers_to_fetch = PRIMARY_TICKERS + [VOLATILITY_TICKER]
  raw_data = {}

  for ticker in tickers_to_fetch:
    try:
      tk = yf.Ticker(ticker)
      df = tk.history(period="1y")
      if not df.empty and len(df) >= 200:
        raw_data[ticker] = df
    except Exception as e:
      st.error(f"Error fetching data for {ticker}: {e}")

  return raw_data


# Load cached data
market_data = load_market_data()

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("Market Dashboard (SPY / DIA / QQQ)")
st.caption(f"Last Updated: {NOW.strftime('%Y-%m-%d %H:%M:%S %Z')}")

# -----------------------------------------------------------------------------
# Section 1: Summary Cards
# -----------------------------------------------------------------------------
st.subheader("Summary")
summary_cols = st.columns(len(PRIMARY_TICKERS))

for idx, ticker in enumerate(PRIMARY_TICKERS):
  with summary_cols[idx]:
    if ticker in market_data:
      df = market_data[ticker]
      curr_price = float(df["Close"].iloc[-1])
      prev_price = float(df["Close"].iloc[-2])
      change = curr_price - prev_price
      pct_change = (change / prev_price) * 100

      # 52-Week Range
      low_52 = float(df["Low"].min())
      high_52 = float(df["High"].max())
      range_pct = (
          ((curr_price - low_52) / (high_52 - low_52)) * 100
          if high_52 > low_52
          else 0
      )

      st.metric(
          label=ticker,
          value=f"${curr_price:,.2f}",
          delta=f"{change:+.2f} ({pct_change:+.2f}%)",
      )
      st.caption(
          f"**52-Wk Range ({range_pct:.1f}%):** ${low_52:,.2f} – ${high_52:,.2f}"
      )

# -----------------------------------------------------------------------------
# Section 2: Volatility (VIX Gauge)
# -----------------------------------------------------------------------------
st.divider()
st.subheader("Volatility")

if VOLATILITY_TICKER in market_data:
  vix_df = market_data[VOLATILITY_TICKER]
  vix_val = float(vix_df["Close"].iloc[-1])
  vix_prev = float(vix_df["Close"].iloc[-2])
  vix_change = vix_val - vix_prev

  # Determine Regime
  if vix_val < 20:
    regime = "LOW VOLATILITY (<20)"
    color_type = "off"
  elif vix_val <= 28:
    regime = "MODERATE VOLATILITY (20-28)"
    color_type = "normal"
  else:
    regime = "HIGH VOLATILITY / PANIC (>28)"
    color_type = "inverse"

  st.metric(
      label=f"CBOE Volatility Index (VIX) - {regime}",
      value=f"{vix_val:.2f}",
      delta=f"{vix_change:+.2f} since last run",
      delta_color=color_type,
  )

# -----------------------------------------------------------------------------
# Section 3: 14-Day ATR Profile
# -----------------------------------------------------------------------------
st.subheader("14-Day ATR Profile")
atr_cols = st.columns(len(PRIMARY_TICKERS))

for idx, ticker in enumerate(PRIMARY_TICKERS):
  with atr_cols[idx]:
    if ticker in market_data:
      atr_info = calculate_atr(market_data[ticker])
      st.markdown(f"### {ticker} Volatility")
      st.metric(
          label="14-Day ATR Value",
          value=f"${atr_info['atr_val']:.2f}",
          delta=f"~{atr_info['atr_pct']:.2f}% of price",
          delta_color="off",
      )

# -----------------------------------------------------------------------------
# Section 4: Moving Averages & Technical Indicators
# -----------------------------------------------------------------------------
st.divider()
st.subheader("Moving Averages & Technical Signals")
tech_cols = st.columns(len(PRIMARY_TICKERS))

for idx, ticker in enumerate(PRIMARY_TICKERS):
  with tech_cols[idx]:
    if ticker in market_data:
      df = market_data[ticker]
      rsi = calculate_rsi(df["Close"])
      ma_info = calculate_moving_averages(df["Close"])

      st.markdown(f"### {ticker} Technicals")

      # Signal Badge
      if ma_info["badge_style"] == "success":
        st.success(f"Action: **{ma_info['action']}**")
      elif ma_info["badge_style"] == "warning":
        st.warning(f"Action: **{ma_info['action']}**")
      else:
        st.info(f"Action: **{ma_info['action']}**")

      # Metrics Grid
      st.write(f"**20-Day EMA:** ${ma_info['ema_20']:,.2f}")
      st.write(f"**50-Day EMA:** ${ma_info['ema_50']:,.2f}")
      st.write(f"**200-Day EMA:** ${ma_info['ema_200']:,.2f}")
      st.write(f"**RSI (14):** {rsi}")

      st.caption(f"• {ma_info['trend_20_50']}")
      st.caption(f"• {ma_info['trend_50_200']}")

# -----------------------------------------------------------------------------
# Section 5: Macro Indicators Grid
# -----------------------------------------------------------------------------
st.divider()
st.subheader("Macro Indicators")
macro_items = get_macro_indicators()

# Render in 3 columns
m_cols = st.columns(3)
for idx, item in enumerate(macro_items):
  with m_cols[idx % 3]:
    with st.container(border=True):
      st.markdown(f"**{item['title']}**")

      if item["color"] == "green":
        st.caption(f"🟢 **{item['status']}**")
      elif item["color"] == "yellow":
        st.caption(f"🟡 **{item['status']}**")
      else:
        st.caption(f"🔴 **{item['status']}**")

      st.write(item["detail"])
