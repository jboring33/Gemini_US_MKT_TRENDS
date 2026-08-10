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
    # Batch fetch all tickers in a single request
    df_batch = yf.download(
        tickers, period="1y", group_by="ticker", progress=False
    )

    for t in tickers:
      # Extract individual ticker dataframe from batch result
      if len(tickers) == 1:
        df_t = df_batch.copy()
      else:
        df_t = (
            df_batch[t].dropna() if t in df_batch.columns.levels[0] else None
        )

      if df_t is not None and not df_t.empty and len(df_t) >= 200:
        # Standardize column structure if needed
        if isinstance(df_t.columns, pd.MultiIndex):
          df_t.columns = df_t.columns.get_level_values(0)
        data[t] = df_t

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
      # Color-Coded Factor Evaluation
      # -----------------------------------------------------------------------
      # 1. Trend Factor
      if metrics.get("above_200", False):
        trend_bullet = (
            "🟢 **Big Picture Trend:** Bullish (Above long-term 200 SMA)"
        )
      else:
        trend_bullet = (
            "🔴 **Big Picture Trend:** Bearish (Below long-term 200 SMA)"
        )

      # 2. Volume Fuel Factor (RVOL)
      rvol_val = metrics.get("rvol", 1.0)
      if rvol_val >= 1.25:
        rvol_bullet = (
            f"🟢 **Volume Fuel (RVOL):** {rvol_val}x — High Institutional"
            " Conviction"
        )
      elif rvol_val >= 0.85:
        rvol_bullet = (
            f"⚪ **Volume Fuel (RVOL):** {rvol_val}x — Normal Trading Volume"
        )
      else:
        rvol_bullet = (
            f"🟡 **Volume Fuel (RVOL):** {rvol_val}x — Low Volume / Retail"
            " Churn"
        )

      # 3. Speed & Energy Factor (RSI)
      rsi_val = metrics.get("rsi", 50)
      if rsi_val >= 70:
        rsi_bullet = (
            f"🔴 **Speed & Energy (RSI {rsi_val}):** Overbought (Extended /"
            " Pullback Risk)"
        )
      elif rsi_val <= 30:
        rsi_bullet = (
            f"🟢 **Speed & Energy (RSI {rsi_val}):** Oversold (Potential Dip"
            " Value Entry)"
        )
      elif rsi_val >= 50:
        rsi_bullet = (
            f"🟢 **Speed & Energy (RSI {rsi_val}):** Positive Bullish"
            " Momentum"
        )
      else:
        rsi_bullet = (
            f"🟡 **Speed & Energy (RSI {rsi_val}):** Neutral to Weak Momentum"
        )

      # 4. Direction Factor (MACD)
      if metrics.get("macd_bullish", False):
        macd_bullet = (
            "🟢 **Direction (MACD):** Bullish (Momentum moving upward)"
        )
      else:
        macd_bullet = (
            "🔴 **Direction (MACD):** Bearish (Momentum slowing / downward)"
        )

      # 5. 52-Week Position Factor
      if range_pct >= 85:
        range_bullet = (
            f"🔴 **52-Wk Position ({range_pct:.0f}%):** Extended Near Highs"
            f" (Pullback Risk) *(Low: ${low_52:,.2f} | High: ${high_52:,.2f})*"
        )
      elif range_pct <= 20:
        range_bullet = (
            f"🟢 **52-Wk Position ({range_pct:.0f}%):** Near 52-Wk Lows"
            f" (Value Zone) *(Low: ${low_52:,.2f} | High: ${high_52:,.2f})*"
        )
      else:
        range_bullet = (
            f"⚪ **52-Wk Position ({range_pct:.0f}%):** Mid-Range"
            f" Consolidation *(Low: ${low_52:,.2f} | High: ${high_52:,.2f})*"
        )

      # Map factors to pull primary driver to the top
      factor_map = {
          "trend": trend_bullet,
          "rvol": rvol_bullet,
          "rsi": rsi_bullet,
          "macd": macd_bullet,
          "range": range_bullet,
      }

      # Determine primary key from reason string
      reason_str = str(metrics.get("reason", "")).lower()
      if "200" in reason_str or "trend" in reason_str:
        primary_key = "trend"
      elif "rsi" in reason_str or "overbought" in reason_str or "oversold" in reason_str:
        primary_key = "rsi"
      elif "macd" in reason_str:
        primary_key = "macd"
      elif "rvol" in reason_str or "volume" in reason_str:
        primary_key = "rvol"
      elif "52" in reason_str or "high" in reason_str or "low" in reason_str:
        primary_key = "range"
      else:
        primary_key = "trend"

      # Re-order list so Primary Driver is FIRST
      ordered_bullets = [factor_map[primary_key]] + [
          b for k, b in factor_map.items() if k != primary_key
      ]

      st.markdown(f"**Primary Driver:** {metrics['reason']}")
      for bullet in ordered_bullets:
        st.markdown(f"- {bullet}")

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
