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
  tickers = list(
      set(settings.PRIMARY_TICKERS + [settings.VOLATILITY_TICKER])
  )
  data = {}
  try:
    df_batch = yf.download(
        tickers, period="1y", group_by="ticker", progress=False
    )
    for t in tickers:
      try:
        if (
            isinstance(df_batch.columns, pd.MultiIndex)
            and t in df_batch.columns.levels[0]
        ):
          df_t = df_batch[t].copy().dropna(how="all")
        elif not isinstance(df_batch.columns, pd.MultiIndex):
          df_t = df_batch.copy().dropna(how="all")
        else:
          df_t = None

        if df_t is not None and not df_t.empty and len(df_t) >= 100:
          if isinstance(df_t.columns, pd.MultiIndex):
            df_t.columns = df_t.columns.get_level_values(0)
          data[t] = df_t
      except Exception:
        continue
  except Exception as e:
    st.error(f"Error fetching market data: {e}")
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

      # -----------------------------------------------------------------------
      # Color-Coded Factors (Strictly 4 Core Factors Here)
      # -----------------------------------------------------------------------
      if metrics.get("above_200", False):
        b1 = "🟢 **Big Picture Trend:** Bullish (Above long-term 200 SMA)"
      else:
        b1 = "🔴 **Big Picture Trend:** Bearish (Below long-term 200 SMA)"

      rvol_val = metrics.get("rvol", 1.0)
      if rvol_val >= 1.25:
        b2 = (
            f"🟢 **Volume Fuel (RVOL):** {rvol_val}x — High Institutional"
            " Conviction"
        )
      elif rvol_val >= 0.85:
        b2 = f"⚪ **Volume Fuel (RVOL):** {rvol_val}x — Normal Trading Volume"
      else:
        b2 = (
            f"🟡 **Volume Fuel (RVOL):** {rvol_val}x — Low Volume / Retail"
            " Churn"
        )

      rsi_val = metrics.get("rsi", 50)
      if rsi_val >= 70:
        b3 = (
            f"🔴 **Speed & Energy (RSI {rsi_val}):** Overbought (Extended /"
            " Pullback Risk)"
        )
      elif rsi_val <= 30:
        b3 = (
            f"🟢 **Speed & Energy (RSI {rsi_val}):** Oversold (Potential Dip"
            " Value Entry)"
        )
      elif rsi_val >= 50:
        b3 = (
            f"🟢 **Speed & Energy (RSI {rsi_val}):** Positive Bullish"
            " Momentum"
        )
      else:
        b3 = f"🟡 **Speed & Energy (RSI {rsi_val}):** Neutral to Weak Momentum"

      if metrics.get("macd_bullish", False):
        b4 = "🟢 **Direction (MACD):** Bullish (Momentum moving upward)"
      else:
        b4 = "🔴 **Direction (MACD):** Bearish (Momentum slowing / downward)"

      # Render ONLY the 4 main factors
      st.markdown(f"{b1}\n\n{b2}\n\n{b3}\n\n{b4}")

      if metrics["cross_20_50"]:
        st.info(metrics["cross_20_50"])
      if metrics["cross_50_200"]:
        st.warning(metrics["cross_50_200"])
    else:
      st.error(f"Unable to load data for {ticker}")

# Static Reference Guides
ref_col1, ref_col2, ref_col3, ref_col4 = st.columns(4)

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

with ref_col4:
  with st.expander("🕯️ Candlestick Guide", expanded=False):
    st.markdown("""
        | Candle Style | Intraday Movement | Price vs. Yesterday |
        | :--- | :--- | :--- |
        | `[ Outline Green ]` | **Bullish** (Close $>$ Open) | **Higher** than prev close |
        | `[ Solid Red ]` | **Bearish** (Close $<$ Open) | **Lower** than prev close |
        | `[ Solid Green ]` | **Bearish** (Close $<$ Open) | **Higher** than prev close |
        | `[ Outline Red ]` | **Bullish** (Close $>$ Open) | **Lower** than prev close |
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
      df = market_data[ticker]
      fig = create_interactive_chart(df, ticker)
      st.plotly_chart(
          fig,
          use_container_width=True,
          config={
              "scrollZoom": True,
              "displayModeBar": True,
              "displaylogo": False,
          },
      )

      # -----------------------------------------------------------------------
      # Dedicated 52-Week Position Card Moved HERE (Below Chart)
      # -----------------------------------------------------------------------
      curr_p = float(df["Close"].iloc[-1])
      low_52 = float(df["Low"].min())
      high_52 = float(df["High"].max())
      range_pct = (
          ((curr_p - low_52) / (high_52 - low_52)) * 100
          if high_52 > low_52
          else 0
      )

      with st.container(border=True):
        st.markdown(f"### 📍 {ticker} 52-Week Position")
        if range_pct >= 85:
          st.markdown(
              f"🔴 **52-Wk Range ({range_pct:.0f}%):** Near Highs (Pullback"
              " Risk)"
          )
        elif range_pct <= 20:
          st.markdown(
              f"🟢 **52-Wk Range ({range_pct:.0f}%):** Near Lows (Value Zone)"
          )
        else:
          st.markdown(
              f"⚪ **52-Wk Range ({range_pct:.0f}%):** Mid-Range"
              " Consolidation"
          )
        st.caption(
            f"**52-Wk Low:** ${low_52:,.2f} | **Current:** ${curr_p:,.2f} |"
            f" **52-Wk High:** ${high_52:,.2f}"
        )
    else:
      st.warning(f"No chart data available for {ticker}")

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
