import os
import json
from datetime import datetime
import pytz
import yfinance as yf
import pandas as pd

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
TICKERS = ["SPY", "DIA", "QQQ"]
TIMEZONE = "America/Denver"  # Mountain Time
SNAPSHOT_FILE = "last_run_snapshot.json"

# -----------------------------------------------------------------------------
# Calculation Helpers
# -----------------------------------------------------------------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50.0

def calculate_atr(df, period=14):
    df = df.copy()
    df['High-Low'] = df['High'] - df['Low']
    df['High-PrevClose'] = abs(df['High'] - df['Close'].shift(1))
    df['Low-PrevClose'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
    atr = df['TR'].rolling(window=period).mean()
    return atr.iloc[-1] if not atr.empty else 0.0

def evaluate_combined_status(current_price, low_52, high_52, market_cycle_phase):
    """
    Combines 52-Week Range Position AND Market Cycle Phase to evaluate overall color status.
    """
    if high_52 == low_52:
        pct = 0.0
    else:
        pct = (current_price - low_52) / (high_52 - low_52) * 100

    # 52-Week Rationale
    if pct >= 80:
        range_rationale = f"Trading in top 20% of 52-week range ({pct:.1f}%). Upper valuation extension limits headroom."
    elif pct >= 25:
        range_rationale = f"Mid-range position ({pct:.1f}%). Balanced technical headroom relative to annual extremes."
    else:
        range_rationale = f"Lower range position ({pct:.1f}%). Price is discounted relative to 52-week peak."

    # Combined Matrix: 52-Wk Range + Market Cycle Phase
    if pct >= 80 or market_cycle_phase == "Late Cycle / Overextended":
        combined_color = "red"
        bg_color = "#ffebe9" # Red
        text_color = "#cf222e"
        badge_text = "RED (High Risk / Trim)"
    elif pct >= 30 or market_cycle_phase == "Late Expansion":
        combined_color = "yellow"
        bg_color = "#fff8c5" # Yellow
        text_color = "#9a6700"
        badge_text = "YELLOW (Neutral / Caution)"
    else:
        combined_color = "green"
        bg_color = "#dafbe1" # Green
        text_color = "#1a7f37"
        badge_text = "GREEN (Accumulate / Value)"

    return pct, range_rationale, combined_color, bg_color, text_color, badge_text

def fetch_ticker_data(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2y")
    
    if hist.empty or len(hist) < 200:
        raise ValueError(f"Insufficient data for {symbol}")

    current_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    daily_change = current_price - prev_close
    daily_change_pct = (daily_change / prev_close) * 100

    # 52-Week High & Low
    one_yr_hist = hist.tail(252)
    high_52 = one_yr_hist['High'].max()
    low_52 = one_yr_hist['Low'].min()

    # Moving Averages
    sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
    sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
    sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    
    sma_20_prev = hist['Close'].rolling(window=20).mean().iloc[-2]
    sma_50_prev = hist['Close'].rolling(window=50).mean().iloc[-2]
    sma_200_prev = hist['Close'].rolling(window=200).mean().iloc[-2]

    # ETF Specific Market Cycle Assignment & Rationale
    etf_cycles = {
        "SPY": {
            "phase": "Late Expansion",
            "rationale": "Broad market supported by resilient mega-cap earnings, but valuation expansion is maturing."
        },
        "DIA": {
            "phase": "Mid-to-Late Expansion",
            "rationale": "Defensive value/industrial tilt providing stable dividend yields amid shifting macro trends."
        },
        "QQQ": {
            "phase": "Late Cycle / Overextended",
            "rationale": "High-beta growth tech leading momentum; vulnerable to rate spikes and profit-taking discipline."
        }
    }

    cycle_info = etf_cycles.get(symbol, {"phase": "Expansion", "rationale": "Standard economic expansion."})

    # Combined Assessment Calculation
    range_pct, range_rationale, combined_color, bg_color, text_color, badge_text = evaluate_combined_status(
        current_price, low_52, high_52, cycle_info["phase"]
    )

    # Crossover Logic
    cross_20_50 = "20-SMA Above 50-SMA (Bullish Trend)" if sma_20 > sma_50 else "20-SMA Below 50-SMA (Short-term Weakness)"
    if sma_20_prev <= sma_50_prev and sma_20 > sma_50:
        cross_20_50 = "Bullish Cross: 20-SMA crossed ABOVE 50-SMA"
    elif sma_20_prev >= sma_50_prev and sma_20 < sma_50:
        cross_20_50 = "Bearish Cross: 20-SMA crossed BELOW 50-SMA"

    cross_50_200 = "50-SMA Above 200-SMA (Golden Alignment)" if sma_50 > sma_200 else "50-SMA Below 200-SMA (Bear Alignment)"
    action_signal = "HOLD"
    if sma_50_prev <= sma_200_prev and sma_50 > sma_200:
        cross_50_200 = "Golden Cross (50 Crossed Above 200)"
        action_signal = "BUY"
    elif sma_50_prev >= sma_200_prev and sma_50 < sma_200:
        cross_50_200 = "Death Cross (50 Crossed Below 200)"
        action_signal = "SELL / TRIM"
    else:
        if current_price > sma_200 and sma_50 > sma_200:
            action_signal = "HOLD / ACCUMULATE"
        elif current_price < sma_200 and sma_50 < sma_200:
            action_signal = "REDUCE / SWEEP CASH"

    rsi = calculate_rsi(hist['Close'], period=14)
    atr = calculate_atr(hist, period=14)

    rsi_status = "Neutral (30-70)"
    if rsi >= 70:
        rsi_status = "Overbought (>70)"
    elif rsi <= 30:
        rsi_status = "Oversold (<30)"

    # Section 2 ATR Rationale
    atr_pct = (atr / current_price) * 100
    atr_rationale = f"14-Day ATR of ${atr:.2f} represents ~{atr_pct:.2f}% expected daily price fluctuation. "
    if atr_pct > 1.2:
        atr_rationale += "Elevated short-term volatility; widen trailing stop thresholds to prevent unwanted shakeouts."
    else:
        atr_rationale += "Normal volatility environment; structure standard risk parameters."

    return {
        "symbol": symbol,
        "price": current_price,
        "change": daily_change,
        "change_pct": daily_change_pct,
        "high_52": high_52,
        "low_52": low_52,
        "range_pct": range_pct,
        "range_rationale": range_rationale,
        "cycle_phase": cycle_info["phase"],
        "cycle_rationale": cycle_info["rationale"],
        "combined_color": combined_color,
        "bg_color": bg_color,
        "text_color": text_color,
        "badge_text": badge_text,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "rsi": rsi,
        "rsi_status": rsi_status,
        "atr": atr,
        "atr_rationale": atr_rationale,
        "cross_20_50": cross_20_50,
        "cross_50_200": cross_50_200,
        "action_signal": action_signal
    }

def fetch_vix_data():
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="5d")
    if not hist.empty:
        val = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        return val, val - prev
    return 18.00, 0.00

def load_previous_snapshot():
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_snapshot(data, vix_val):
    snapshot = {item["symbol"]: item["price"] for item in data}
    snapshot["VIX"] = vix_val
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)

# -----------------------------------------------------------------------------
# HTML Report Generator
# -----------------------------------------------------------------------------
def generate_html(data, vix_val, vix_change, prev_snapshot, update_time_str):
    prev_vix = prev_snapshot.get("VIX")
    if prev_vix is not None:
        vix_delta = vix_val - prev_vix
        vix_delta_str = f"{'+' if vix_delta >= 0 else ''}{vix_delta:.2f}"
    else:
        vix_delta_str = f"{'+' if vix_change >= 0 else ''}{vix_change:.2f}"

    cards_html = ""
    sec2_columns = ""
    sec4_columns = ""
    sec5_columns = ""
    sec6_columns = ""

    sec4_details = {
        "SPY": {
            "target": "50% Core Allocation",
            "steps": [
                "Trim 2.5% when 52-wk range > 85% to maintain preservation target.",
                "Sweep proceeds into short-term cash equivalents.",
                "Re-enter on dips near 200-day SMA ($" + f"{data[0]['sma_200']:.2f}" + ")."
            ]
        },
        "DIA": {
            "target": "20% Value Baseline",
            "steps": [
                "Maintain defensive posture for yield stability.",
                "Rebalance when RSI crosses extreme levels (>70 or <30).",
                "Deploy accrued dividends to preserve baseline exposure."
            ]
        },
        "QQQ": {
            "target": "10% Growth Ceiling",
            "steps": [
                "Cap max exposure to limit high-beta drawdown risk.",
                "Enforce strict stop/trim rules when RSI > 70.",
                "Harvest tech gains into cash equivalents during late-cycle expansion."
            ]
        }
    }

    sec6_details = {
        "SPY": {"downside": "Moderate Drawdown Risk", "support": f"${data[0]['sma_200']:.2f} (200-SMA)", "action": "Trailing Stop / Cash Sweep"},
        "DIA": {"downside": "Low-Moderate Drawdown Risk", "support": f"${data[1]['sma_200']:.2f} (200-SMA)", "action": "Hold Value Base"},
        "QQQ": {"downside": "Elevated High-Beta Risk", "support": f"${data[2]['sma_200']:.2f} (200-SMA)", "action": "Trim on Overbought Signals"}
    }

    for item in data:
        symbol = item["symbol"]
        price = item["price"]
        change = item["change"]
        
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

        # Section 1: Executive Summary (Full Card Background Colored)
        cards_html += f"""
        <div class="card" style="background-color: {item['bg_color']}; border: 1px solid #d0d7de;">
            <div class="card-header">
                <h3 style="margin:0; font-size: 22px;">{symbol}</h3>
                <span class="badge" style="background-color: #ffffff; color: {item['text_color']}; border: 1px solid {item['text_color']}; font-weight: bold;">
                    {item['badge_text']}
                </span>
            </div>
            <div class="price-main">${price:.2f}</div>
            <div class="price-change" style="color: {change_color};">
                {change_sign}${change:.2f} ({change_sign}{item['change_pct']:.2f}%)
            </div>
            
            <div class="info-block" style="border-top: 1px solid rgba(0,0,0,0.1); padding-top: 8px; margin-top: 8px; font-size: 13px;">
                <strong>52-Wk Range ({item['range_pct']:.1f}%):</strong> ${item['low_52']:.2f} - ${item['high_52']:.2f}
                <div style="font-size: 12px; margin-top: 2px; color: #333;">{item['range_rationale']}</div>
            </div>

            <div class="info-block" style="border-top: 1px solid rgba(0,0,0,0.1); padding-top: 8px; margin-top: 8px; font-size: 13px;">
                <strong>Market Cycle:</strong> {item['cycle_phase']}
                <div style="font-size: 12px; margin-top: 2px; color: #333;">{item['cycle_rationale']}</div>
            </div>

            <div class="delta-info" style="border-top: 1px solid rgba(0,0,0,0.1); margin-top: 8px; padding-top: 6px; font-size: 12px;">
                <span>Since Last Run:</span> 
                <strong style="color: {delta_color};">{delta_str}</strong>
            </div>
        </div>
        """

        # Section 2: Technical Volatility Profile (ATR Rationale Focus)
        sec2_columns += f"""
        <div class="column-card" style="background-color: #ffffff; border: 1px solid #d0d7de;">
            <div class="column-title" style="color: #0969da; border-bottom: 2px solid #0969da; font-weight: bold;">
                {symbol} Volatility Analysis
            </div>
            <div class="metric-row">
                <span>14-Day ATR Value:</span> <strong>${item['atr']:.2f}</strong>
            </div>
            <div class="comment-box" style="margin-top: 12px; font-size: 13px; color: #24292f; line-height: 1.4;">
                <strong>ATR Rationale:</strong> {item['atr_rationale']}
            </div>
        </div>
        """

        # Section 4: Conservative Allocation Roadmap
        s4 = sec4_details[symbol]
        sec4_columns += f"""
        <div class="column-card">
            <div class="column-title">{symbol} Target: {s4['target']}</div>
            <p><strong>Actionable Steps:</strong></p>
            <ul class="custom-list">
                <li>{s4['steps'][0]}</li>
                <li>{s4['steps'][1]}</li>
                <li>{s4['steps'][2]}</li>
            </ul>
        </div>
        """

        # Section 5: Moving Averages, RSI-14 & Crossover Signals
        sec5_columns += f"""
        <div class="column-card">
            <div class="column-title">{symbol} Technical Indicators</div>
            <div class="metric-row"><span>20-Day SMA:</span> <strong>${item['sma_20']:.2f}</strong></div>
            <div class="metric-row"><span>50-Day SMA:</span> <strong>${item['sma_50']:.2f}</strong></div>
            <div class="metric-row"><span>200-Day SMA:</span> <strong>${item['sma_200']:.2f}</strong></div>
            <div class="metric-row"><span>RSI (14):</span> <strong>{item['rsi']:.1f} ({item['rsi_status']})</strong></div>
            <div class="metric-row" style="margin-top: 8px;"><span>20 vs 50 SMA:</span> <strong style="font-size: 11px;">{item['cross_20_50']}</strong></div>
            <div class="metric-row"><span>50 vs 200 SMA:</span> <strong style="font-size: 11px;">{item['cross_50_200']}</strong></div>
            <div class="signal-badge" style="background-color: {'#dafbe1' if 'BUY' in item['action_signal'] or 'HOLD' in item['action_signal'] else '#ffebe9'}; color: {'#1a7f37' if 'BUY' in item['action_signal'] or 'HOLD' in item['action_signal'] else '#cf222e'};">
                Action: {item['action_signal']}
            </div>
        </div>
        """

        # Section 6: ETF Downside Risk Profiles
        s6 = sec6_details[symbol]
        sec6_columns += f"""
        <div class="column-card">
            <div class="column-title">{symbol} Downside Profile</div>
            <div class="metric-row"><span>Risk Rating:</span> <strong style="color: #cf222e;">{s6['downside']}</strong></div>
            <div class="metric-row"><span>Key Support:</span> <strong>{s6['support']}</strong></div>
            <div class="metric-row"><span>Risk Rule:</span> <strong>{s6['action']}</strong></div>
        </div>
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
            max-width: 1050px;
            margin: 0 auto;
        }}
        .header {{
            margin-bottom: 24px;
            border-bottom: 1px solid #d0d7de;
            padding-bottom: 12px;
        }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
        .header .timestamp {{ color: #57606a; font-size: 14px; }}
        
        .three-column-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}

        @media (max-width: 768px) {{
            .three-column-grid {{ grid-template-columns: 1fr; }}
        }}

        .card, .column-card {{
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            background: #ffffff;
            border: 1px solid #d0d7de;
        }}

        .column-title {{
            font-size: 16px;
            font-weight: bold;
            border-bottom: 2px solid #0969da;
            padding-bottom: 6px;
            margin-bottom: 12px;
            color: #0969da;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .price-main {{ font-size: 28px; font-weight: bold; margin-bottom: 4px; }}
        .price-change {{ font-size: 14px; font-weight: 600; margin-bottom: 8px; }}
        
        .badge, .signal-badge {{
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 600;
            display: inline-block;
        }}
        .signal-badge {{ font-size: 13px; padding: 6px 12px; margin-top: 12px; font-weight: bold; width: 100%; text-align: center; box-sizing: border-box; }}

        .metric-row {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            padding: 6px 0;
            border-bottom: 1px dashed #e1e4e8;
        }}

        .section-box {{
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .section-box h2 {{ margin-top: 0; font-size: 18px; border-bottom: 1px solid #eaecef; padding-bottom: 8px; color: #24292f; }}
        
        .macro-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        .macro-item {{
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #d0d7de;
        }}
        .macro-label {{ font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; opacity: 0.8; }}
        .macro-value {{ font-size: 14px; font-weight: bold; margin-bottom: 6px; }}
        .macro-comment {{ font-size: 12px; line-height: 1.3; opacity: 0.9; }}

        ul.custom-list {{ margin: 8px 0; padding-left: 18px; color: #24292f; line-height: 1.5; font-size: 13px; }}
        ul.custom-list li {{ margin-bottom: 6px; }}

        .vix-banner {{
            background: #f8f9fa;
            border-left: 4px solid #0969da;
            padding: 12px 16px;
            margin-bottom: 16px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Market Dashboard (SPY / DIA / QQQ)</h1>
            <div class="timestamp">Last Updated: {update_time_str} Mountain Time</div>
        </div>

        <!-- Section 1: Executive Summary & Combined Status Matrix -->
        <h2>1. Executive Summary & Combined Status Matrix</h2>
        <div class="three-column-grid">
            {cards_html}
        </div>

        <!-- Section 2: Technical Volatility Profile (14-ATR Rationale) -->
        <h2>2. Volatility Analysis (14-ATR Rationale)</h2>
        <div class="three-column-grid">
            {sec2_columns}
        </div>

        <!-- Section 3: Macro & Valuation Context (10 Core Indicators) -->
        <div class="section-box">
            <h2>3. Macro & Valuation Context (10 Core Indicators)</h2>
            <div class="macro-grid">
                
                <!-- Red / High Risk Indicators -->
                <div class="macro-item" style="background-color: #ffebe9; color: #cf222e;">
                    <div class="macro-label">1. Shiller CAPE Ratio</div>
                    <div class="macro-value">41.05 (Elevated)</div>
                    <div class="macro-comment">Top quintile historically; suggests limited long-term valuation expansion.</div>
                </div>

                <div class="macro-item" style="background-color: #ffebe9; color: #cf222e;">
                    <div class="macro-label">2. Fed Balance Sheet</div>
                    <div class="macro-value">QT Ongoing</div>
                    <div class="macro-comment">Continued balance sheet runoff drains net systemic liquidity over time.</div>
                </div>

                <div class="macro-item" style="background-color: #ffebe9; color: #cf222e;">
                    <div class="macro-label">3. S&P Dividend Yield</div>
                    <div class="macro-value">1.25% (Low)</div>
                    <div class="macro-comment">Below long-term averages; offers negligible downside yield support.</div>
                </div>

                <!-- Yellow / Neutral Indicators -->
                <div class="macro-item" style="background-color: #fff8c5; color: #9a6700;">
                    <div class="macro-label">4. Yield Curve (10Y-2Y)</div>
                    <div class="macro-value">Un-inverting</div>
                    <div class="macro-comment">Transitioning out of inversion; historically warrants late-cycle caution.</div>
                </div>

                <div class="macro-item" style="background-color: #fff8c5; color: #9a6700;">
                    <div class="macro-label">5. Fed Funds Rate</div>
                    <div class="macro-value">Restrictive Horizon</div>
                    <div class="macro-comment">Rates remain elevated above neutral level to curb lingering inflation.</div>
                </div>

                <div class="macro-item" style="background-color: #fff8c5; color: #9a6700;">
                    <div class="macro-label">6. Inflation CPI</div>
                    <div class="macro-value">Moderating</div>
                    <div class="macro-comment">Trending toward policy target, but service sector stickiness persists.</div>
                </div>

                <div class="macro-item" style="background-color: #fff8c5; color: #9a6700;">
                    <div class="macro-label">7. Consumer Sentiment</div>
                    <div class="macro-value">Rangebound</div>
                    <div class="macro-comment">Balanced between steady labor markets and higher living costs.</div>
                </div>

                <div class="macro-item" style="background-color: #fff8c5; color: #9a6700;">
                    <div class="macro-label">8. US Dollar (DXY)</div>
                    <div class="macro-value">Stable Range</div>
                    <div class="macro-comment">Neutral impact on multinational corporate earnings performance.</div>
                </div>

                <!-- Green / Low Risk Indicators -->
                <div class="macro-item" style="background-color: #dafbe1; color: #1a7f37;">
                    <div class="macro-label">9. High Yield Spreads</div>
                    <div class="macro-value">Tight (Low Stress)</div>
                    <div class="macro-comment">Credit markets signal minimal immediate default risk or liquidity freeze.</div>
                </div>

                <div class="macro-item" style="background-color: #dafbe1; color: #1a7f37;">
                    <div class="macro-label">10. Real GDP Growth</div>
                    <div class="macro-value">Positive Expansion</div>
                    <div class="macro-comment">Economic activity continues to support underlying corporate earnings.</div>
                </div>

            </div>
        </div>

        <!-- Section 4: Conservative Allocation Execution Roadmap -->
        <div class="section-box">
            <h2>4. Conservative Allocation & Execution Roadmap</h2>
            <div class="three-column-grid">
                {sec4_columns}
            </div>
        </div>

        <!-- Section 5: Moving Averages, RSI-14 & Crossover Signals -->
        <div class="section-box">
            <h2>5. Moving Averages, RSI-14 & Crossover Signals</h2>
            <div class="three-column-grid">
                {sec5_columns}
            </div>
        </div>

        <!-- Section 6: Volatility & ETF Downside Risk -->
        <div class="section-box">
            <h2>6. Volatility & ETF Downside Risk</h2>
            <div class="vix-banner">
                <div>
                    <strong>CBOE Volatility Index (VIX):</strong> <span style="font-size: 20px; font-weight: bold; margin-left: 8px;">{vix_val:.2f}</span>
                </div>
                <div>
                    <strong>Delta Since Last Run:</strong> 
                    <span style="font-size: 16px; font-weight: bold; color: {'#cf222e' if vix_change >= 0 else '#1a7f37'}; margin-left: 6px;">{vix_delta_str}</span>
                </div>
            </div>
            <div class="three-column-grid">
                {sec6_columns}
            </div>
        </div>

        <!-- Section 7: Action Pipeline Checkpoints -->
        <div class="section-box">
            <h2>7. Decision Pipeline & Execution Rules</h2>
            <ul class="custom-list">
                <li><strong>52-Week Range Threshold:</strong> When index status remains tagged in the <span style="color: #cf222e; font-weight: bold;">RED zone (≥80%)</span>, sweep gains into cash equivalents.</li>
                <li><strong>Crossover Action Rule:</strong> On 50/200 SMA <strong>Death Cross</strong>, automatically scale back allocation target by 50%. On <strong>Golden Cross</strong>, hold/accumulate core target.</li>
                <li><strong>Overbought RSI Discipline:</strong> When RSI (14) > 70, pause new capital injections into high-beta indices (QQQ).</li>
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

    vix_val, vix_change = fetch_vix_data()

    prev_snapshot = load_previous_snapshot()
    generate_html(market_data, vix_val, vix_change, prev_snapshot, update_time_str)
    save_current_snapshot(market_data, vix_val)
    print("Report generated successfully with all sections intact and updated!")

if __name__ == "__main__":
    main()
