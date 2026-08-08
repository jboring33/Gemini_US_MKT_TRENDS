def get_macro_indicators() -> list[dict]:
    """Returns static macro status cards matching the original dashboard."""
    return [
        {
            "title": "1. FED BALANCE SHEET",
            "status": "QT Ongoing",
            "detail": "Continued balance sheet runoff strains systemic liquidity over time.",
            "color": "red"
        },
        {
            "title": "2. UNEMPLOYMENT RATE",
            "status": "Stable (~4.1%)",
            "detail": "Labor market shows gradual cooling without signaling immediate recession.",
            "color": "yellow"
        },
        {
            "title": "3. CPI & PCE INFLATION",
            "status": "Moderating",
            "detail": "Trending downward toward target, though sticky services remain.",
            "color": "yellow"
        },
        {
            "title": "4. YIELD CURVE (10Y-2Y)",
            "status": "Un-inverting",
            "detail": "Transitioning out of inversion; historically warrants late-cycle caution.",
            "color": "yellow"
        },
        {
            "title": "5. FED FUNDS RATE",
            "status": "Restrictive Horizon",
            "detail": "Rates remain elevated above neutral level to curb lingering inflation.",
            "color": "red"
        },
        {
            "title": "6. CONSUMER SENTIMENT",
            "status": "Rangebound",
            "detail": "Balanced between steady labor markets and higher cost of living.",
            "color": "yellow"
        },
        {
            "title": "7. US DOLLAR (DXY)",
            "status": "Stable Range",
            "detail": "Neutral impact on multinational corporate earnings performance.",
            "color": "yellow"
        },
        {
            "title": "8. HIGH YIELD SPREADS",
            "status": "Tight (Low Stress)",
            "detail": "Credit markets signal minimal immediate default risk or liquidity distress.",
            "color": "green"
        },
        {
            "title": "9. REAL GDP GROWTH",
            "status": "Positive Expansion",
            "detail": "Economic activity continues to support underlying corporate earnings.",
            "color": "green"
        }
    ]
