def get_macro_risk_indicators() -> list[dict]:
  """Macro economic and credit regime parameters."""
  return [
      {
          "title": "Yield Curve (10Y - 2Y)",
          "status": "Late-Cycle Un-Inversion",
          "detail": (
              "Curve un-inversion signals transitioning macro regime."
              " Maintain conservative equity discipline."
          ),
          "color": "yellow",
      },
      {
          "title": "High Yield Credit Spreads",
          "status": "Tight Spreads (Low Stress)",
          "detail": (
              "Bond market pricing minimal systemic credit risk. Confirms equity"
              " hold bias."
          ),
          "color": "green",
      },
      {
          "title": "Real Yields (10Y TIPS)",
          "status": "Elevated Real Cost of Capital",
          "detail": (
              "Restrictive real rates place valuation limits on mega-cap growth"
              " multiples (QQQ factor)."
          ),
          "color": "yellow",
      },
      {
          "title": "Fed Balance Sheet (QT)",
          "status": "Quantitative Tightening Active",
          "detail": (
              "System liquidity drain favors cash-flow-rich dividend/value"
              " assets over high-beta."
          ),
          "color": "red",
      },
      {
          "title": "Labor & Unemployment",
          "status": "Orderly Cooling (~4.1%)",
          "detail": (
              "Gradual cooling avoids immediate recessionary shock while"
              " providing rate cut flexibility."
          ),
          "color": "green",
      },
      {
          "title": "Core PCE Inflation",
          "status": "Moderating Trajectory",
          "detail": (
              "Disinflation supports Federal Reserve policy easing, dampening"
              " market tail risks."
          ),
          "color": "yellow",
      },
  ]
