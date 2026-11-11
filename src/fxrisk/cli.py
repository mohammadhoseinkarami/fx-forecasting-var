"""Command-line interface for the FX forecasting and VaR project."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .analysis import (
    analyze_all,
    load_exchange_rates,
    save_exchange_rate_chart,
    save_exception_chart,
    save_return_distribution_chart,
    write_markdown_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AR(1) exchange-rate forecasts and Gaussian return-risk analysis."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/exchange_rates.csv"),
        help="Input CSV (default: data/exchange_rates.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Project directory where results/, figures/ and reports/ will be written.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.975,
        help="Two-sided central confidence level (default: 0.975).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = args.output_dir
    results_dir = output_dir / "results"
    figures_dir = output_dir / "figures"
    reports_dir = output_dir / "reports"
    for directory in (results_dir, figures_dir, reports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rates = load_exchange_rates(args.input)
    summary, models, returns = analyze_all(rates, args.confidence)
    summary.to_csv(results_dir / "currency_summary.csv", index=False, float_format="%.10g")

    regression_rows = []
    for currency, model in models.items():
        regression_rows.append({
            "currency": currency,
            "intercept": model.params["const"],
            "lag_coefficient": model.params["lagged_return"],
            "intercept_p_value": model.pvalues["const"],
            "lag_coefficient_p_value": model.pvalues["lagged_return"],
            "r_squared": model.rsquared,
            "standard_error": model.mse_resid ** 0.5,
            "observations": int(model.nobs),
        })
    pd.DataFrame(regression_rows).to_csv(
        results_dir / "ar1_regression_results.csv", index=False, float_format="%.10g"
    )

    save_exchange_rate_chart(rates, figures_dir / "normalized_exchange_rates.png")
    save_return_distribution_chart(returns, summary, figures_dir / "return_distributions.png")
    save_exception_chart(summary, figures_dir / "exception_rates.png")
    write_markdown_report(summary, reports_dir / "analysis_summary.md")

    display_columns = [
        "currency", "ar1_lag_coefficient", "ar1_lag_p_value",
        "forecast_daily_return", "observed_exception_rate",
    ]
    print(summary[display_columns].to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print(f"\nOutputs saved under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
