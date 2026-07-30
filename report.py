import json
import os
from datetime import datetime
from string import Template

# Snapshot JSON filenames
SNAPSHOT_MACRO = "last_run_macro.json"
SNAPSHOT_RETIREE = "last_run_retiree.json"
SNAPSHOT_TECHNICAL = "last_run_technical.json"


# --- FILE I/O HELPERS ---

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# --- DATA ACQUISITION & COMPUTATION ---

def get_current_data():
    dt_local = datetime.now().astimezone()
    today = dt_local.strftime("%Y-%m-%d")

    return {
        "run_date": today,

        # SPY (ETF)
        "spy_price": 550.12,
        "spy_ytd": 8.4,
        "spy_low": 480.00,
        "spy_high": 560.00,
        "spy_dividend": 1.4,
        "spy_pe": 20.5,
        "spy_off_high": -1.8,
        "spy_beta": 1.00,
        "spy_tech": "High but diversified",
        "spy_drawdown": 22.0,
        "spy_phase": "Late-cycle, neutral–cautious",
        "spy_suitability": 68,

        # DIA (ETF)
        "dia_price": 405.34,
        "dia_ytd": 6.1,
        "dia_low": 340.00,
        "dia_high": 410.00,
        "dia_dividend": 2.1,
        "dia_pe": 18.2,
        "dia_off_high": -1.2,
        "dia_beta": 0.85,
        "dia_tech": "Moderate, more industrials",
        "dia_drawdown": 15.0,
        "dia_phase": "Late-cycle, relatively defensive",
        "dia_suitability": 78,

        # QQQ (ETF)
        "qqq_price": 480.56,
        "qqq_ytd": 12.7,
        "qqq_low": 390.00,
        "qqq_high": 510.00,
        "qqq_dividend": 0.7,
        "qqq_off_high": -3.5,
        "qqq_off_ath": -4.0,
        "qqq_beta": 1.25,
        "qqq_tech": "Very high, mega-cap tech heavy",
        "qqq_drawdown": 30.0,
        "qqq_phase": "Extended, momentum-driven, vulnerable to air pockets",
        "qqq_suitability": 42,

        # Macro Composite
        "composite_score": 54,

        # Macro Indicators
        "vix_level": 16.5,
        "michigan_csi": 72.0,
        "aaii_bull": 38.0,
        "oil_price": 82.0,
        "credit_spread": 130.0,

        # Risk Thresholds
        "oil_threshold": 95.0,
        "credit_spread_threshold": 160.0,
        "vix_risk_threshold": 22.0,

        # Allocations
        "allocation_dia_range": "20–25%",
        "allocation_spy_range": "40–50%",
        "allocation_qqq_range": "0–10%",
        "allocation_bonds_range": "30–35%",
    }


def compute_delta(current, previous, key, default=0.0):
    cur = current.get(key, default)
    prev = previous.get(key, default)
    try:
        delta = float(cur) - float(prev)
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.2f}"
    except Exception:
        return "n/a"


def compute_all_deltas(current, last_macro, last_retiree, last_technical):
    return {
        "spy_ytd_delta": compute_delta(current, last_macro, "spy_ytd"),
        "dia_ytd_delta": compute_delta(current, last_macro, "dia_ytd"),
        "qqq_ytd_delta": compute_delta(current, last_macro, "qqq_ytd"),

        "spy_off_high_delta": compute_delta(current, last_macro, "spy_off_high"),
        "dia_off_high_delta": compute_delta(current, last_macro, "dia_off_high"),
        "qqq_off_ath_delta": compute_delta(current, last_macro, "qqq_off_ath"),

        "spy_suitability_delta": compute_delta(current, last_retiree, "spy_suitability"),
        "dia_suitability_delta": compute_delta(current, last_retiree, "dia_suitability"),
        "qqq_suitability_delta": compute_delta(current, last_retiree, "qqq_suitability"),

        "composite_delta": compute_delta(current, last_macro, "composite_score"),

        "vix_delta": compute_delta(current, last_macro, "vix_level"),
        "michigan_delta": compute_delta(current, last_macro, "michigan_csi"),
        "aaii_delta": compute_delta(current, last_macro, "aaii_bull"),
    }


# --- COMMENTARY & HTML GENERATORS ---

def build_phase_commentary(current):
    return {
        "spy_phase_commentary": (
            "SPY remains in a late‑cycle, neutral–cautious phase. "
            "Valuations are full, but breadth is acceptable and macro "
            "conditions are not yet outright recessionary."
        ),
        "dia_phase_commentary": (
            "DIA screens as relatively defensive, with more industrials and "
            "value exposure. It remains suitable as a core equity anchor for "
            "a modest‑risk retiree."
        ),
        "qqq_phase_commentary": (
            "QQQ is extended and heavily concentrated in mega‑cap tech. "
            "Momentum is strong, but drawdown risk is elevated and not ideal "
            "for incremental retiree capital at current levels."
        ),
    }


def build_suitability_commentary(current, deltas):
    return {
        "spy_suitability_commentary": (
            f"SPY suitability is {current['spy_suitability']} (Δ {deltas['spy_suitability_delta']}). "
            "Still acceptable for a modest‑risk retiree, but volatility and "
            "valuation argue for measured exposure rather than aggressive adds."
        ),
        "dia_suitability_commentary": (
            f"DIA suitability is {current['dia_suitability']} (Δ {deltas['dia_suitability_delta']}). "
            "Dow exposure remains a strong candidate for core equity weight, "
            "given lower beta and more defensive sector mix."
        ),
        "qqq_suitability_commentary": (
            f"QQQ suitability is {current['qqq_suitability']} (Δ {deltas['qqq_suitability_delta']}). "
            "High concentration and elevated drawdown risk keep this sleeve "
            "small and tactical for a retiree profile."
        ),
    }


def build_composite_commentary(current, deltas):
    score = current["composite_score"]
    delta = deltas["composite_delta"]

    if score < 35:
        category = "Bearish / risk‑off bias"
        text = (
            "Macro composite is in a risk‑off zone. For a retiree, this argues "
            "for higher cash and bond weight, with equity exposure kept at the "
            "lower end of the target ranges."
        )
    elif score < 50:
        category = "Cautious"
        text = (
            "Macro composite is cautious. Conditions are not outright bearish, "
            "but they do not justify aggressive equity adds. Maintain positions, "
            "avoid chasing strength."
        )
    elif score < 65:
        category = "Neutral–cautious"
        text = (
            "Macro composite is neutral–cautious. A retiree can hold existing "
            "equity allocations, but new capital should be deployed patiently "
            "and preferably on pullbacks."
        )
    elif score < 80:
        category = "Moderate bull"
        text = (
            "Macro composite is moderately constructive. For a retiree, this "
            "supports maintaining core equity weights and modestly adding on "
            "weakness, while still respecting volatility."
        )
    else:
        category = "Bullish"
        text = (
            "Macro composite is bullish. For a retiree, this supports full "
            "target equity weights, but risk management and diversification "
            "remain essential."
        )

    return {
        "composite_category": category,
        "composite_commentary": f"Composite score is {score} (Δ {delta}). {text}",
    }


def build_guidance_commentary(current, deltas):
    return {
        "guidance_left_commentary": (
            "Given a neutral–cautious macro backdrop, the guidance for a modest‑risk "
            "retiree is to hold existing positions rather than add aggressively at "
            "current levels. Volatility, valuations, and sentiment do not yet justify "
            "a full risk‑on stance."
        ),
        "guidance_right_commentary": (
            "Key risks to monitor include geopolitical shocks that push oil above the "
            f"{current['oil_threshold']} level, a meaningful widening in credit spreads "
            f"beyond {current['credit_spread_threshold']} bps, and a VIX spike above "
            f"{current['vix_risk_threshold']} that would argue for a shift toward "
            "more defensive positioning."
        ),
    }


def build_allocation_commentary(current):
    return {
        "allocation_dia_commentary": (
            "DIA (Dow exposure) anchors the equity sleeve with lower beta and a "
            "more defensive sector mix. This is well‑aligned with a modest‑risk "
            "retiree profile."
        ),
        "allocation_spy_commentary": (
            "SPY provides broad U.S. equity exposure. It remains a core holding, "
            "but position size should respect valuations and volatility."
        ),
        "allocation_qqq_commentary": (
            "QQQ is a tactical growth sleeve. For a retiree, this allocation "
            "stays small and is best used opportunistically rather than as a "
            "core holding."
        ),
        "allocation_bonds_commentary": (
            "Bonds and cash provide stability, income, and dry powder. This "
            "allocation is critical for preserving principal and managing "
            "sequence‑of‑returns risk."
        ),
    }


def build_macro_indicator_blocks(current, deltas):
    summary_map = {
        "green": "Bullish / supportive",
        "yellow": "Cautious / mixed",
        "red": "Bearish / risk-off",
    }

    indicators = [
        ("Federal Reserve policy stance", "High", "yellow", 55, "Policy is restrictive but not tightening further; cuts are data‑dependent."),
        ("Forward P/E ratio (S&P 500)", "High", "yellow", 60, "Valuations are full, limiting upside for a retiree without pullbacks."),
        ("ICE BofA credit spread (IG OAS)", "High", "green", 40, "Credit spreads are not flashing stress, supporting a hold stance."),
        ("10‑year Treasury yield", "Medium", "yellow", 50, "Yields are elevated but not disorderly; bonds remain viable for income."),
        ("VIX", "Medium", "yellow", 45, f"VIX at {current['vix_level']} (Δ {deltas['vix_delta']}) — not extreme, but worth monitoring."),
        ("M2 money supply", "Medium", "yellow", 50, "Liquidity is not abundant, but not collapsing; neutral for risk assets."),
        ("Price & momentum", "Medium", "yellow", 60, "Price action is constructive but extended in pockets, especially in QQQ."),
        ("Michigan consumer sentiment", "Low", "green", 40, f"Sentiment at {current['michigan_csi']} (Δ {deltas['michigan_delta']}) — improving from lows."),
        ("AAII sentiment survey", "Low", "yellow", 55, f"Bulls at {current['aaii_bull']}% (Δ {deltas['aaii_delta']}) — not euphoric, but elevated."),
        ("Earnings & EPS growth", "Medium", "green", 45, "Earnings are holding up; no broad earnings recession yet."),
        ("Geopolitical / oil", "Medium", "yellow", 55, f"Oil at {current['oil_price']} — below the key {current['oil_threshold']} risk threshold."),
    ]

    blocks = []
    for name, weight, signal, score, comment in indicators:
        color_class = {
            "green": "indicator-bar-fill",
            "yellow": "indicator-bar-fill-yellow",
            "red": "indicator-bar-fill-red",
        }.get(signal, "indicator-bar-fill")

        summary = summary_map.get(signal, "Neutral")

        blocks.append(f"""
        <div class="indicator-item">
            <div class="indicator-header">
                <div class="indicator-name">{name}</div>
                <div class="indicator-meta">Weight: {weight}</div>
            </div>
            <div class="indicator-bar-shell">
                <div class="{color_class}" style="width: {score}%;"></div>
            </div>
            <div class="indicator-footer">
                <span class="indicator-comment">{comment}</span>
                <span class="indicator-meta">{summary}</span>
            </div>
        </div>
        """)

    return "\n".join(blocks)


# --- HTML TEMPLATES & RENDER ---

CSS_STYLES = """
:root {
    --bg: #0b1020;
    --bg-card: #141a2f;
    --bg-card-soft: #181f36;
    --text-main: #f5f7ff;
    --text-muted: #a9b0c7;
    --border-soft: #252b45;
    --accent-blue: #4ea3ff;
    --accent-green: #3cc46b;
    --accent-yellow: #f7c948;
    --accent-red: #ff5c5c;
    --accent-grey: #6b7280;
    --accent-bar-bg: #1f253b;
    --accent-bar-fill: #4ea3ff;
    --font-main: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body {
    margin: 0; padding: 0;
    font-family: var(--font-main);
    background: radial-gradient(circle at top, #1b2340 0, #050814 55%);
    color: var(--text-main);
}
.page { max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }
h1, h2, h3 { margin: 0; font-weight: 600; }
h1 { font-size: 1.6rem; letter-spacing: 0.03em; }
h2 { font-size: 1.2rem; }
h3 { font-size: 1rem; }
p { margin: 4px 0 6px; font-size: 0.9rem; color: var(--text-muted); }
.section {
    margin-bottom: 28px; padding: 18px 20px 20px;
    border-radius: 14px;
    background: linear-gradient(135deg, #141a2f 0, #101628 40%, #141a2f 100%);
    border: 1px solid var(--border-soft);
}
.section-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; }
.section-title { display: flex; flex-direction: column; gap: 4px; }
.section-title span.section-subtitle { font-size: 0.8rem; color: var(--text-muted); }
.section-tag {
    font-size: 0.75rem; padding: 3px 8px; border-radius: 999px;
    border: 1px solid var(--accent-blue); color: var(--accent-blue);
    text-transform: uppercase; letter-spacing: 0.06em;
}
.tag-green { border-color: var(--accent-green); color: var(--accent-green); }
.tag-yellow { border-color: var(--accent-yellow); color: var(--accent-yellow); }
.tag-red { border-color: var(--accent-red); color: var(--accent-red); }
.ticker-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.ticker-card { padding: 12px 12px 14px; border-radius: 12px; background: var(--bg-card-soft); border: 1px solid #222842; }
.ticker-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.ticker-name { font-size: 0.95rem; font-weight: 600; }
.ticker-symbol { font-size: 0.8rem; color: var(--text-muted); }
.ticker-price { font-size: 1.2rem; font-weight: 600; color: var(--accent-blue); }
.ticker-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px 10px; margin-top: 6px; }
.metric-label { font-size: 0.75rem; color: var(--text-muted); }
.metric-value { font-size: 0.85rem; color: var(--text-main); }
.metric-value-green { color: var(--accent-green); }
.metric-value-yellow { color: var(--accent-yellow); }
.metric-value-red { color: var(--accent-red); }
.range-bar-wrapper { margin-top: 8px; }
.range-bar-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px; }
.range-bar { width: 100%; height: 8px; border-radius: 999px; background: var(--accent-bar-bg); overflow: hidden; position: relative; }
.range-bar-fill { height: 100%; border-radius: 999px; background: var(--accent-blue); width: 50%; }
.range-bar-fill-green { background: var(--accent-green); }
.range-bar-fill-yellow { background: var(--accent-yellow); }
.range-bar-fill-red { background: var(--accent-red); }
.range-bar-text { margin-top: 2px; font-size: 0.75rem; color: var(--text-muted); }
.phase-note { margin-top: 6px; font-size: 0.78rem; color: var(--text-muted); }
.table-wrapper { margin-top: 4px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
th, td { padding: 6px 8px; border-bottom: 1px solid #222842; }
th { text-align: left; color: var(--text-muted); font-weight: 500; background: #161c33; }
td { color: var(--text-main); }
.cell-muted { color: var(--text-muted); }
.cell-green { color: var(--accent-green); }
.cell-yellow { color: var(--accent-yellow); }
.cell-red { color: var(--accent-red); }
.score-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.score-card { padding: 12px 12px 14px; border-radius: 12px; background: var(--bg-card-soft); border: 1px solid #222842; }
.score-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.score-value { font-size: 1.1rem; font-weight: 600; }
.score-bar-shell { margin-top: 4px; width: 100%; height: 10px; border-radius: 999px; background: var(--accent-bar-bg); overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 999px; width: 50%; background: var(--accent-green); }
.score-bar-fill-yellow { height: 100%; border-radius: 999px; width: 50%; background: var(--accent-yellow); }
.score-bar-fill-red { height: 100%; border-radius: 999px; width: 50%; background: var(--accent-red); }
.score-note { margin-top: 6px; font-size: 0.78rem; color: var(--text-muted); }
.indicator-list { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }
.indicator-item { padding: 8px 10px; border-radius: 10px; background: #151b32; border: 1px solid #222842; }
.indicator-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
.indicator-name { font-size: 0.85rem; font-weight: 500; }
.indicator-meta { font-size: 0.75rem; color: var(--text-muted); }
.indicator-bar-shell { margin-top: 4px; width: 100%; height: 8px; border-radius: 999px; background: var(--accent-bar-bg); overflow: hidden; }
.indicator-bar-fill { height: 100%; border-radius: 999px; width: 40%; background: var(--accent-green); }
.indicator-bar-fill-yellow { height: 100%; border-radius: 999px; width: 40%; background: var(--accent-yellow); }
.indicator-bar-fill-red { height: 100%; border-radius: 999px; width: 40%; background: var(--accent-red); }
.indicator-footer { margin-top: 4px; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.75rem; }
.indicator-comment { color: var(--text-muted); }
.composite-wrapper { margin-top: 6px; }
.composite-scale-labels { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px; }
.composite-bar-shell { width: 100%; height: 12px; border-radius: 999px; background: var(--accent-bar-bg); position: relative; overflow: hidden; }
.composite-bar-fill { position: absolute; top: 0; left: 0; height: 100%; background: var(--accent-yellow); border-radius: 999px; }
.composite-bar-fill-green { position: absolute; top: 0; left: 0; height: 100%; background: var(--accent-green); border-radius: 999px; }
.composite-bar-fill-yellow { position: absolute; top: 0; left: 0; height: 100%; background: var(--accent-yellow); border-radius: 999px; }
.composite-bar-fill-red { position: absolute; top: 0; left: 0; height: 100%; background: var(--accent-red); border-radius: 999px; }
.composite-marker { position: absolute; top: -2px; width: 4px; height: 16px; border-radius: 999px; background: var(--accent-blue); }
.composite-score-row { margin-top: 6px; display: flex; justify-content: space-between; align-items: baseline; }
.composite-score-value { font-size: 1.1rem; font-weight: 600; }
.composite-score-label { font-size: 0.8rem; color: var(--text-muted); }
.composite-note { margin-top: 4px; font-size: 0.78rem; color: var(--text-muted); }
.guidance-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 6px; }
.guidance-card { padding: 10px 12px 12px; border-radius: 12px; background: var(--bg-card-soft); border: 1px solid #222842; }
.guidance-card h3 { margin-bottom: 6px; }
.guidance-list { margin: 0; padding-left: 16px; font-size: 0.8rem; color: var(--text-muted); }
.guidance-list li { margin-bottom: 4px; }
.risk-red { color: var(--accent-red); }
.risk-yellow { color: var(--accent-yellow); }
.risk-green { color: var(--accent-green); }
.allocation-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 6px; }
.allocation-card { padding: 10px 12px 12px; border-radius: 12px; background: var(--bg-card-soft); border: 1px solid #222842; }
.allocation-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
.allocation-range { font-size: 0.8rem; color: var(--text-muted); }
.allocation-note { margin-top: 4px; font-size: 0.78rem; color: var(--text-muted); }
.allocation-note-green { color: var(--accent-green); }
.allocation-note-yellow { color: var(--accent-yellow); }
.allocation-note-red { color: var(--accent-red); }
@media (max-width: 900px) {
    .ticker-grid, .score-grid, .guidance-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    .allocation-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 600px) {
    .allocation-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
}
"""

HTML_BODY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CoPilot US Markets Trends Dashboard</title>
    <style>${css}</style>
</head>
<body>
<div class="page">
    <section class="section" id="macro-dashboard">
        <div class="section-header">
            <div class="section-title">
                <h1>SPY · DIA · QQQ — Macro Trend Dashboard</h1>
                <span class="section-subtitle">
                    Run date: ${run_date} • Last run: ${last_run_date} ${last_run_time}
                </span>
            </div>
            <span class="section-tag">Macro overview</span>
        </div>

        <div class="ticker-grid">
            <div class="ticker-card" id="spy-card">
                <div class="ticker-header">
                    <div>
                        <div class="ticker-name">SPY — S&P 500</div>
                        <div class="ticker-symbol">SPDR S&P 500 ETF Trust</div>
                    </div>
                    <div class="ticker-price">${spy_price}</div>
                </div>
                <div class="ticker-metrics">
                    <div><div class="metric-label">YTD</div><div class="metric-value metric-value-green">${spy_ytd}% (Δ ${spy_ytd_delta})</div></div>
                    <div><div class="metric-label">Forward P/E</div><div class="metric-value">${spy_pe}</div></div>
                    <div><div class="metric-label">52‑wk low</div><div class="metric-value">${spy_low}</div></div>
                    <div><div class="metric-label">52‑wk high</div><div class="metric-value">${spy_high}</div></div>
                    <div><div class="metric-label">Dividend yield</div><div class="metric-value">${spy_dividend}%</div></div>
                    <div><div class="metric-label">Market phase</div><div class="metric-value metric-value-yellow">${spy_phase}</div></div>
                </div>
                <div class="range-bar-wrapper">
                    <div class="range-bar-label">52‑wk range position</div>
                    <div class="range-bar"><div class="range-bar-fill range-bar-fill-green" style="width: ${spy_range_pos}%;"></div></div>
                    <div class="range-bar-text">${spy_range_pos}% of 52‑wk low–high range</div>
                </div>
                <div class="phase-note">${spy_phase_commentary}</div>
            </div>

            <div class="ticker-card" id="dia-card">
                <div class="ticker-header">
                    <div>
                        <div class="ticker-name">DIA — Dow Jones ETF</div>
                        <div class="ticker-symbol">SPDR Dow Jones Industrial Average ETF Trust</div>
                    </div>
                    <div class="ticker-price">${dia_price}</div>
                </div>
                <div class="ticker-metrics">
                    <div><div class="metric-label">YTD</div><div class="metric-value metric-value-green">${dia_ytd}% (Δ ${dia_ytd_delta})</div></div>
                    <div><div class="metric-label">Forward P/E</div><div class="metric-value">${dia_pe}</div></div>
                    <div><div class="metric-label">52‑wk low</div><div class="metric-value">${dia_low}</div></div>
                    <div><div class="metric-label">52‑wk high</div><div class="metric-value">${dia_high}</div></div>
                    <div><div class="metric-label">Dividend yield</div><div class="metric-value">${dia_dividend}%</div></div>
                    <div><div class="metric-label">Market phase</div><div class="metric-value metric-value-green">${dia_phase}</div></div>
                </div>
                <div class="range-bar-wrapper">
                    <div class="range-bar-label">52‑wk range position</div>
                    <div class="range-bar"><div class="range-bar-fill range-bar-fill-green" style="width: ${dia_range_pos}%;"></div></div>
                    <div class="range-bar-text">${dia_range_pos}% of 52‑wk low–high range</div>
                </div>
                <div class="phase-note">${dia_phase_commentary}</div>
            </div>

            <div class="ticker-card" id="qqq-card">
                <div class="ticker-header">
                    <div>
                        <div class="ticker-name">QQQ — Nasdaq 100</div>
                        <div class="ticker-symbol">Invesco QQQ Trust</div>
                    </div>
                    <div class="ticker-price">${qqq_price}</div>
                </div>
                <div class="ticker-metrics">
                    <div><div class="metric-label">YTD</div><div class="metric-value metric-value-green">${qqq_ytd}% (Δ ${qqq_ytd_delta})</div></div>
                    <div><div class="metric-label">Off ATH</div><div class="metric-value metric-value-red">${qqq_off_ath}% (Δ ${qqq_off_ath_delta})</div></div>
                    <div><div class="metric-label">52‑wk low</div><div class="metric-value">${qqq_low}</div></div>
                    <div><div class="metric-label">52‑wk high</div><div class="metric-value">${qqq_high}</div></div>
                    <div><div class="metric-label">Dividend yield</div><div class="metric-value">${qqq_dividend}%</div></div>
                    <div><div class="metric-label">Market phase</div><div class="metric-value metric-value-red">${qqq_phase}</div></div>
                </div>
                <div class="range-bar-wrapper">
                    <div class="range-bar-label">52‑wk range position</div>
                    <div class="range-bar"><div class="range-bar-fill range-bar-fill-yellow" style="width: ${qqq_range_pos}%;"></div></div>
                    <div class="range-bar-text">${qqq_range_pos}% of 52‑wk low–high range</div>
                </div>
                <div class="phase-note">${qqq_phase_commentary}</div>
            </div>
        </div>
    </section>

    <section class="section" id="retiree-head-to-head">
        <div class="section-header">
            <div class="section-title">
                <h1>Head‑to‑Head — Retiree Lens</h1>
                <span class="section-subtitle">Comparative risk and suitability</span>
            </div>
            <span class="section-tag tag-yellow">Retiree focus</span>
        </div>
        <div class="table-wrapper">
            <table>
                <tr><th>Metric</th><th>SPY</th><th>DIA</th><th>QQQ</th></tr>
                <tr><td>YTD 2026 return</td><td class="cell-green">${spy_ytd}% (Δ ${spy_ytd_delta})</td><td class="cell-green">${dia_ytd}% (Δ ${dia_ytd_delta})</td><td class="cell-green">${qqq_ytd}% (Δ ${qqq_ytd_delta})</td></tr>
                <tr><td>From 52‑wk high</td><td class="cell-yellow">${spy_off_high}% (Δ ${spy_off_high_delta})</td><td class="cell-yellow">${dia_off_high}% (Δ ${dia_off_high_delta})</td><td class="cell-red">${qqq_off_high}%</td></tr>
                <tr><td>Market cycle phase</td><td class="cell-yellow">${spy_phase}</td><td class="cell-green">${dia_phase}</td><td class="cell-red">${qqq_phase}</td></tr>
                <tr><td>Beta / volatility</td><td class="cell-yellow">${spy_beta}</td><td class="cell-green">${dia_beta}</td><td class="cell-red">${qqq_beta}</td></tr>
                <tr><td>Dividend yield</td><td class="cell-yellow">${spy_dividend}%</td><td class="cell-green">${dia_dividend}%</td><td class="cell-red">${qqq_dividend}%</td></tr>
                <tr><td>AI / tech concentration</td><td class="cell-yellow">${spy_tech}</td><td class="cell-green">${dia_tech}</td><td class="cell-red">${qqq_tech}</td></tr>
                <tr><td>Estimated drawdown risk</td><td class="cell-yellow">${spy_drawdown}%</td><td class="cell-green">${dia_drawdown}%</td><td class="cell-red">${qqq_drawdown}%</td></tr>
                <tr><td>Retiree suitability</td><td class="cell-yellow">${spy_suitability} (Δ ${spy_suitability_delta})</td><td class="cell-green">${dia_suitability} (Δ ${dia_suitability_delta})</td><td class="cell-red">${qqq_suitability} (Δ ${qqq_suitability_delta})</td></tr>
            </table>
        </div>
    </section>

    <section class="section" id="retiree-scores">
        <div class="section-header">
            <div class="section-title">
                <h1>Retiree Suitability Scores — Modest Risk Profile</h1>
                <span class="section-subtitle">Score changes since last run</span>
            </div>
            <span class="section-tag tag-green">Suitability</span>
        </div>
        <div class="score-grid">
            <div class="score-card" id="spy-score">
                <div class="score-header"><h2>SPY — S&P 500</h2><div class="score-value">${spy_suitability} / 100</div></div>
                <div class="score-bar-shell"><div class="score-bar-fill-yellow" style="width: ${spy_suitability}%;"></div></div>
                <div class="score-note">${spy_suitability_commentary}</div>
            </div>
            <div class="score-card" id="dia-score">
                <div class="score-header"><h2>DIA — Dow Jones ETF</h2><div class="score-value">${dia_suitability} / 100</div></div>
                <div class="score-bar-shell"><div class="score-bar-fill" style="width: ${dia_suitability}%;"></div></div>
                <div class="score-note">${dia_suitability_commentary}</div>
            </div>
            <div class="score-card" id="qqq-score">
                <div class="score-header"><h2>QQQ — Nasdaq 100</h2><div class="score-value">${qqq_suitability} / 100</div></div>
                <div class="score-bar-shell"><div class="score-bar-fill-red" style="width: ${qqq_suitability}%;"></div></div>
                <div class="score-note">${qqq_suitability_commentary}</div>
            </div>
        </div>
    </section>

    <section class="section" id="macro-indicators">
        <div class="section-header">
            <div class="section-title">
                <h1>11 Macro Indicators — Ranked by Predictive Weight</h1>
                <span class="section-subtitle">Same indicator set each run, with updated scores</span>
            </div>
            <span class="section-tag tag-yellow">Macro signals</span>
        </div>
        <div class="indicator-list">${macro_indicator_blocks}</div>
    </section>

    <section class="section" id="composite-score">
        <div class="section-header">
            <div class="section-title">
                <h1>Weighted Composite Score — ${run_date}</h1>
                <span class="section-subtitle">Composite of 11 macro indicators</span>
            </div>
            <span class="section-tag tag-yellow">${composite_category}</span>
        </div>
        <div class="composite-wrapper">
            <div class="composite-scale-labels">
                <span>Bear (0)</span><span>Caution (25)</span><span>Neutral (50)</span><span>Mod. bull (75)</span><span>Bull (100)</span>
            </div>
            <div class="composite-bar-shell">
                <div class="${composite_bar_class}" style="width: ${composite_score}%;"></div>
                <div class="composite-marker" style="left: ${composite_score}%;"></div>
            </div>
            <div class="composite-score-row">
                <div class="composite-score-value">${composite_score}</div>
                <div class="composite-score-label">${composite_category} (Δ ${composite_delta})</div>
            </div>
            <div class="composite-note">${composite_commentary}</div>
        </div>
    </section>

    <section class="section" id="forward-guidance">
        <div class="section-header">
            <div class="section-title">
                <h1>Retiree Forward Guidance — ${run_date}</h1>
                <span class="section-subtitle">Positioning and risk triggers</span>
            </div>
            <span class="section-tag tag-yellow">Guidance</span>
        </div>
        <div class="guidance-grid">
            <div class="guidance-card">
                <h3>Hold positions — do not add at current levels</h3>
                <p>${guidance_left_commentary}</p>
                <ul class="guidance-list">
                    <li class="risk-yellow">Composite score: ${composite_score} (Δ ${composite_delta})</li>
                    <li class="risk-yellow">VIX: ${vix_level} (Δ ${vix_delta})</li>
                    <li class="risk-yellow">AAII sentiment: ${aaii_bull}% bulls (Δ ${aaii_delta})</li>
                    <li class="risk-green">Michigan CSI: ${michigan_csi} (Δ ${michigan_delta})</li>
                </ul>
            </div>
            <div class="guidance-card">
                <h3>Key risks — watch these triggers</h3>
                <p>${guidance_right_commentary}</p>
                <ul class="guidance-list">
                    <li class="risk-red">Iran escalation / oil above ${oil_threshold} sustained</li>
                    <li class="risk-red">Fed divergence — projected cut removed if inflation re‑accelerates</li>
                    <li class="risk-red">Credit spreads widening past ${credit_spread_threshold} bps</li>
                    <li class="risk-red">Risk trigger: VIX > ${vix_risk_threshold} (current: ${vix_level})</li>
                </ul>
            </div>
        </div>
    </section>

    <section class="section" id="allocation">
        <div class="section-header">
            <div class="section-title">
                <h1>Suggested Equity Allocation for a Retiree</h1>
                <span class="section-subtitle">Dynamic, modest‑risk profile — updates each run</span>
            </div>
            <span class="section-tag tag-green">Allocation</span>
        </div>
        <div class="allocation-grid">
            <div class="allocation-card">
                <div class="allocation-header"><h3>DIA — Dow Jones ETF</h3><span class="allocation-range">${allocation_dia_range}</span></div>
                <div class="allocation-note allocation-note-green">${allocation_dia_commentary}</div>
            </div>
            <div class="allocation-card">
                <div class="allocation-header"><h3>SPY — S&P 500</h3><span class="allocation-range">${allocation_spy_range}</span></div>
                <div class="allocation-note allocation-note-yellow">${allocation_spy_commentary}</div>
            </div>
            <div class="allocation-card">
                <div class="allocation-header"><h3>QQQ — Nasdaq 100</h3><span class="allocation-range">${allocation_qqq_range}</span></div>
                <div class="allocation-note allocation-note-red">${allocation_qqq_commentary}</div>
            </div>
            <div class="allocation-card">
                <div class="allocation-header"><h3>Bonds & Cash</h3><span class="allocation-range">${allocation_bonds_range}</span></div>
                <div class="allocation-note allocation-note-green">${allocation_bonds_commentary}</div>
            </div>
        </div>
    </section>
</div>
</body>
</html>
"""


def render_html(current, deltas, extra, last_macro):
    def range_pos(price, low, high):
        try:
            p, l, h = float(price), float(low), float(high)
            if h <= l:
                return 50.0
            return max(0.0, min(100.0, (p - l) / (h - l) * 100))
        except Exception:
            return 50.0

    current["spy_range_pos"] = f"{range_pos(current['spy_price'], current['spy_low'], current['spy_high']):.1f}"
    current["dia_range_pos"] = f"{range_pos(current['dia_price'], current['dia_low'], current['dia_high']):.1f}"
    current["qqq_range_pos"] = f"{range_pos(current['qqq_price'], current['qqq_low'], current['qqq_high']):.1f}"

    score = current["composite_score"]
    if score < 35:
        composite_bar_class = "composite-bar-fill-red"
    elif score < 65:
        composite_bar_class = "composite-bar-fill-yellow"
    else:
        composite_bar_class = "composite-bar-fill-green"

    context = {
        "css": CSS_STYLES,
        "macro_indicator_blocks": build_macro_indicator_blocks(current, deltas),
        "composite_bar_class": composite_bar_class,
        "last_run_date": last_macro.get("last_run_date", "N/A"),
        "last_run_time": last_macro.get("last_run_time", "N/A"),
    }
    
    # Merge all dicts into context
    context.update(current)
    context.update(deltas)
    context.update(extra)

    # Perform substitution via Template engine
    tpl = Template(HTML_BODY_TEMPLATE)
    return tpl.safe_substitute(context)


# --- MAIN ENTRY POINT ---

def main():
    last_macro = load_json(SNAPSHOT_MACRO)
    last_retiree = load_json(SNAPSHOT_RETIREE)
    last_technical = load_json(SNAPSHOT_TECHNICAL)

    current = get_current_data()
    deltas = compute_all_deltas(current, last_macro, last_retiree, last_technical)

    extra = {}
    extra.update(build_phase_commentary(current))
    extra.update(build_suitability_commentary(current, deltas))
    extra.update(build_composite_commentary(current, deltas))
    extra.update(build_guidance_commentary(current, deltas))
    extra.update(build_allocation_commentary(current))

    html = render_html(current, deltas, extra, last_macro)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    dt_local = datetime.now().astimezone()

    save_json(SNAPSHOT_MACRO, {
        "last_run_date": current["run_date"],
        "last_run_time": dt_local.strftime("%H:%M:%S %Z"),
        "spy_ytd": current["spy_ytd"],
        "dia_ytd": current["dia_ytd"],
        "qqq_ytd": current["qqq_ytd"],
        "qqq_off_ath": current["qqq_off_ath"],
        "spy_off_high": current["spy_off_high"],
        "dia_off_high": current["dia_off_high"],
        "composite_score": current["composite_score"],
        "vix_level": current["vix_level"],
        "michigan_csi": current["michigan_csi"],
        "aaii_bull": current["aaii_bull"],
    })

    save_json(SNAPSHOT_RETIREE, {
        "spy_suitability": current["spy_suitability"],
        "dia_suitability": current["dia_suitability"],
        "qqq_suitability": current["qqq_suitability"],
    })

    save_json(SNAPSHOT_TECHNICAL, {})


if __name__ == "__main__":
    main()
