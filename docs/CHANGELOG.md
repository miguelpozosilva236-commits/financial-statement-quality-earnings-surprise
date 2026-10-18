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
