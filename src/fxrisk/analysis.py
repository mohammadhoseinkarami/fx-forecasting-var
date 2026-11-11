"""Core calculations for exchange-rate forecasting and return-risk analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

DATE_COLUMN = "date"
CURRENCIES = ["USD", "GBP", "CAD", "AUD", "JPY"]


def load_exchange_rates(path: str | Path) -> pd.DataFrame:
    """Load and validate daily foreign-currency-units-per-EUR exchange rates."""
    data = pd.read_csv(path, parse_dates=[DATE_COLUMN])

    expected = [DATE_COLUMN, *CURRENCIES]
    missing = [column for column in expected if column not in data.columns]
    if missing:
        raise ValueError(f"Input is missing required columns: {', '.join(missing)}")

    data = data[expected].copy().sort_values(DATE_COLUMN).reset_index(drop=True)
    if data[DATE_COLUMN].isna().any():
        raise ValueError("The date column contains missing or invalid values.")
    if data[DATE_COLUMN].duplicated().any():
        raise ValueError("The dataset contains duplicate dates.")
    if data[CURRENCIES].isna().any().any():
        raise ValueError("Exchange-rate columns contain missing values.")
    if (data[CURRENCIES] <= 0).any().any():
        raise ValueError("Exchange rates must be strictly positive.")

    return data.set_index(DATE_COLUMN)


def calculate_returns(rates: pd.DataFrame) -> pd.DataFrame:
    """Calculate simple daily percentage changes, matching the stated return calculation."""
    return rates.pct_change(fill_method=None).dropna(how="all")


def analyze_currency(
    rates: pd.Series,
    confidence_level: float = 0.975,
) -> tuple[dict[str, Any], Any, pd.Series]:
    """Fit an AR(1) model and calculate a two-sided Gaussian return interval.

    Model: r[t] = alpha + beta * r[t-1] + error[t].
    The interval uses the full-sample mean and sample standard deviation.
    """
    if not 0.5 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0.5 and 1.0.")

    rates = rates.dropna().astype(float)
    if len(rates) < 4:
        raise ValueError("At least four rate observations are required.")

    returns = rates.pct_change(fill_method=None).dropna()
    lagged = returns.shift(1).dropna()
    target = returns.loc[lagged.index]
    design = sm.add_constant(lagged.rename("lagged_return"))
    model = sm.OLS(target, design).fit()

    alpha = float(model.params["const"])
    beta = float(model.params["lagged_return"])
    last_return = float(returns.iloc[-1])
    forecast_return = alpha + beta * last_return

    mean_return = float(returns.mean())
    volatility = float(returns.std(ddof=1))
    z_score = float(norm.ppf((1.0 + confidence_level) / 2.0))
    lower_return = mean_return - z_score * volatility
    upper_return = mean_return + z_score * volatility

    outside = (returns < lower_return) | (returns > upper_return)
    exception_count = int(outside.sum())
    observation_count = int(len(returns))
    latest_date = rates.index[-1]
    spot_rate = float(rates.iloc[-1])

    metrics: dict[str, Any] = {
        "currency": rates.name,
        "quote_convention": f"{rates.name} per EUR",
        "observations": observation_count,
        "regression_observations": int(model.nobs),
        "first_observation_date": rates.index[0].date().isoformat(),
        "last_observation_date": latest_date.date().isoformat(),
        "next_weekday_forecast_date": (latest_date + pd.offsets.BDay(1)).date().isoformat(),
        "spot_rate": spot_rate,
        "mean_daily_return": mean_return,
        "daily_volatility": volatility,
        "ar1_intercept": alpha,
        "ar1_lag_coefficient": beta,
        "ar1_lag_p_value": float(model.pvalues["lagged_return"]),
        "ar1_r_squared": float(model.rsquared),
        "last_daily_return": last_return,
        "forecast_daily_return": forecast_return,
        "forecast_spot_rate": spot_rate * (1.0 + forecast_return),
        "confidence_level_two_sided": confidence_level,
        "z_score": z_score,
        "lower_return_bound": lower_return,
        "upper_return_bound": upper_return,
        "expected_exceptions_under_normality": observation_count * (1.0 - confidence_level),
        "observed_exceptions": exception_count,
        "observed_exception_rate": exception_count / observation_count,
        "lower_spot_bound": spot_rate * (1.0 + lower_return),
        "upper_spot_bound": spot_rate * (1.0 + upper_return),
    }
    return metrics, model, returns


def analyze_all(
    rates: pd.DataFrame,
    confidence_level: float = 0.975,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, pd.Series]]:
    """Run the analysis for each currency and return summary/model/return data."""
    rows: list[dict[str, Any]] = []
    models: dict[str, Any] = {}
    returns_by_currency: dict[str, pd.Series] = {}

    for currency in CURRENCIES:
        metrics, model, returns = analyze_currency(rates[currency].rename(currency), confidence_level)
        rows.append(metrics)
        models[currency] = model
        returns_by_currency[currency] = returns

    return pd.DataFrame(rows), models, returns_by_currency


def save_exchange_rate_chart(rates: pd.DataFrame, output_path: str | Path) -> None:
    """Save normalized exchange-rate history for cross-currency comparison."""
    normalized = rates.divide(rates.iloc[0]).multiply(100.0)
    fig, ax = plt.subplots(figsize=(12, 6))
    for currency in CURRENCIES:
        ax.plot(normalized.index, normalized[currency], label=currency, linewidth=1.2)
    ax.set_title("EUR exchange rates: normalized history")
    ax.set_xlabel("Date")
    ax.set_ylabel("Index (2 Jan 2006 = 100)")
    ax.grid(True, alpha=0.25)
    ax.legend(title="Foreign currency per EUR", ncol=5, frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_return_distribution_chart(
    returns: dict[str, pd.Series],
    summary: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Save return histograms with their fitted Gaussian central intervals."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    axes = axes.ravel()
    for index, currency in enumerate(CURRENCIES):
        series = returns[currency]
        row = summary.loc[summary["currency"] == currency].iloc[0]
        ax = axes[index]
        ax.hist(series * 100.0, bins=60, density=True, alpha=0.65, label="Observed returns")
        x = np.linspace(float(series.min()), float(series.max()), 400)
        density = norm.pdf(x, row["mean_daily_return"], row["daily_volatility"])
        ax.plot(x * 100.0, density / 100.0, linewidth=1.7, label="Normal fit")
        ax.axvline(row["lower_return_bound"] * 100.0, linestyle="--", linewidth=1.2)
        ax.axvline(row["upper_return_bound"] * 100.0, linestyle="--", linewidth=1.2)
        ax.set_title(currency)
        ax.set_xlabel("Daily simple return (%)")
        ax.set_ylabel("Density")
        ax.grid(True, alpha=0.2)
    axes[-1].axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Daily FX returns and 97.5% two-sided Gaussian intervals", y=0.995)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_exception_chart(summary: pd.DataFrame, output_path: str | Path) -> None:
    """Compare observed in-sample exception rates with the nominal tail rate."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ordered = summary.sort_values("observed_exception_rate", ascending=False)
    ax.bar(ordered["currency"], ordered["observed_exception_rate"] * 100.0, label="Observed")
    nominal = (1.0 - float(ordered["confidence_level_two_sided"].iloc[0])) * 100.0
    ax.axhline(nominal, linestyle="--", linewidth=1.8, label=f"Nominal outside rate ({nominal:.1f}%)")
    ax.set_title("Observed exceptions vs. Gaussian interval expectation")
    ax.set_xlabel("Currency")
    ax.set_ylabel("Returns outside interval (%)")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_markdown_report(summary: pd.DataFrame, output_path: str | Path) -> None:
    """Write a compact, reproducible narrative summary of the model output."""
    first = summary.iloc[0]
    p_values = summary["ar1_lag_p_value"]
    all_insignificant = bool((p_values >= 0.05).all())
    max_exception = summary.loc[summary["observed_exception_rate"].idxmax()]
    min_exception = summary.loc[summary["observed_exception_rate"].idxmin()]

    lines = [
        "# Analysis summary",
        "",
        f"The dataset contains {int(first['observations'] + 1):,} daily rate observations per currency, "
        f"from {summary['first_observation_date'].min()} to {summary['last_observation_date'].max()}.",
        "",
        "## Main findings",
        "",
    ]
    if all_insignificant:
        lines.append(
            "- The AR(1) lag coefficient is not statistically significant at the 5% level for any of the five currencies. "
            "In this in-sample specification, yesterday's return does not provide statistically reliable linear "
            "predictive information about today's return. This is not, by itself, proof of market efficiency."
        )
    lines.extend([
        f"- The observed in-sample exception rate ranges from {min_exception['observed_exception_rate']:.2%} "
        f"({min_exception['currency']}) to {max_exception['observed_exception_rate']:.2%} ({max_exception['currency']}).",
        "- The nominal fraction outside a 97.5% two-sided interval is 2.5%. All five observed exception rates are higher, "
        "suggesting that a constant-volatility Gaussian interval understates tail observations in this sample.",
        "",
        "## Interpretation limits",
        "",
        "- The 97.5% interval is two-sided: 1.25% is allocated to each tail. It is not the conventional one-tailed 97.5% VaR measure.",
        "- Mean and standard deviation are estimated over the same full sample used to count exceptions. These are in-sample diagnostics, "
        "not a genuine out-of-sample VaR backtest.",
        "- The AR(1) model is estimated and evaluated in-sample. A walk-forward forecast evaluation would be needed to assess real predictive performance.",
        "- The volatility estimate is the full-sample standard deviation; no GARCH or other time-varying volatility model is fitted.",
        "- The next forecast date is the next weekday after the final observation, not an exchange-calendar-adjusted trading date.",
        "",
        "## Currency-level statistics",
        "",
        "| Currency | AR(1) beta | Beta p-value | Daily volatility | Forecast return | Exceptions | Observed exception rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['currency']} | {row['ar1_lag_coefficient']:.6f} | {row['ar1_lag_p_value']:.4f} | "
            f"{row['daily_volatility']:.4%} | {row['forecast_daily_return']:.4%} | "
            f"{int(row['observed_exceptions'])} | {row['observed_exception_rate']:.2%} |"
        )
    lines.append("")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
