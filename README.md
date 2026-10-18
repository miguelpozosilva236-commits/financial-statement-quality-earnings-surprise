# Financial Statement Quality & Earnings Surprise Model

**Vicente Pozo · Academic investment research · Python**

An academic research prototype examining the relationship between accounting quality, earnings surprises and subsequent benchmark-adjusted stock returns. The project combines SEC EDGAR/XBRL disclosures with Yahoo Finance earnings and adjusted-price data.

## Start here

- [Research notebook](notebooks/Financial_Statement_Quality_Earnings_Surprise_Model.ipynb): 26 cells covering data access, accounting features, event alignment, return calculations, signal buckets and model evaluation.
- [Methodology](docs/METHODOLOGY.md): information timing, definitions, assumptions and limitations.
- [Revision notes](docs/CHANGELOG.md): repairs to the original August 2026 notebook.
- [Validation](docs/VALIDATION.md): checks performed and the remaining live-data execution requirement.
- [Testable helpers](src/research_core.py) and [boundary tests](tests/test_research_core.py).

## Research design

1. Build accounting features from disclosures available by their filing date.
2. Use comparable trailing-twelve-month flows and year-earlier assets for accounting ratios.
3. Match an earnings event to a filing strictly before that announcement date.
4. Combine an accounting-quality score with an explicitly scaled EPS-surprise signal.
5. Measure 1-, 5- and 21-session forward returns from the next trading close, relative to the S&P 500.
6. Compare trailing-history signal buckets and evaluate OLS/Random Forest models using a purged chronological holdout.

## Execution status

The notebook format and Python syntax pass validation. Ten deterministic calculation and timing tests pass. **A complete live-data run has not been validated**, and no empirical investment-performance result is claimed. SEC access requires a configured identifying User-Agent; Yahoo returned HTTP 429 during the access check. Test fixtures are calculation checks, not market research evidence.

## Run locally

Use Python 3.12 in a dedicated environment, then run from the project directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

For a live run, set `SEC_USER_AGENT` to your own project name and chosen contact address, as required by SEC automated-access policy. Keep that setting outside version control. The contact address is sent to SEC when requests are made. Do not use a placeholder address.

```bash
export SEC_USER_AGENT='Your project name your-contact-address'
python -m jupyter nbconvert --execute --to notebook \
  --output Financial_Statement_Quality_Earnings_Surprise_Model.executed.ipynb \
  notebooks/Financial_Statement_Quality_Earnings_Surprise_Model.ipynb
```

The notebook is self-contained and can also be uploaded to Colab after installing the listed dependencies. Configure `SEC_USER_AGENT` in that session before execution. Local paths are relative to the notebook/project directory.

## Data and outputs

The configured universe is a fixed, small sample of 15 US equities, from 2018-01-01 to 2026-10-16 (exclusive end date). Actual coverage depends on the providers' returned history. Raw provider data and caches are excluded from version control. A successful run writes filing features, earnings events, the matched event panel, issuer summaries, a research scorecard and execution metadata to `outputs/`.

## Interpretation

This is an association study and a coding/modeling portfolio project. It does not establish tradable alpha. Material limitations include universe selection, survivorship, sparse events, sector comparability, filing-date granularity, provider revisions, overlapping returns, dependent observations and execution costs. Read the methodology before interpreting any future result.

Developed by Vicente Pozo with AI assistance for coding, documentation and technical review. Documentation separates implemented methods from validated empirical findings.

## Technical references

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC automated-access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [pandas merge_asof](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html)
- [scikit-learn data leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html)
- [yfinance download API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)

No redistribution license is granted by this repository. Third-party data remain subject to their providers' terms.
