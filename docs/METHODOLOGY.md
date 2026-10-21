# Methodology

## Accounting information set

USD facts retain period starts, period ends and filing dates. Alternative accounting tags are combined rather than selecting a single tag for an issuer's whole history. Instant balance-sheet facts do not need a start date. A fact is eligible only when its filing date is on or before the feature observation's filing date.

Flow measures use a direct annual observation or `latest FY + current fiscal YTD − comparable prior fiscal YTD`. This avoids mixing annual and quarterly cash-flow amounts. Missing compatible periods remain missing. The implementation allows small calendar differences and is not a universal fiscal-calendar normalization engine.

Features include cash conversion, accrual intensity, ROAA, gross-margin change, revenue growth and leverage. Cash conversion is undefined for nonpositive net income. ROAA and accruals use the mean of current and year-earlier assets. At each filing date, the reference cross-section contains the latest known filing per issuer. Scores use available weighted ranks with minimum peer and coverage requirements. No full-sample winsorization is applied.

## Event timing and composite

Announcement dates are expressed in New York calendar dates. Financial features must come from a filing strictly before the announcement date. This is conservative when a filing and earnings release occur on the same day, because precise intraday filing availability is not reconstructed.

EPS surprise equals `100 × (reported EPS − estimated EPS) / abs(estimated EPS)`. Zero/missing estimates do not receive a numeric surprise. The composite equals `0.5 × quality score + 0.5 × tanh(surprise percentage / 20)`. The weights and scale are declared modeling choices, not optimized parameters or proven economic relationships.

## Returns and buckets

Entry is the first benchmark trading close strictly after the announcement date. A horizon of h sessions requires h+1 prices. The forward benchmark-adjusted buy-and-hold return is the stock return minus the benchmark return over identical entry/exit dates. Missing prices remain missing.

Event profiles use additive cumulative daily abnormal returns from entry close. This CAR differs from the difference of compounded holding-period returns and is labeled separately.

Five signal buckets use cutoffs estimated from the previous 365 days of events, excluding the current date. At least 20 prior events and distinct thresholds are required. They are historical-reference buckets, not a simultaneous cross-sectional long-short portfolio. Threshold selection, sample size and sector effects need further sensitivity work before stronger claims.

## Model evaluation

The latest 25% of unique entry dates form the holdout. Training observations whose 21-session labels mature on or after the first test entry are purged. Missing-feature imputation is learned from training data only. Random Forest holdout RMSE is compared with a training-mean baseline. OLS uses issuer-clustered errors for exploratory inference. Fifteen clusters, overlapping labels and repeated issuers still limit formal inference. Quarter-block bootstrap intervals resample calendar-quarter blocks with 2,000 fixed-seed draws.

## Data coverage and limitations

The fixed 15-stock universe is a convenience sample, not a historical investable universe. Returned historical submission files whose date windows intersect 2019–2025 are included; no recent-filings cap truncates this window. Accounting tags differ by issuer, financial/non-financial ratios are not fully comparable, earnings estimates may be revised and adjusted prices may be back-adjusted. Filing-date controls alone cannot eliminate every revision or survivorship issue.

Optional macro context was removed from the executed scope because it does not enter the research question or predictive model. Gross event returns omit costs, turnover, execution constraints and portfolio construction. Test fixtures establish selected calculation behavior only; they do not validate market results.


## Executed scope and uncertainty

Announcements are fixed to 2021–2025 before results are evaluated. The 2019–2025 filing history provides
accounting warm-up observations; prices extend from 2020 through 2026-02-13 to mature the final 21-session outcomes.
Quarter-block bootstrap intervals preserve within-quarter dependence but use at most twenty quarters and
do not eliminate issuer dependence. They are descriptive uncertainty checks, not confirmatory evidence.

The prespecified nonfinancial sensitivity removes JPM before rebuilding accounting ranks, composite
scores and trailing signal thresholds. It retains the original weights. Historical provider EPS estimates
and reported EPS may be revised or use adjusted reporting conventions; exact pre-announcement vintages
and uniform GAAP/non-GAAP comparability are not certified. Stock adjusted-price returns and the S&P 500
price-index benchmark differ in dividend treatment. No stronger point-in-time or tradable-alpha claim is made.


## Historical company identity

For XOM, the 2021–2025 study uses predecessor registrant CIK 0000034088. The current SEC ticker map
points to successor CIK 0002115436 following the July 1, 2026 reorganization. Using only the current
map would silently remove XOM's historical sample. The override is specific to this fixed pre-merger window,
and source-cache names include CIKs to avoid mixing entities.

Source: [ExxonMobil successor-registration filing, July 1, 2026](https://www.sec.gov/Archives/edgar/data/2115436/000119312526291990/d71068d8k12b.htm).


## Parent net income derivation

When direct parent net income is unavailable, the accounting identity consolidated profit
(`ProfitLoss`) less income attributable to noncontrolling interests
(`NetIncomeLossAttributableToNoncontrollingInterest`) is used, with the same reporting and TTM
periods and filing cutoff. Both components must exist; missing noncontrolling income is never
assumed to be zero. This recovers CAT's parent-income history. The latest CAT annual observation
is independently reconciled to its exact accession in `cat_accounting_check.json`.
