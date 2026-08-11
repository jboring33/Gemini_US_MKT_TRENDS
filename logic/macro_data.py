def get_macro_risk_indicators():
  """Returns the full list of 8 macro, market regime, and corporate risk indicators."""
  return [
      {
          "title": "Corporate Earnings Growth & Guidance",
          "status": "Expansionary / Positive EPS Beats",
          "color": "green",
          "detail": (
              "S&P 500 (SPY) and Nasdaq (QQQ) aggregate earnings growth remains"
              " solid with stable forward guidance. Corporate margins across"
              " major holdings continue to support market valuations."
          ),
      },
      {
          "title": "Federal Reserve Policy Trajectory",
          "status": "Neutral / Restrictive Baseline",
          "color": "yellow",
          "detail": (
              "Policy rates remain elevated to ensure target inflation control,"
              " though liquidity buffers and rate-cut optionality cushion downside"
              " risks."
          ),
      },
      {
          "title": "Inflation Trend (CPI / PCE)",
          "status": "Moderating / Disinflation Trend",
          "color": "green",
          "detail": (
              "Core and headline inflation figures continue a gradual downward"
              " drift toward targets, reducing margin pressure for industrial"
              " (DIA) and consumer sectors."
          ),
      },
      {
          "title": "Yield Curve & Debt Markets (10Y - 2Y)",
          "status": "Un-Inverting / Normalization Phase",
          "color": "yellow",
          "detail": (
              "Treasury yields are stabilizing as short-end rates ease,"
              " signaling a transition from curve inversion toward economic"
              " normalization."
          ),
      },
      {
          "title": "Labor Market & Employment Stability",
          "status": "Resilient Expansion",
          "color": "green",
          "detail": (
              "Job growth and unemployment metrics stay within sustainable"
              " historical ranges, supporting consumer spending across broader"
              " benchmark equities."
          ),
      },
      {
          "title": "Financial Conditions & Market Liquidity",
          "status": "Accommodative / Low Stress",
          "color": "green",
          "detail": (
              "Credit spreads remain tight and access to capital is fluid,"
              " preventing systemic credit freeze risks across large-cap"
              " indexes."
          ),
      },
      {
          "title": "Geopolitical & Supply Chain Risk",
          "status": "Elevated / Watch",
          "color": "yellow",
          "detail": (
              "Ongoing international friction and commodity volatility present"
              " sporadic headline risk, though global supply chains remain"
              " largely functional."
          ),
      },
      {
          "title": "Volatility Regime (VIX Baseline)",
          "status": "Low-to-Moderate Volatility Environment",
          "color": "green",
          "detail": (
              "Volatility metrics reflect orderly market participation,"
              " keeping hedging costs stable and preventing panicky institutional"
              " liquidations."
          ),
      },
  ]
