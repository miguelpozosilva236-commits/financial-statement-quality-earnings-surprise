# Validation record

Execution: 2026-10-20T21:56:02.354424+00:00.

- 14 code cells executed sequentially in one fresh Python/IPython process, with saved outputs.
- 6 native Matplotlib figure outputs saved in the notebook.
- Ten deterministic timing/accounting tests passed.
- 10 sampled event returns independently recomputed from source prices.
- Three Apple annual fundamentals reconciled to the exact SEC accession, not a later restatement.
- CAT annual parent income independently reconciled as consolidated profit less noncontrolling income, using the exact accession (see `cat_accounting_check.json`).
- Coverage is complete: 20 announcements per company, 300 matched events, and 420 eligible filings across the fixed 15-company universe.
- Every matched filing precedes the earnings date; entry follows the announcement date.
- The latest training-label exit (2024-09-30) precedes the first test entry (2024-10-16).
- Source snapshots have retrieval timestamps, byte counts and SHA-256 hashes.

## Execution engine

The host blocks TCP kernel sockets, so nbclient could not start its Jupyter kernel. The included
`scripts/execute_notebook.py` runs each actual code cell in a fresh local IPython process, fails on the
first error, captures stdout/rich tables, and saves native Matplotlib plots into notebook outputs.
This is a complete computational execution, with its engine explicitly recorded; it is not a successful
Jupyter-kernel connectivity check. On an unrestricted local machine, ordinary Jupyter execution is also supported.

## Boundaries

Completed retrospective empirical analysis is not proof of forecasting skill, causation, investable alpha,
or an audited point-in-time consensus dataset. Historical vendor estimates may have been revised.
The fixed survivor universe, dependent events, limited quarter blocks/clusters and accounting-sector
differences remain disclosed. Public outputs contain derived aggregates; raw vendor event/price records are not published.

## Visual review

All six saved charts were inspected for readable titles, axes, units and clipping. The linear price-context chart is dominated by NVDA; the signal and held-out model charts remain the primary result figures.
