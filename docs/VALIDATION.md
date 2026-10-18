# Validation record

Review date: 16 October 2026, America/Lima.

## Passed

- Jupyter notebook schema validation: 26 cells.
- Python syntax parsing for every code cell.
- Ten deterministic unit tests: forward-return horizons, insufficient history, missing prices, additive CAR, instant XBRL facts, TTM construction with future-revision exclusion, strict as-of joins, future-invariant bucket thresholds, label-maturity purge and future-invariant quality scores.

Run the tests from the project directory:

```bash
python -m unittest discover -s tests -v
```

The standalone helper definitions are embedded from the same source into the reviewed notebook. The tests use small constructed inputs solely to verify calculations; they are not reported as empirical research findings.

## Remaining

A complete real-data execution has not passed. This environment prohibits Jupyter kernel sockets, so the kernel could not start. Sequential execution of the pure-Python cells in-process successfully reached cell 3 and stopped at the missing SEC User-Agent configuration. Yahoo also returned HTTP 429 during the provider access check. No artificial market results were substituted. Configure the contact setting, run in an environment with a working Jupyter kernel and provider access, execute all cells and inspect the resulting figures/tables before reporting empirical findings.

Notebook HTML preview is a static code/documentation view; it is not evidence of a successful empirical run. No strategy returns, model RMSE or statistical significance are asserted in this delivery.
