import os
import sys

# Ensure repository root is in Python's path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pandas as pd
import pytz
import streamlit as st
import yfinance as yf

# Import settings module directly
import config.settings as settings
from logic.macro_data import get_macro_risk_indicators
from logic.metrics import (
    calculate_atr,
    create_interactive_chart,
    evaluate_trend_and_action,
)

# Page Setup
st.set_page_config(
    page_title="US Market Trends & Risk Dashboard",
    page_icon="🛡️",
    layout="wide",
)

TIMEZONE = pytz.timezone("US/Eastern")
NOW = datetime.now(TIMEZONE)

# -----------------------------------------------------------------------------
# Data Loader
# -----------------------------------------------------------------------------


@st.cache_data(ttl=CACHE_TTL)
def load_market_data():
  """Fetch 1-year historical data for SPY, DIA, QQQ, and VIX."""
  tickers = PRIMARY_TICKERS + [VOLATILITY_TICKER]
  data = {}
  for t in tickers:
    try:
      tk = yf.Ticker(t)
      df = tk.history(period="1y")
      if not df.empty and len(df) >= 200:
        data[t] = df
    except Exception as e:
      st.error(f"Error loading ticker {t}: {e}")
  return data


market_data = load_market_data()

# Header
st.title("🛡️ Moderate / Conservative Market Trend Dashboard")
st.caption(
    f"Primary Benchmarks: **SPY, DIA, QQQ** | Last Updated:"
    f" {NOW.strftime('%Y-%m-%d %H:%M:%S %Z')}"
)

# -----------------------------------------------------------------------------
# 1. Executive Summary & Action Signals
# -----------------------------------------------------------------------------
st.subheader("1. Broad Market Guidance & Pricing")
cols = st.columns(len(PRIMARY_TICKERS))

for idx, ticker in enumerate(PRIMARY_TICKERS):
  with cols[idx]:
    if ticker in market_data:
      df = market_data[ticker]
      metrics = evaluate_trend_and_action(df)

      prev_price = float(df["Close"].iloc[-2])
      change = metrics["curr_price"] - prev_price
      pct_change = (change / prev_price) * 100

      # 52-Week Range
      low_52 = float(df["Low"].min())
      high_52 = float(df["High"].max())
      range_pct = (
          ((metrics["curr_price"] - low_52) / (high_52 - low_52)) * 100
          if high_52 > low_52
          else 0
      )

      st.metric(
          label=ticker,
          value=f"${metrics['curr_price']:,.2f}",
          delta=f"{change:+.2f} ({pct_change:+.2f}%)",
      )

      # Action Badge
      if metrics["badge"] == "success":
        st.success(metrics["action"])
      elif metrics["badge"] == "warning":
        st.warning(metrics["action"])
      elif metrics["badge"] == "info":
        st.info(metrics["action"])
      else:
        st.error(metrics["action"])

      st.caption(
          f"**52-Wk Range ({range_pct:.0f}%):** ${low_52:,.2f} – ${high_52:,.2f}"
      )

      # Show Crossover Alerts if present
      if metrics["cross_20_50"]:
        st.info(metrics["cross_20_50"])
      if metrics["cross_50_200"]:
        st.warning(metrics["cross_50_200"])

# -----------------------------------------------------------------------------
# 2. Interactive Charts (Price + SMAs, MACD, RSI)
# -----------------------------------------------------------------------------
st.divider()
st.subheader("2. Price Action & Volume Technical Charts")

chart_tab1, chart_tab2, chart_tab3 = st.tabs(
    ["SPY Chart", "DIA Chart", "QQQ Chart"]
)
tab_map = {"SPY": chart_tab1, "DIA": chart_tab2, "QQQ": chart_tab3}

for ticker, tab in tab_map.items():
  with tab:
    if ticker in market_data:
      fig = create_interactive_chart(market_data[ticker], ticker)
      st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 3. Volatility & Position Sizing (VIX & ATR)
# -----------------------------------------------------------------------------
st.divider()
st.subheader("3. Volatility & Position Risk Profiling")

v_col1, v_col2 = st.columns([1, 2])

with v_col1:
  if VOLATILITY_TICKER in market_data:
    vix_df = market_data[VOLATILITY_TICKER]
    vix_val = float(vix_df["Close"].iloc[-1])
    vix_prev = float(vix_df["Close"].iloc[-2])
    vix_change = vix_val - vix_prev

    if vix_val < VIX_LOW_RISK:
      vix_status = "LOW VOLATILITY (Favorable)"
      v_color = "normal"
    elif vix_val <= VIX_HIGH_RISK:
      vix_status = "MODERATE VOLATILITY (Caution)"
      v_color = "off"
    else:
      vix_status = "ELEVATED VOLATILITY / PANIC"
      v_color = "inverse"

    st.metric(
        label=f"CBOE Volatility Index (VIX) — {vix_status}",
        value=f"{vix_val:.2f}",
        delta=f"{vix_change:+.2f} vs yesterday",
        delta_color=v_color,
    )

with v_col2:
  st.markdown("#### 14-Day Expected Daily Volatility (ATR)")
  atr_cols = st.columns(3)
  for idx, ticker in enumerate(PRIMARY_TICKERS):
    with atr_cols[idx]:
      if ticker in market_data:
        atr_info = calculate_atr(market_data[ticker])
        st.metric(
            label=f"{ticker} Daily Range",
            value=f"± ${atr_info['atr_val']:.2f}",
            delta=f"~{atr_info['atr_pct']:.2f}% of price",
            delta_color="off",
        )

# -----------------------------------------------------------------------------
# 4. Fundamental Macro Risk Cards
# -----------------------------------------------------------------------------
st.divider()
st.subheader("4. Economic & Macro Regime Cards")
macro_list = get_macro_risk_indicators()
m_cols = st.columns(3)

for idx, item in enumerate(macro_list):
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
