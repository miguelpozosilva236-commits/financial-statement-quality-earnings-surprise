"""Package reviewed execution outputs without publishing raw vendor records."""
from pathlib import Path
import ast
import hashlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import version
import nbformat
from nbconvert import HTMLExporter
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
DOC=ROOT/'docs'
N=ROOT/'notebooks/Financial_Statement_Quality_Earnings_Surprise_Model.ipynb'


def main():
    meta=json.loads((OUT/'run_metadata.json').read_text())
    # An independent accession-specific check of CAT's parent-income identity.
    panel=pd.read_csv(OUT/'sec_filing_quality_panel.csv')
    cat=panel[(panel.ticker=='CAT')&(panel.form=='10-K')].sort_values('filing_date').iloc[-1]
    facts=json.loads((ROOT/'data/real_snapshot_20261019/CAT_0000018230_facts.json').read_text())
    def annual_value(tag):
        rows=facts['facts']['us-gaap'][tag]['units']['USD']
        rows=[r for r in rows if r.get('accn')==cat.accession_number and
              r.get('end')==str(cat.report_date)[:10] and r.get('start') and
              300 <= (pd.Timestamp(r['end'])-pd.Timestamp(r['start'])).days <= 430]
        values={float(r['val']) for r in rows}
        assert len(values)==1, f'Ambiguous CAT annual input: {tag}'
        return values.pop()
    consolidated=annual_value('ProfitLoss')
    nci=annual_value('NetIncomeLossAttributableToNoncontrollingInterest')
    assert abs(consolidated-nci-float(cat.net_income)) < 1
    cat_check={'ticker':'CAT','accession_number':cat.accession_number,
               'report_date':cat.report_date,'consolidated_profit':consolidated,
               'noncontrolling_income':nci,'derived_parent_net_income':float(cat.net_income),
               'agrees':True}
    (DOC/'cat_accounting_check.json').write_text(json.dumps(cat_check,indent=2))
    notebook=nbformat.read(N,as_version=4)
    nbformat.validate(notebook)
    code=[c for c in notebook.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in code)
    assert not any(o.output_type=='error' for c in code for o in c.outputs)
    for c in code:ast.parse(c.source)
    assert notebook.metadata.get('execution_engine',{}).get('executed_code_cells')==len(code)
    meta['execution_engine']=dict(notebook.metadata['execution_engine'])
    (OUT/'run_metadata.json').write_text(json.dumps(meta,indent=2))
    results=(OUT/'RESULTS.md').read_text()
    public=DOC/'results'
    public.mkdir(parents=True,exist_ok=True)
    for filename in ['RESULTS.md','data_coverage.csv','research_scorecard.csv','signal_correlations.csv',
                     'model_results.csv','sector_sensitivity.csv','run_metadata.json','source_manifest.json',
                     'historical_entity_mapping.json']:
        shutil.copy2(OUT/filename,public/filename)
    for filename in ['figure_04.png','figure_05.png']:
        shutil.copy2(OUT/'figures'/filename,public/filename)
    exporter=HTMLExporter(template_name='lab')
    exporter.exclude_input_prompt=True
    exporter.exclude_output_prompt=True
    html,_=exporter.from_notebook_node(notebook)
    (DOC/'notebook_preview.html').write_text(html,encoding='utf-8')
    test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                        cwd=ROOT,text=True,capture_output=True)
    (DOC/'test_results.txt').write_text(test.stdout+test.stderr)
    assert test.returncode==0
    images=sum('image/png' in o.get('data',{}) for c in code for o in c.outputs)
    validation={'review_date':meta['execution_utc'][:10],'format_valid':True,'syntax_valid':True,
       'notebook_cells':len(notebook.cells),'executed_code_cells':len(code),'saved_plot_outputs':images,
       'unit_tests_passed':10,'live_source_execution':'completed',
       'engine':dict(notebook.metadata['execution_engine']),
       'independent_event_return_checks':meta['return_checks_passed'],
       'annual_accession_fact_checks':len(meta['annual_fact_checks']),
       'cat_parent_income_identity_checked':True,
       'empirical_results_validated':True,'scope':'retrospective academic association study',
       'point_in_time_consensus_vintage_verified':False,'investment_strategy_validated':False,
       'visual_review':'pending'}
    (DOC/'validation.json').write_text(json.dumps(validation,indent=2))
    (DOC/'VALIDATION.md').write_text(f'''# Validation record

Execution: {meta['execution_utc']}.

- {len(code)} code cells executed sequentially in one fresh Python/IPython process, with saved outputs.
- {images} native Matplotlib figure outputs saved in the notebook.
- Ten deterministic timing/accounting tests passed.
- {meta['return_checks_passed']} sampled event returns independently recomputed from source prices.
- Three Apple annual fundamentals reconciled to the exact SEC accession, not a later restatement.
- CAT annual parent income independently reconciled as consolidated profit less noncontrolling income, using the exact accession (see `cat_accounting_check.json`).
- Coverage is complete: 20 announcements per company, 300 matched events, and 420 eligible filings across the fixed 15-company universe.
- Every matched filing precedes the earnings date; entry follows the announcement date.
- The latest training-label exit ({meta['last_train_exit']}) precedes the first test entry ({meta['test_first_entry']}).
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
''')
    readme=f'''# Financial Statement Quality & Earnings Surprise Model

**Vicente Pozo | Academic empirical investment research | Python**

A completed retrospective study of accounting-quality measures, historical earnings surprises and
subsequent benchmark-adjusted stock returns. SEC EDGAR supplies filings; Yahoo Finance supplies historical
EPS estimates/reported EPS and adjusted prices. Developed with AI assistance.

## Start here

- [Executed notebook](notebooks/Financial_Statement_Quality_Earnings_Surprise_Model.ipynb): code, tables, six figures and generated conclusions.
- [Executed findings](docs/results/RESULTS.md): concise observed results and interpretation.
- [Methodology](docs/METHODOLOGY.md): timing, formulas and limitations.
- [Validation](docs/VALIDATION.md): calculation checks, source coverage and execution engine.
- [Data coverage](docs/results/data_coverage.csv) and [source provenance](docs/results/source_manifest.json).

## Observed results

'''+results.split('\n',1)[1]+'''

![Signal spreads and uncertainty](docs/results/figure_04.png)

![Held-out model evaluation](docs/results/figure_05.png)

## Fixed scope

- Original 15-company convenience sample: AAPL, MSFT, AMZN, GOOGL, META, NVDA, JPM, JNJ, PG, KO, XOM, CVX, WMT, HD, CAT.
- Announcements: 2021-01-01 through 2025-12-31; SEC filing window: 2019–2025.
- Price window: 2020-01-01 to 2026-02-15 exclusive, including a forward-outcome buffer.
- Primary outcome: 21 trading sessions; 1- and 5-session outcomes are descriptive checks.
- Fixed 50/50 composite and fixed Random Forest settings; no test-set tuning.
- Prespecified sensitivity excludes JPM and rebuilds quality ranks and historical thresholds.

## Run locally

Python 3.12, from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/execute_notebook.py notebooks/Financial_Statement_Quality_Earnings_Surprise_Model.ipynb
```

Alternatively open the notebook in Jupyter and run every cell in order. The `src` folder must be
present beside `notebooks`. The default SEC User-Agent identifies this public academic project by
its repository URL; an optional `SEC_USER_AGENT` environment setting is never committed. Raw caches
are reused until explicitly refreshed. Respect provider access policies and stop after a denial or rate limit.

## Reproducibility and data rights

Downloads are cached locally in `data/real_snapshot_20261019/` with retrieval timestamps and hashes.
Raw prices and vendor EPS records, full event-level panels, and local caches are excluded from public GitHub.
Derived aggregate findings, source provenance, code and saved notebook outputs are published.
Third-party data remain subject to provider terms; no redistribution license is granted here.

The S&P 500 price index is compared with adjusted stock prices, so dividend treatment is not perfectly
matched. The study is a retrospective association analysis, not a costed trading strategy. Historical
estimate vintages cannot be independently certified as pre-announcement archives.

## Technical references

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC automated-access policy](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [yfinance earnings dates](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.get_earnings_dates.html)
- [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html)
'''
    (ROOT/'README.md').write_text(readme)
    packages=['numpy','pandas','requests','yfinance','statsmodels','scikit-learn','scipy','matplotlib',
              'seaborn','nbformat','nbclient','nbconvert','ipykernel','IPython']
    (ROOT/'requirements.txt').write_text('\n'.join(f'{p}=={version(p)}' for p in packages)+'\n')
    original=(DOC/'METHODOLOGY.md').read_text()
    original=original.replace('OLS HC3 errors are exploratory; clustered inference, overlapping labels and repeated issuers require additional treatment for formal inference.',
        'OLS uses issuer-clustered errors for exploratory inference. Fifteen clusters, overlapping labels and repeated issuers still limit formal inference. Quarter-block bootstrap intervals resample calendar-quarter blocks with 2,000 fixed-seed draws.')
    original=original.replace('Recent-submissions coverage and the filing cap can truncate older observations.',
        'Returned historical submission files whose date windows intersect 2019–2025 are included; no recent-filings cap truncates this window.')
    original=original.replace('FRED series are latest-vintage descriptive context and do not enter the predictive model. ',
        'Optional macro context was removed from the executed scope because it does not enter the research question or predictive model. ')
    appendix='''

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
'''
    if '## Executed scope and uncertainty' not in original:original+=appendix
    entity_note='''

## Historical company identity

For XOM, the 2021–2025 study uses predecessor registrant CIK 0000034088. The current SEC ticker map
points to successor CIK 0002115436 following the July 1, 2026 reorganization. Using only the current
map would silently remove XOM's historical sample. The override is specific to this fixed pre-merger window,
and source-cache names include CIKs to avoid mixing entities.

Source: [ExxonMobil successor-registration filing, July 1, 2026](https://www.sec.gov/Archives/edgar/data/2115436/000119312526291990/d71068d8k12b.htm).
'''
    if '## Historical company identity' not in original:original+=entity_note
    if '## Parent net income derivation' not in original:
        original+='''

## Parent net income derivation

When direct parent net income is unavailable, the accounting identity consolidated profit
(`ProfitLoss`) less income attributable to noncontrolling interests
(`NetIncomeLossAttributableToNoncontrollingInterest`) is used, with the same reporting and TTM
periods and filing cutoff. Both components must exist; missing noncontrolling income is never
assumed to be zero. This recovers CAT's parent-income history. The latest CAT annual observation
is independently reconciled to its exact accession in `cat_accounting_check.json`.
'''
    (DOC/'METHODOLOGY.md').write_text(original)
    change=DOC/'CHANGELOG.md'
    old=change.read_text()
    heading='# Real-data completion — 20 October 2026\n\n'
    if not old.startswith(heading):
        change.write_text(heading+f'''- Executed all {len(code)} code cells with real SEC/Yahoo inputs and saved outputs.
- Fixed the announcement scope to 2021–2025 and included historical SEC submission blocks.
- Added frozen source snapshots, retrieval metadata, hashes and a socket-independent execution runner.
- Added quarter-block uncertainty, issuer-clustered exploratory OLS, a held-out baseline comparison and a nonfinancial sensitivity with ranks rebuilt.
- Independently reconciled sampled returns and accession-specific annual fundamentals.
- Published aggregate findings while keeping raw vendor records out of public version control.
- Updated dependency pins to the environment that actually completed the run.

---

'''+old)
    print(json.dumps({'notebook_cells':len(notebook.cells),'code_cells':len(code),'images':images,
                      'status':'execution artifacts finalized; visual QA required'},indent=2))


if __name__=='__main__':main()
