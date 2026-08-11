def get_macro_risk_indicators() -> list:
  """Returns macro, fundamental valuation, and economic regime indicators
  """
  return [
      {
          "title": "S&P 500 Valuation (Shiller CAPE Ratio)",
          "status": "ELEVATED VALUATION",
          "color": "yellow",  # Options: 'green' (<25), 'yellow' (25-35), 'red' (>35)
          "detail": (
              "The Cyclically Adjusted Price-to-Earnings (CAPE) ratio measures"
              " long-term valuation using 10-year inflation-adjusted earnings."
              " While CAPE is a poor short-term timing tool, levels above 30"
              " historically signal lower expected 10-year annualized returns"
              " and higher vulnerability to macro drawdowns."
          ),
      },
      {
          "title": "Yield Curve Dynamics (10Y - 2Y Spread)",
          "status": "UNINVERTING / NORMALIZING",
          "color": "yellow",
          "detail": (
              "Monitors recession risks and credit availability. A historic"
              " inversion followed by un-inversion often marks the late stage"
              " of an economic cycle. Watch for steepening driven by short rate"
              " cuts versus long-term bond yield movements."
          ),
      },
      {
          "title": "Fed Monetary Policy & Liquidity",
          "status": "NEUTRAL / DATA-DEPENDENT",
          "color": "green",
          "detail": (
              "Evaluates interest rate trajectories and central bank balance"
              " sheet changes (QT/QE). A stable or accommodative rate posture"
              " provides liquidity support for risk assets like broad equity"
              " index ETFs."
          ),
      },
      {
          "title": "Labor Market & Core Inflation (PCE / CPI)",
          "status": "MODERATING TREND",
          "color": "green",
          "detail": (
              "Core inflation trends toward target levels alongside stable"
              " employment data support a 'soft landing' narrative, favoring"
              " corporate margin preservation and multi-quarter equity market"
              " stability."
          ),
      },
      {
          "title": "Credit Spreads (High Yield vs. Treasury)",
          "status": "TIGHT SPREADS (Low Stress)",
          "color": "green",
          "detail": (
              "Tight high-yield credit spreads indicate strong institutional"
              " risk appetite and low corporate default anxiety. Widening"
              " spreads serve as an early warning signal before broader equity"
              " pullbacks."
          ),
      },
      {
          "title": "USD / Commodity Price Environment",
          "status": "BALANCED REGIME",
          "color": "green",
          "detail": (
              "A stable US Dollar index (DXY) and moderate energy/commodity"
              " prices reduce input-cost pressures for S&P 500 and Dow Jones"
              " industrial components."
          ),
      },
  ]

def get_macro_risk_indicators():
  return [
      {
          "title": "Corporate Earnings Growth & Guidance",
          "status": "Positive / Expansionary",
          "color": "green",
          "detail": (
              "S&P 500 (SPY) and Nasdaq (QQQ) aggregate EPS growth remains"
              " solid with stable forward guidance. Corporate margins across"
              " major index holdings continue to support elevated market"
              " valuations."
          ),
      },
      {
          "title": "Federal Reserve Rate Trajectory",
          "status": "Neutral / Data Dependent",
          "color": "yellow",
          "detail": (
              "The Fed is balancing inflation control with economic growth."
              " Rate policy remains restricted, but easing expectations"
              " provide liquidity support for broad equities."
          ),
      },
      {
          "title": "Inflation & Consumer Health (CPI / PCE)",
          "status": "Moderating Trend",
          "color": "green",
          "detail": (
              "Headline and core inflation measures show gradual cooling towards"
              " target levels, easing margin pressure on Dow (DIA) industrial"
              " and consumer components."
          ),
      },
  ]
