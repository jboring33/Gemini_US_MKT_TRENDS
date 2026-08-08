import os
import json
from datetime import datetime
import pytz
import pandas as pd
import yfinance as yf

# -----------------------------------------------------------------------------
# Configuration & Setup
# -----------------------------------------------------------------------------
# Default ticker universe to track
TICKERS = ["VFLO", "SCHD", "SCYB", "JPST", "JAAA", "^GSPC", "^IXIC", "^VIX"]

TIMEZONE = pytz.timezone("US/Eastern")
NOW = datetime.now(TIMEZONE)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def calculate_rsi(series: pd.Series, period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI) with zero-division protection."""
    if len(series) < period + 1:
        return 50.0  # Neutral fallback if insufficient data
    
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    last_loss = loss.iloc[-1]
    last_gain = gain.iloc[-1]

    if last_loss == 0:
        return 100.0 if last_gain > 0 else 50.0

    rs = last_gain / last_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def get_market_data(tickers):
    """Fetch market history and compute key metrics for each ticker."""
    report_data = []
    
    for ticker in tickers:
        try:
            tk = yf.Ticker(ticker)
            # Fetch 30 days of daily history to ensure enough data for 14-period RSI
            hist = tk.history(period="30d")
            
            if hist.empty or len(hist) < 2:
                print(f"Warning: Insufficient data for {ticker}")
                continue

            current_price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100

            rsi_val = calculate_rsi(hist["Close"])

            report_data.append({
                "ticker": ticker,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "pct_change": round(pct_change, 2),
                "rsi": rsi_val
            })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            
    return report_data


def generate_html(data, timestamp):
    """Generate a clean, responsive single-file HTML report."""
    rows_html = ""
    for item in data:
        # Determine color formatting for percentage change
        if item["pct_change"] > 0:
            change_class = "positive"
            prefix = "+"
        elif item["pct_change"] < 0:
            change_class = "negative"
            prefix = ""
        else:
            change_class = "neutral"
            prefix = ""

        # Specific styling for VIX if desired, otherwise standard price reporting
        rows_html += f"""
        <tr>
            <td><strong>{item['ticker']}</strong></td>
            <td>${item['price']:,.2f}</td>
            <td class="{change_class}">{prefix}{item['change']:,.2f} ({prefix}{item['pct_change']:.2f}%)</td>
            <td>{item['rsi']}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Overview Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8f9fa;
            color: #212529;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        h1 {{
            margin-top: 0;
            font-size: 24px;
            color: #1a1a1a;
        }}
        .timestamp {{
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f1f3f5;
            font-weight: 600;
        }}
        .positive {{ color: #2b8a3e; font-weight: 600; }}
        .negative {{ color: #c92a2a; font-weight: 600; }}
        .neutral {{ color: #495057; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Market Dashboard</h1>
        <div class="timestamp">Last Updated: {timestamp}</div>
        <table>
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Price</th>
                    <th>Change (%)</th>
                    <th>RSI (14)</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return html_content

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
def main():
    print("Fetching market data...")
    data = get_market_data(TICKERS)
    
    timestamp_str = NOW.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # 1. Save state snapshot as JSON
    snapshot = {
        "updated_at": timestamp_str,
        "data": data
    }
    with open("last_run_snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2)
    print("Saved last_run_snapshot.json")

    # 2. Render and save index.html
    html = generate_html(data, timestamp_str)
    with open("index.html", "w") as f:
        f.write(html)
    print("Saved index.html")

if __name__ == "__main__":
    main()
