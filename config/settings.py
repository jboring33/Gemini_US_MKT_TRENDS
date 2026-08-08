# Tickers & Market Parameters
PRIMARY_TICKERS = ["SPY", "DIA", "QQQ"]
VOLATILITY_TICKER = "^VIX"

# Default Cache Time-to-Live (Seconds)
# Set to 300 seconds (5 minutes) to avoid hitting yfinance rate limits
CACHE_TTL = 300

# Technical Thresholds & Lookbacks
RSI_PERIOD = 14
ATR_PERIOD = 14
EMA_PERIODS = [20, 50, 200]
