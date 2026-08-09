from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import pytz
import streamlit as st
import yfinance as yf

import config.settings as settings
from logic.macro_data import get_macro_risk_indicators
from logic.metrics import (
    create_interactive_chart,
    evaluate_trend_and_action,
)

st.set_page_config(
    page_title="US Market Trends & Risk Dashboard",
    page_icon="🛡️",
    layout="wide",
)

TIMEZONE = pytz.timezone("US/Eastern")
NOW = datetime.now(TIMEZONE)


@st.cache_data(ttl=settings.CACHE_TTL)
def load_market_data():
  tickers = settings.PRIMARY_TICKERS + [settings.VOLATILITY_TICKER]
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

st.title("🛡️ Moderate / Conservative Market Trend Dashboard")
st.caption(
    f"Primary Benchmarks: **SPY, DIA, QQQ** | Last Updated:"
    f" {NOW.strftime('%Y-%m-%d %H:%M:%S %Z')}"
)

# -----------------------------------------------------------------------------
# 1. Executive Summary & Quick Reference Guides
# -----------------------------------------------------------------------------
st.subheader("1. Broad Market Guidance & Pricing")

cols = st.columns(len(settings.PRIMARY_TICKERS))

for idx, ticker in enumerate(settings.PRIMARY_TICKERS):
  with cols[idx]:
    if ticker in market_data:
      df = market_data[ticker]
      metrics = evaluate_trend_and_action(df)

      prev_price = float(df["Close"].iloc[-2])
      change = metrics["curr_price"] - prev_price
      pct_change = (change / prev_price) * 100

      low_52 = float(df["Low"].min())
      high_52 = float(df["High"].max())
      range_pct = (
          ((metrics["curr_price"] - low_52) / (high_52 - low_52)) * 100
          if high_52 > low_52
          else 0
      )

      # Determine plain-English 52-week position summary
      if range_pct >= 85:
        range_status = "Trading near 52-Week Highs (Strong Momentum)"
      elif range_pct <= 20:
        range_status = "Trading near 52-Week Lows (Value / Pullback)"
      else:
        range_status = "Mid-Range relative to 52-Week High/Low"

      st.metric(
          label=ticker,
          value=f"${metrics['curr_price']:,.2f}",
          delta=f"{change:+.2f} ({pct_change:+.2f}%)",
      )

      # Direct Matrix Action Badge
      if metrics["badge"] == "success":
        st.success(f"**{metrics['action']}**")
      elif metrics["badge"] == "warning":
        st.warning(f"**{metrics['action']}**")
      elif metrics["badge"] == "info":
        st.info(f"**{metrics['action']}**")
      else:
        st.error(f"**{metrics['action']}**")

      # Plain-English Factor Breakdown
      st.markdown(f"**Primary Driver:** {metrics['reason']}")
      
      st.markdown(
          f"- **Big Picture Trend:** {'🟢 Bullish (Above long-term average)' if metrics['above_200'] else '🔴 Bearish (Below long-term average)'}\n"
          f"- **Volume Fuel (RVOL):** {metrics['rvol']}x — {'Heavy Institutional Activity' if metrics['rvol'] >= 1.25 else 'Normal / Retail Trading'}\n"
          f"- **Speed & Energy (RSI):** {metrics['rsi_commentary']}\n"
          f"- **Direction (MACD):** {metrics['macd_commentary']}\n"
          f"- **52-Wk Position ({range_pct:.0f}%):** {range_status} *(${low_52:,.2f} – ${high_52:,.2f})*"
      )

      if metrics["cross_20_50"]:
        st.info(metrics["cross_20_50"])
      if metrics["cross_50_200"]:
        st.warning(metrics["cross_50_200"])

# Static Decision Matrix, RVOL, and Momentum Reference Guides
ref_col1, ref_col2, ref_col3 = st.columns(3)

with ref_col1:
  with st.expander("📖 Action Matrix Reference", expanded=False):
    st.markdown("""
        | Dashboard Signal | Lump-Sum | Routine DCA |
        | :--- | :--- | :--- |
        | **`ACCUMULATE`** | 🟢 **Buy Dips** | 🟢 **Green Light** |
        | **`HOLD`** | 🟡 **Wait** | 🟢 **Green Light** |
        | **`PAUSE BUYS`** | 🔴 **Stop** | 🟡 **Pause / Cash** |
        | **`TRIM / DEFENSIVE`** | 🔴 **Stop** | 🔴 **Pause** |
        """)

with ref_col2:
  with st.expander("📊 Relative Volume (RVOL) Guide", expanded=False):
    st.markdown("""
        | RVOL Level | Institutional Meaning | Action |
        | :--- | :--- | :--- |
        | **$\ge$ 1.25x** | 🏦 **Institutional Surge** | Confirms breakouts/dips. |
        | **0.85x – 1.24x** | ⚖️ **Normal Volume** | Standard trend movement. |
        | **$<$ 0.85x** | ⚠️ **Retail Churn** | Weak fuel; prone to reversals. |
        """)

with ref_col3:
  with st.expander("📈 RSI & MACD Momentum Guide", expanded=False):
    st.markdown("""
        | Indicator | Reading / Signal | Tactical Meaning |
        | :--- | :--- | :--- |
        | **RSI (14)** | **$\ge$ 70** | **Overbought:** Pause new lump-sum buys. |
        | **RSI (14)** | **$\le$ 30** | **Oversold:** Potential deep value entry. |
        | **MACD** | **Line $>$ Signal** | **Bullish Momentum:** Upward momentum intact. |
        | **MACD** | **Bull Crossover** | **Buy Signal:** Line crosses above signal line. |
        """)

# -----------------------------------------------------------------------------
# 2. Interactive Technical Charts
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
# 3. Economic & Macro Risk Cards
# -----------------------------------------------------------------------------
st.divider()
st.subheader("3. Economic & Macro Regime Cards")
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
