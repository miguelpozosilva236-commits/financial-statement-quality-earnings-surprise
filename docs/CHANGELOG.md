# Real-data completion — 20 October 2026

- Executed all 14 code cells with real SEC/Yahoo inputs and saved outputs.
- Fixed the announcement scope to 2021–2025 and included historical SEC submission blocks.
- Added frozen source snapshots, retrieval metadata, hashes and a socket-independent execution runner.
- Added quarter-block uncertainty, issuer-clustered exploratory OLS, a held-out baseline comparison and a nonfinancial sensitivity with ranks rebuilt.
- Independently reconciled sampled returns and accession-specific annual fundamentals.
- Published aggregate findings while keeping raw vendor records out of public version control.
- Updated dependency pins to the environment that actually completed the run.

---

# Technical revision — 16 October 2026

Original notebook: August 2026. The 26-cell teaching/research flow is retained.

- Corrected one-session returns: exit is one trading observation after entry, rather than the entry close itself.
- Corrected event profiles to use h+1 prices for h daily returns and keep missing observations unavailable.
- Sorted as-of joins globally by the date merge key and enforced strictly prior filings.
- Handled instant XBRL facts without start dates and combined alternative USD tags.
- Replaced mixed annual/quarterly flows with compatible TTM construction and year-earlier comparisons.
- Removed whole-sample winsorization and within-quarter future-peer rankings.
- Replaced sparse same-announcement-day z-scores with an explicit bounded surprise transformation.
- Replaced sparse same-day quintiles with trailing-history cutoffs.
- Split model samples by unique dates, purged overlapping training labels and fitted imputation on training data only.
- Made empty data/provider failures explicit, removed the placeholder SEC contact, fixed the date boundary and added execution metadata.

These are implementation changes, not evidence of improved investment performance. A complete live-data run remains to be validated.
