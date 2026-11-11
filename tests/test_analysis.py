import numpy as np
import pandas as pd
import pytest

from fxrisk.analysis import analyze_currency, calculate_returns, load_exchange_rates


def test_calculate_returns_uses_simple_percentage_changes():
    rates = pd.DataFrame({"USD": [1.0, 1.1, 1.21]})
    returns = calculate_returns(rates)
    assert np.allclose(returns["USD"].to_numpy(), [0.10, 0.10])


def test_ar1_forecast_and_interval_are_well_formed():
    index = pd.bdate_range("2024-01-01", periods=200)
    rng = np.random.default_rng(7)
    daily_returns = rng.normal(0.0002, 0.005, len(index) - 1)
    rates = pd.Series(
        np.r_[100.0, 100.0 * np.cumprod(1.0 + daily_returns)],
        index=index,
        name="USD",
    )
    metrics, model, returns = analyze_currency(rates, confidence_level=0.975)
    assert metrics["regression_observations"] == len(returns) - 1
    assert metrics["lower_return_bound"] < metrics["upper_return_bound"]
    assert metrics["lower_spot_bound"] < metrics["spot_rate"] < metrics["upper_spot_bound"]
    assert np.isfinite(metrics["forecast_daily_return"])
    assert model.nobs == len(returns) - 1


def test_invalid_confidence_level_is_rejected():
    index = pd.bdate_range("2024-01-01", periods=10)
    rates = pd.Series(np.linspace(1.0, 1.1, len(index)), index=index, name="USD")
    with pytest.raises(ValueError):
        analyze_currency(rates, confidence_level=1.0)


def test_input_loader_rejects_duplicate_dates(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "date,USD,GBP,CAD,AUD,JPY\n"
        "2024-01-01,1,1,1,1,1\n"
        "2024-01-01,1,1,1,1,1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate dates"):
        load_exchange_rates(csv)


def test_included_dataset_has_expected_scope():
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    rates = load_exchange_rates(project_root / "data" / "exchange_rates.csv")
    assert rates.shape == (5288, 5)
    assert rates.index.min() == pd.Timestamp("2006-01-02")
    assert rates.index.max() == pd.Timestamp("2026-08-31")
