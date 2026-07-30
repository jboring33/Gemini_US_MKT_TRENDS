import os
import json
from datetime import datetime
import pytz
import yfinance as yf

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
TICKERS = ["SPY", "DIA", "QQQ"]
TIMEZONE = "America/Denver"  # Mountain Time
SNAPSHOT_FILE = "last_run_snapshot.json"

# -----------------------------------------------------------------------------
# Data Processing Helpers
# -----------------------------------------------------------------------------
def get_range_color_and_status(current_price, low_52, high_52):
    """
    Calculates position within 52-week range.
    Red: >= 80% (Near Highs)
    Yellow: 25% - 80%
    Green: < 25% (Near Lows)
    """
    if high_52 == low_52:
        pct = 0.0
    else:
        pct = (current_price - low_52) / (high_52 - low_52) * 100

    if pct >= 80:
        return "red", f"{pct:.1f}% (High Range)", "#ffebe9", "#cf222e"
    elif pct >= 25:
        return "yellow", f"{pct:.1f}% (Mid Range)", "#fff8c5", "#9a6700"
    else:
        return "green", f"{pct:.1f}% (Low Range)", "#dafbe1", "#1a7f37"

def fetch_ticker_data(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1y")
    
    if hist.empty:
        raise ValueError(f"Could not fetch data for {symbol}")

    current_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
    daily_change = current_price - prev_close
    daily_change_pct = (daily_change / prev_close) * 100

    high_52 = hist['High'].max()
    low_52 = hist['Low'].min()

    color, status_text, bg_color, text_color = get_range_color_and_status(current_price, low_52, high_52)

    return {
        "symbol": symbol,
        "name": ticker.info.get("shortName", symbol),
        "price": current_price,
        "change": daily_change,
        "change_pct": daily_change_pct,
        "high_52": high_52,
        "low_52": low_52,
        "range_color": color,
        "range_status": status_text,
        "bg_color": bg_color,
        "text_color": text_color
    }

def load_previous_snapshot():
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_snapshot(data):
    snapshot = {item["symbol"]: item["price"] for item in data}
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)

# -----------------------------------------------------------------------------
# HTML Report Generator
# -----------------------------------------------------------------------------
def generate_html(data, prev_snapshot, update_time_str):
    cards_html = ""
    table_rows = ""

    for item in data:
        symbol = item["symbol"]
        price = item["price"]
        change = item["change"]
        change_pct = item["change_pct"]
        
        # Delta calculation from last run
        prev_price = prev_snapshot.get(symbol)
        if prev_price is not None:
            delta = price - prev_price
            delta_str = f"{'+' if delta >= 0 else ''}${delta:.2f}"
            delta_color = "#1a7f37" if delta >= 0 else "#cf222e"
        else:
            delta_str = "First Run (N/A)"
            delta_color = "#57606a"

        change_color = "#1a7f37" if change >= 0 else "#cf222e"
        change_sign = "+" if change >= 0 else ""

        # Summary Cards (Top Section)
        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <h3>{symbol}</h3>
                <span class="badge" style="background-color: {item['bg_color']}; color: {item['text_color']};">
                    {item['range_status']}
                </span>
            </div>
            <div class="price-main">${price:.2f}</div>
            <div class="price-change" style="color: {change_color};">
                {change_sign}${change:.2f} ({change_sign}{change_pct:.2f}%)
            </div>
            <div class="delta-info">
                <span>Since Last Run:</span> 
                <strong style="color: {delta_color};">{delta_str}</strong>
            </div>
        </div>
        """

        # Detailed Breakdown Table (Bottom Section)
        table_rows += f"""
        <tr>
            <td><strong>{symbol}</strong></td>
            <td>${price:.2f}</td>
            <td style="color: {change_color};">{change_sign}${change:.2f} ({change_sign}{change_pct:.2f}%)</td>
            <td>${item['low_52']:.2f} - ${item['high_52']:.2f}</td>
            <td>
                <span class="badge" style="background-color: {item['bg_color']}; color: {item['text_color']};">
                    {item['range_color'].upper()}
                </span>
            </td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f6f8fa;
            color: #24292f;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            margin-bottom: 24px;
            border-bottom: 1px solid #d0d7de;
            padding-bottom: 12px;
        }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
        .header .timestamp {{ color: #57606a; font-size: 14px; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .card-header h3 {{ margin: 0; font-size: 18px; }}
        .price-main {{ font-size: 28px; font-weight: bold; margin-bottom: 4px; }}
        .price-change {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; }}
        .delta-info {{ font-size: 12px; color: #57606a; border-top: 1px solid #f0f0f0; padding-top: 8px; }}
        
        .badge {{
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 600;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #d0d7de;
        }}
        th {{ background-color: #f6f8fa; font-size: 12px; text-transform: uppercase; color: #57606a; }}
        tr:last-child td {{ border-bottom: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Market Dashboard (SPY / DIA / QQQ)</h1>
            <div class="timestamp">Last Updated: {update_time_str} Mountain Time</div>
        </div>

        <div class="grid">
            {cards_html}
        </div>

        <h2>Technical Details & 52-Week Ranges</h2>
        <table>
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Current Price</th>
                    <th>Daily Change</th>
                    <th>52-Week Range (Low - High)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    with open("index.html", "w") as f:
        f.write(html_content)

# -----------------------------------------------------------------------------
# Main Execution Workflow
# -----------------------------------------------------------------------------
def main():
    tz = pytz.timezone(TIMEZONE)
    now_mt = datetime.now(tz)
    update_time_str = now_mt.strftime("%Y-%m-%d %I:%M:%S %p %Z")

    print(f"Fetching market data for {TICKERS}...")
    market_data = []
    for symbol in TICKERS:
        try:
            data = fetch_ticker_data(symbol)
            market_data.append(data)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    prev_snapshot = load_previous_snapshot()
    generate_html(market_data, prev_snapshot, update_time_str)
    save_current_snapshot(market_data)
    print("Report generated successfully in index.html!")

if __name__ == "__main__":
    main()
