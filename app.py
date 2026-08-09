import streamlit as st
import yfinance as yf
import pandas as pd
from logic.metrics import evaluate_trend_and_action, create_interactive_chart
from logic.macro_data import get_macro_risk_indicators

# -------------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="ETF Strategy Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 ETF Strategy & Market Dashboard")

# -------------------------------------------------------------------
# Data Retrieval Helper
# -------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------------
# Sidebar Controls
# -------------------------------------------------------------------
with st.sidebar:
    st.header("Dashboard Settings")
    selected_indices = st.multiselect(
        "Major Index ETFs",
        options=["SPY", "QQQ", "DIA", "IWM"],
        default=["SPY", "QQQ", "DIA"]
    )
    lookback = st.selectbox("History Period", options=["6m", "1y", "2y"], index=1)

# -------------------------------------------------------------------
# SECTION 1: Major Index Technical & Risk Matrix
# -------------------------------------------------------------------
st.subheader("Section 1: Major Index Technical & Risk Matrix")

if selected_indices:
    cols = st.columns(len(selected_indices))
    
    for col, ticker in zip(cols, selected_indices):
        df = fetch_data(ticker, period=lookback)
        
        if not df.empty:
            eval_data = evaluate_trend_and_action(df)
            
            with col:
                st.markdown(f"### **{ticker}**")
                
                # Action Badge
                badge_type = eval_data.get("badge", "info")
                action_text = eval_data.get("action", "HOLD")
                
                if badge_type == "success":
                    st.success(f"**{action_text}**")
                elif badge_type == "warning":
                    st.warning(f"**{action_text}**")
                elif badge_type == "error":
                    st.error(f"**{action_text}**")
                else:
                    st.info(f"**{action_text}**")
                
                st.caption(f"**Reason:** {eval_data.get('reason', 'N/A')}")
                
                # Metric Grid
                m1, m2 = st.columns(2)
                m1.metric("Price", f"${eval_data['curr_price']:.2f}")
                m2.metric("RVOL", f"{eval_data['rvol']}x")
                
                m3, m4 = st.columns(2)
                m3.metric("RSI (14)", f"{eval_data['rsi']}")
                m4.metric("MACD", "Bullish" if eval_data["macd_bullish"] else "Bearish")
                
                # ATR Trailing Stop Card Metric
                st.markdown("---")
                st.metric(
                    label="2x ATR Trailing Stop",
                    value=f"${eval_data['atr_stop']:.2f}",
                    delta=f"14D Vol: {eval_data['atr_pct']}% (${eval_data['atr_val']})",
                    delta_color="off"
                )

st.markdown("---")

# -------------------------------------------------------------------
# SECTION 2: Interactive Technical Charting
# -------------------------------------------------------------------
st.subheader("Section 2: Technical Chart")

focus_ticker = st.selectbox("Select Ticker for Detailed Breakdown", options=selected_indices, index=0 if selected_indices else None)

if focus_ticker:
    chart_df = fetch_data(focus_ticker, period=lookback)
    if not chart_df.empty:
        fig = create_interactive_chart(chart_df, focus_ticker)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------------
# SECTION 4: Macro & Economic Regime Cards (Including VIX)
# -------------------------------------------------------------------
st.subheader("Section 4: Macro & Economic Regime Cards")

macro_cards = get_macro_risk_indicators()
macro_cols = st.columns(2)

for i, card in enumerate(macro_cards):
    with macro_cols[i % 2]:
        st.markdown(f"#### {card['title']}")
        
        status_color = card.get("color", "info")
        if status_color == "green":
            st.success(f"Status:")
        elif status_color == "yellow":
            st.warning(f"Status:")
        elif status_color == "red":
            st.error(f"Status:")
        else:
            st.info(f"Status:")
            
        st.write(card["detail"])
        st.markdown("---")
