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
from logic.metrics import evaluate_trend_and_action

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
      # Color-Coded Factors (Big Picture, Volume, Speed, Direction)
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

      st.markdown(f"{b1}\n\n{b2}\n\n{b3}\n\n{b4}")

      # Dedicated 52-Week Position Card Restored inside Section 1
      with st.container(border=True):
        if range_pct >= 85:
          st.markdown(
              f"🔴 **52-Wk Position ({range_pct:.0f}%):** Extended Near Highs"
              " (Pullback Risk)"
          )
        elif range_pct <= 20:
          st.markdown(
              f"🟢 **52-Wk Position ({range_pct:.0f}%):** Near Lows (Value Zone)"
          )
        else:
          st.markdown(
              f"⚪ **52-Wk Position ({range_pct:.0f}%):** Mid-Range"
              " Consolidation"
          )
        st.caption(f"**Low:** ${low_52:,.2f} | **High:** ${high_52:,.2f}")
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
  with st.expander("⚙️ Decision Matrix & Weights", expanded=False):
    st.markdown("""
        | Factor / Signal | Weight / Hierarchy | Condition Rules |
        | :--- | :--- | :--- |
        | **200-Day SMA** | **Primary (50%)** | Price $>$ 200 SMA required for Bullish status. |
        | **MACD Line** | **Secondary (25%)** | Line $>$ Signal = Upward direction. |
        | **RSI (14)** | **Secondary (15%)** | Overbought ($\ge 70$), Oversold ($\le 30$). |
        | **RVOL (20d)** | **Filter (10%)** | $\ge 1.25x$ confirms high institutional fuel. |
        """)

# -----------------------------------------------------------------------------
# 2. Economic & Macro Risk Cards
# -----------------------------------------------------------------------------
st.divider()
st.subheader("2. Economic & Macro Regime Cards")
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
