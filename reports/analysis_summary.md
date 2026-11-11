# Analysis summary

The dataset contains 5,288 daily rate observations per currency, from 2006-01-02 to 2026-08-31.

## Main findings

- The AR(1) lag coefficient is not statistically significant at the 5% level for any of the five currencies. In this in-sample specification, yesterday's return does not provide statistically reliable linear predictive information about today's return. This is not, by itself, proof of market efficiency.
- The observed in-sample exception rate ranges from 3.44% (AUD) to 3.78% (CAD).
- The nominal fraction outside a 97.5% two-sided interval is 2.5%. All five observed exception rates are higher, suggesting that a constant-volatility Gaussian interval understates tail observations in this sample.

## Interpretation limits

- The 97.5% interval is two-sided: 1.25% is allocated to each tail. It is not the conventional one-tailed 97.5% VaR measure.
- Mean and standard deviation are estimated over the same full sample used to count exceptions. These are in-sample diagnostics, not a genuine out-of-sample VaR backtest.
- The AR(1) model is estimated and evaluated in-sample. A walk-forward forecast evaluation would be needed to assess real predictive performance.
- The volatility estimate is the full-sample standard deviation; no GARCH or other time-varying volatility model is fitted.
- The next forecast date is the next weekday after the final observation, not an exchange-calendar-adjusted trading date.

## Currency-level statistics

| Currency | AR(1) beta | Beta p-value | Daily volatility | Forecast return | Exceptions | Observed exception rate |
|---|---:|---:|---:|---:|---:|---:|
| USD | -0.006476 | 0.6378 | 0.5534% | 0.0037% | 189 | 3.57% |
| GBP | 0.021116 | 0.1248 | 0.4840% | 0.0034% | 184 | 3.48% |
| CAD | 0.014395 | 0.2953 | 0.5465% | 0.0018% | 200 | 3.78% |
| AUD | -0.006968 | 0.6125 | 0.6256% | 0.0017% | 182 | 3.44% |
| JPY | -0.017795 | 0.1958 | 0.6905% | 0.0146% | 199 | 3.76% |
