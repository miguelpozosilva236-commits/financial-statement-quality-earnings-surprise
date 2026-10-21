"""Bounded, cached source downloads for the fixed academic study.

Raw market-provider data stay local. No credentials or personal contact details
are embedded. Requests stop rather than rotate routes after access/rate limits.
"""
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import hashlib
import json
import time
import pandas as pd
import yfinance as yf

PROJECT_URL = 'https://github.com/miguelpozosilva236-commits/financial-statement-quality-earnings-surprise'
DEFAULT_SEC_USER_AGENT = f'VicentePozoAcademicResearch/1.0 (+{PROJECT_URL})'


class SourceAccessError(RuntimeError):
    pass


def provenance(path, source, operation, retrieved=None):
    path = Path(path)
    record = dict(source=source, operation=operation,
                  retrieved_utc=retrieved or datetime.now(timezone.utc).isoformat(),
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  bytes=path.stat().st_size)
    path.with_suffix(path.suffix + '.meta.json').write_text(json.dumps(record, indent=2))


def get_json(url, path, user_agent=DEFAULT_SEC_USER_AGENT):
    path = Path(path)
    if path.exists():
        metadata_path = path.with_suffix(path.suffix + '.meta.json')
        if metadata_path.exists() and json.loads(metadata_path.read_text()).get('source') != url:
            raise ValueError(f'Cached source identity differs for {path.name}; inspect before reuse.')
        return json.loads(path.read_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(Request(url, headers={'User-Agent': user_agent,
                                         'Accept-Encoding': 'identity'}), timeout=45) as r:
            payload = r.read()
    except HTTPError as exc:
        if exc.code in (403, 429):
            raise SourceAccessError(f'Source denied or rate-limited access ({exc.code}); stop.') from exc
        raise
    data = json.loads(payload)
    path.write_bytes(payload)
    provenance(path, url, 'HTTP GET JSON')
    time.sleep(.3)
    return data


def filing_history(cik, submissions, directory, start, end, user_agent=DEFAULT_SEC_USER_AGENT):
    """Include only archive files returned by SEC that overlap the fixed window."""
    parts = [pd.DataFrame(submissions.get('filings', {}).get('recent', {}))]
    for item in submissions.get('filings', {}).get('files', []):
        if str(item.get('filingTo', '')) < start or str(item.get('filingFrom', '9999')) >= end:
            continue
        name = item['name']
        payload = get_json(f'https://data.sec.gov/submissions/{name}', Path(directory)/name, user_agent)
        parts.append(pd.DataFrame(payload))
    frame = pd.concat([part.dropna(axis=1, how='all') for part in parts if not part.empty], ignore_index=True)
    frame['filingDate'] = pd.to_datetime(frame['filingDate'], errors='coerce')
    frame['reportDate'] = pd.to_datetime(frame['reportDate'], errors='coerce')
    frame = frame[frame['form'].isin(['10-K', '10-Q'])]
    frame = frame[frame['filingDate'].ge(start) & frame['filingDate'].lt(end)]
    return frame.drop_duplicates('accessionNumber').sort_values('filingDate')


def market_prices(ticker, start, end, directory):
    path = Path(directory)/f'{ticker.replace("^", "INDEX_")}_prices.csv'
    if path.exists():
        cached = pd.read_csv(path, index_col=0)
        cached.index = pd.to_datetime(cached.index)
        return cached.iloc[:, 0].rename(ticker)
    data = yf.download(ticker, start=start, end=end, auto_adjust=True,
                       progress=False, threads=False, timeout=30)
    if data.empty:
        raise SourceAccessError(f'No market data for {ticker}; stop and inspect source access.')
    close = data['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close = pd.to_numeric(close, errors='coerce').dropna().rename(ticker)
    close.to_csv(path)
    provenance(path, f'https://finance.yahoo.com/quote/{ticker}/history/',
               f'yfinance.download auto_adjust=True; start={start}; end_exclusive={end}')
    time.sleep(.8)
    return close


def earnings_events(ticker, directory):
    path = Path(directory)/f'{ticker}_earnings.csv'
    if path.exists():
        frame = pd.read_csv(path, index_col=0)
        frame.index = pd.to_datetime(frame.index, utc=True).tz_convert('America/New_York')
        return frame
    frame = yf.Ticker(ticker).get_earnings_dates(limit=50)
    if frame is None or frame.empty:
        raise SourceAccessError(f'No earnings dates for {ticker}; stop and inspect coverage.')
    frame.to_csv(path)
    provenance(path, f'https://finance.yahoo.com/quote/{ticker}/earnings/',
               'yfinance.Ticker.get_earnings_dates(limit=50); historical estimate vintage unverified')
    time.sleep(.8)
    return frame
