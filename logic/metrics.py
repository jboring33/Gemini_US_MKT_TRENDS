import numpy as np
import pandas as pd

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    
    if avg_loss.iloc[-1] == 0:
        return 100.0
    
    rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
    return float(round(100 - (100 / (1 + rs)), 2))

def calculate_atr(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate 14-Day Average True Range (ATR) and % of price."""
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    
    current_price = df['Close'].iloc[-1]
    atr_pct = (atr / current_price) * 100
    
    return {
        "atr_val": float(round(atr, 2)),
        "atr_pct": float(round(atr_pct, 2))
    }

def calculate_moving_averages(prices: pd.Series) -> dict:
    """Compute 20, 50, and 200 EMAs + Trend alignments."""
    ema_20 = prices.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_50 = prices.ewm(span=50, adjust=False).mean().iloc[-1]
    ema_200 = prices.ewm(span=200, adjust=False).mean().iloc[-1]
    
    current = prices.iloc[-1]
    
    # Trend rules
    trend_20_50 = "20 EMA above 50 EMA (Bullish)" if ema_20 > ema_50 else "20 EMA below 50 EMA (Weakness)"
    trend_50_200 = "50 vs 200 EMA (Golden Alignment)" if ema_50 > ema_200 else "50 vs 200 EMA (Death Cross)"
    
    # Recommended Action
    if current > ema_20 and ema_20 > ema_50 and ema_50 > ema_200:
        action = "HOLD / ACCUMULATE"
        badge_style = "success"
    elif current < ema_50:
        action = "TRIM / PROTECT"
        badge_style = "warning"
    else:
        action = "NEUTRAL / WATCH"
        badge_style = "info"

    return {
        "ema_20": float(round(ema_20, 2)),
        "ema_50": float(round(ema_50, 2)),
        "ema_200": float(round(ema_200, 2)),
        "trend_20_50": trend_20_50,
        "trend_50_200": trend_50_200,
        "action": action,
        "badge_style": badge_style
    }
