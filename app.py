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
  """Downloads all primary market tickers in a single batched request

  to prevent individual request timeouts, with resilient multi-index parsing.
  """
  tickers = list(
      set(settings.PRIMARY_TICKERS + [settings.VOLATILITY_TICKER])
  )
  data = {}

  try:
    # Single batch call prevents per-ticker timeouts
    df_batch = yf.download(
        tickers=tickers, period="1y", group_by="ticker", progress=False
    )

    if df_batch.empty:
      st.error("Market data fetch returned an empty dataset.")
      return data

    for t in tickers:
      try:
        df_t = None
        # Case 1: Multi-level columns grouped by ticker (Standard yfinance batch output)
        if (
            isinstance(df_batch.columns, pd.MultiIndex)
            and t in df_batch.columns.levels[0]
        ):
          df_t = df_batch[t].copy()
        # Case 2: Multi-level columns grouped by attribute ('Close', 'SPY')
        elif (
            isinstance(df_batch.columns, pd.MultiIndex)
            and t in df_batch.columns.levels[1]
        ):
          df_t = df_batch.xs(t, axis=1, level=1).copy()
        # Case 3: Flat DataFrame (single ticker fallback)
        elif not isinstance(df_batch.columns, pd.MultiIndex):
          df_t = df_batch.copy()

        if df_t is not None:
          df_t = df_t.dropna(how="all")
          if len(df_t) >= 50:
            data[t] = df_t

      except Exception as inner_e:
        st.warning(f"Error parsing ticker {t}: {inner_e}")
        continue

  except Exception as e:
    st.error(f"Error fetching batched market data: {e}")

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

      # Color-Coded Factors
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

      # Dedicated 52-Week Position Card
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

# -----------------------------------------------------------------------------
# Quick Reference Guides: Left-Margin Selector & Full-Width Right Display
# -----------------------------------------------------------------------------
st.write("")
guide_left_col, guide_right_col = st.columns([1, 3])

with guide_left_col:
  selected_guide = st.radio(
      "📖 Quick Reference Guides",
      options=[
          "Action Matrix Reference",
          "Relative Volume (RVOL) Guide",
          "RSI & MACD Momentum Guide",
          "Decision Matrix & Weights",
      ],
      index=0,
  )

with guide_right_col:
  with st.container(border=True):
    if selected_guide == "Action Matrix Reference":
      st.markdown("### 📖 Action Matrix Reference")
      st.markdown("""
            | Dashboard Signal | Lump-Sum Capital | Routine DCA Capital | Strategy Execution |
            | :--- | :--- | :--- | :--- |
            | **`ACCUMULATE`** | 🟢 **Buy Dips** | 🟢 **Green Light** | Full conviction allocation on market pullbacks. |
            | **`HOLD`** | 🟡 **Wait** | 🟢 **Green Light** | Continue systematic DCA; pause large lump-sum entries. |
            | **`PAUSE BUYS`** | 🔴 **Stop** | 🟡 **Pause / Cash** | Hold cash allocations; trend below major 200 SMA threshold. |
            | **`TRIM / DEFENSIVE`** | 🔴 **Stop** | 🔴 **Pause** | Focus on capital preservation; reduce exposure. |
            """)

    elif selected_guide == "Relative Volume (RVOL) Guide":
      st.markdown("### 📊 Relative Volume (RVOL) Guide")
      st.markdown("""
            | RVOL Threshold | Institutional Meaning | Market Impact & Action |
            | :--- | :--- | :--- |
            | **$\ge$ 1.25x** | 🏦 **Institutional Heavy Volume** | Confirms true trend breakouts or major dip accumulation. |
            | **0.85x – 1.24x** | ⚖️ **Normal Trading Volume** | Expected baseline market participation and orderly trend flow. |
            | **$<$ 0.85x** | ⚠️ **Retail Churn / Low Volume** | Weak institutional support; signals fragile moves prone to reversals. |
            """)

    elif selected_guide == "RSI & MACD Momentum Guide":
      st.markdown("### 📈 RSI & MACD Momentum Guide")
      st.markdown("""
            | Indicator | Signal / Level | Interpretation & Tactical Meaning |
            | :--- | :--- | :--- |
            | **RSI (14)** | **$\ge$ 70** | **Overbought:** Extended movement; pause new lump-sum entries. |
            | **RSI (14)** | **$\le$ 30** | **Oversold:** Value compression zone; monitor for deep dip buying. |
            | **MACD** | **Line $>$ Signal** | **Bullish Momentum:** Upward momentum intact across short/mid timeframe. |
            | **MACD** | **Line $<$ Signal** | **Bearish Momentum:** Momentum slowing down; caution warranted. |
            """)

    elif selected_guide == "Decision Matrix & Weights":
      st.markdown("### ⚙️ Decision Matrix & Factor Weights")
      st.markdown("""
            | Factor / Metric | Decision Weight | Condition Rules |
            | :--- | :--- | :--- |
            | **200-Day SMA** | **Primary Baseline (50%)** | Price $>$ 200 SMA required for Bullish status. Hard gate for `ACCUMULATE`. |
            | **MACD Indicator** | **Directional Vector (25%)** | MACD Line $>$ Signal Line required for active upward momentum. |
            | **RSI (14-Day)** | **Speed & Energy (15%)** | Filters out overbought conditions ($\ge 70$) to prevent buying peaks. |
            | **RVOL (20-Day)** | **Institutional Fuel (10%)** | Volume multiplier verifying high-conviction institutional backing ($\ge 1.25x$). |
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
