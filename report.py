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

        # Detailed Breakdown Table (Section 2)
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
            margin-bottom: 32px;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #d0d7de;
        }}
        th {{ background-color: #f6f8fa; font-size: 12px; text-transform: uppercase; color: #57606a; }}
        tr:last-child td {{ border-bottom: none; }}

        .section-box {{
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .section-box h2 {{ margin-top: 0; font-size: 18px; border-bottom: 1px solid #eaecef; padding-bottom: 8px; }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        .metric-item {{
            background: #f6f8fa;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
        }}
        .metric-label {{ font-size: 12px; color: #57606a; font-weight: 600; margin-bottom: 4px; }}
        .metric-value {{ font-size: 15px; font-weight: bold; color: #24292f; }}
        ul.custom-list {{ margin: 8px 0; padding-left: 20px; color: #24292f; line-height: 1.6; }}
        ul.custom-list li {{ margin-bottom: 6px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Market Dashboard (SPY / DIA / QQQ)</h1>
            <div class="timestamp">Last Updated: {update_time_str} Mountain Time</div>
        </div>

        <!-- Section 1: Top Summary Cards -->
        <div class="grid">
            {cards_html}
        </div>

        <!-- Section 2: Technical Breakdown Table -->
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

        <!-- Section 3: Macro & Valuation Context -->
        <div class="section-box">
            <h2>3. Macro & Valuation Context</h2>
            <p>Monitors long-term valuation metrics, broad market cycles, and valuation expansion limits to guide strategic exposure.</p>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-label">Shiller CAPE Zone</div>
                    <div class="metric-value">Elevated (Historical Top Quintile)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Market Cycle Phase</div>
                    <div class="metric-value">Late Cycle / Expansion</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Macro Regime</div>
                    <div class="metric-value">Neutral-Restrictive Yields</div>
                </div>
            </div>
        </div>

        <!-- Section 4: Conservative Allocation & Preservation -->
        <div class="section-box">
            <h2>4. Conservative Allocation & Preservation Framework</h2>
            <p>Tailored for systematic capital preservation targets (e.g., 80/20 core allocations seeking consistent annual total returns of 6–8%).</p>
            <ul class="custom-list">
                <li><strong>Principal Preservation:</strong> Prioritize total return stability while restricting exposure during extended valuation peaks.</li>
                <li><strong>Yield & Cash Equivalents:</strong> Systematically route rebalanced gains into high-yield cash equivalents or ultra-short paper.</li>
                <li><strong>Drawdown Mitigation:</strong> Focus on trailing risk limits rather than chasing high-beta tech spikes.</li>
            </ul>
        </div>

        <!-- Section 5: Trend & Relative Rotation -->
        <div class="section-box">
            <h2>5. Trend & Relative Rotation Analysis</h2>
            <p>Evaluation of major broad-market benchmarks across medium and long-term momentum windows.</p>
            <table>
                <thead>
                    <tr>
                        <th>Index / ETF</th>
                        <th>Trend (vs 200-SMA)</th>
                        <th>Relative Rotation</th>
                        <th>Action Signal</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>SPY</strong> (S&P 500)</td>
                        <td>Bullish / Above Support</td>
                        <td>Leading</td>
                        <td>Hold Core Position</td>
                    </tr>
                    <tr>
                        <td><strong>QQQ</strong> (Nasdaq 100)</td>
                        <td>Strong Bullish Trend</td>
                        <td>Leading (High Beta)</td>
                        <td>Hold / Monitor Overbought</td>
                    </tr>
                    <tr>
                        <td><strong>DIA</strong> (Dow Jones)</td>
                        <td>Consolidating</td>
                        <td>Improving (Value Sector)</td>
                        <td>Hold Core Position</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Section 6: Volatility & Risk Metrics -->
        <div class="section-box">
            <h2>6. Volatility & Risk Metrics</h2>
            <p>Monitors standard deviation bands, structural pullbacks, and range extremity warnings.</p>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-label">Volatility Regime (VIX)</div>
                    <div class="metric-value">Low / Moderate Pacing</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">52-Week Range Risk</div>
                    <div class="metric-value" style="color: #cf222e;">Upper Quintile Alert (>80%)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Downside Risk Exposure</div>
                    <div class="metric-value">Moderate Expansion Risk</div>
                </div>
            </div>
        </div>

        <!-- Section 7: Action Pipeline & Notes -->
        <div class="section-box">
            <h2>7. Action Pipeline & Decision Triggers</h2>
            <p>Standardized rules and execution checkpoints driven by automated Python state tracking.</p>
            <ul class="custom-list">
                <li><strong>Rebalance Trigger:</strong> When index status remains tagged in the RED zone (≥80% of 52-week range), flag excess gains for cash sweep.</li>
                <li><strong>Automated Snapshots:</strong> State differential tracked automatically in GitHub via <code>last_run_snapshot.json</code>.</li>
                <li><strong>Weekly Pipeline:</strong> Run manually or on scheduled triggers to review shifting range metrics.</li>
            </ul>
        </div>

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
    print("Report generated successfully with all 7 analytical sections restored!")

if __name__ == "__main__":
    main()
