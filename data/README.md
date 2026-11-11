# Dataset and source

`exchange_rates.csv` contains 5,288 daily observations for 1 EUR quoted in USD, GBP, CAD, AUD and JPY, from 2 January 2006 to 31 August 2026. The dataset is the fixed historical input used in this analysis.

## Source attribution

**Source: Suomen Pankki (Bank of Finland), Exchange Rates.**

- [Suomen Pankki – Exchange Rates](https://www.suomenpankki.fi/en/statistics/interest-rates-and-exchange-rates/exchange-rates/)
- [Suomen Pankki – Historical exchange-rate report](https://reports.suomenpankki.fi/WebForms/ReportViewerPage.aspx?output=&report=%2Ftilastot%2Fvaluuttakurssit%2Fvaluuttakurssit_short_en)

The Bank of Finland states that the exchange rates shown on its website are euro reference rates published by the European Central Bank (ECB). Accordingly, this project credits **Suomen Pankki as the cited data source/access point** and identifies the ECB as the publisher of the underlying euro reference rates.

## Data description

- **Base currency:** EUR
- **Quote currencies:** USD, GBP, CAD, AUD and JPY
- **Quote convention:** units of foreign currency per 1 EUR
- **Frequency:** daily reference rates on publication days
- **Period:** 2 January 2006 to 31 August 2026
- **File:** [`exchange_rates.csv`](exchange_rates.csv)

The CSV is a fixed input snapshot. The analysis script does not download or refresh observations automatically. Check the source pages for the latest available data before extending the sample.
