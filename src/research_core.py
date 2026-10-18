"""Timing and accounting helpers for the academic research notebook.

No network access on import. Functions use explicit inputs for reproducible checks.
"""
import numpy as np
import pandas as pd

WEIGHTS = {"cfo_ni_ratio": 1., "accrual_ratio": -1., "roaa": 1.,
           "gross_margin_change": .75, "revenue_growth": .5, "leverage": -.75}


def numeric(values):
    return pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)


def fact_table(facts, name, fact_tags):
    """Combine alternative USD tags; retain filing dates and tag priority."""
    parts = []
    for priority, (taxonomy, tag) in enumerate(fact_tags[name]):
        units = facts.get("facts", {}).get(taxonomy, {}).get(tag, {}).get("units", {})
        records = units.get("USD", [])
        if not records:
            continue
        frame = pd.DataFrame(records)
        for column in ("start", "end", "filed"):
            if column not in frame:
                frame[column] = pd.NaT
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
        frame["value"] = numeric(frame["val"])
        frame["tag_priority"] = priority
        parts.append(frame.dropna(subset=["end", "filed", "value"]))
    if not parts:
        return pd.DataFrame(columns=["start", "end", "filed", "value", "tag_priority"])
    return pd.concat(parts, ignore_index=True).sort_values(["end", "filed", "tag_priority"])


def _latest_fact(frame):
    if frame.empty:
        return np.nan
    # Prefer latest disclosed revision, then the preferred accounting tag.
    return float(frame.sort_values(["filed", "tag_priority"], ascending=[False, True]).iloc[0]["value"])


def choose_ttm_flow(frame, filed_date, report_date):
    """Annual flow or FY + current YTD - comparable prior YTD, all known as of filing.

    Missing compatible periods remain NaN rather than mixing annual/quarterly
    amounts or treating missing cash flow as zero.
    """
    if frame.empty:
        return np.nan
    fd, rd = pd.Timestamp(filed_date), pd.Timestamp(report_date)
    x = frame[(frame["filed"] <= fd) & (frame["end"] <= rd + pd.Timedelta(days=7))].copy()
    duration = (x["end"] - x["start"]).dt.days
    annual = x[duration.between(300, 430)]
    direct = annual[(annual["end"] - rd).abs() <= pd.Timedelta(days=7)]
    if not direct.empty:
        return _latest_fact(direct)
    annual = annual[annual["end"] < rd - pd.Timedelta(days=7)]
    if annual.empty:
        return np.nan
    annual_end = annual["end"].max()
    base = annual[annual["end"] == annual_end].sort_values(
        ["filed", "tag_priority"], ascending=[False, True]).iloc[0]
    if (rd - annual_end).days > 310:
        return np.nan
    current = x[((x["end"] - rd).abs() <= pd.Timedelta(days=7)) &
                ((x["start"] - (annual_end + pd.Timedelta(days=1))).abs() <= pd.Timedelta(days=14))]
    prior_end = rd - pd.DateOffset(years=1)
    prior = x[((x["end"] - prior_end).abs() <= pd.Timedelta(days=14)) &
              ((x["start"] - base["start"]).abs() <= pd.Timedelta(days=14))]
    current_value, prior_value = _latest_fact(current), _latest_fact(prior)
    if not np.isfinite(current_value) or not np.isfinite(prior_value):
        return np.nan
    return float(base["value"] + current_value - prior_value)


def choose_balance(frame, filed_date, report_date):
    if frame.empty:
        return np.nan
    fd, rd = pd.Timestamp(filed_date), pd.Timestamp(report_date)
    x = frame[(frame["filed"] <= fd) &
              ((frame["end"] - rd).abs() <= pd.Timedelta(days=7))]
    return _latest_fact(x)


def compute_quality(features, min_peers=5):
    """Score each filing using a one-row-per-issuer information set available then."""
    out = features.sort_values(["filing_date", "ticker"]).reset_index(drop=True).copy()
    out["gross_margin"] = out["gross_profit"] / out["revenue"].replace(0, np.nan)
    out["revenue_growth"] = out["revenue"] / out["prior_year_revenue"].replace(0, np.nan) - 1
    out["gross_margin_change"] = out["gross_margin"] - out["prior_year_gross_margin"]
    out["avg_assets"] = (out["assets"] + out["prior_year_assets"]) / 2
    denom = out["avg_assets"].where(out["avg_assets"] > 0)
    out["roaa"] = out["net_income"] / denom
    out["accrual_ratio"] = (out["net_income"] - out["cfo"]) / denom
    out["cfo_ni_ratio"] = out["cfo"] / out["net_income"].where(out["net_income"] > 0)
    out["leverage"] = out["liabilities"] / out["assets"].where(out["assets"] > 0)
    for metric in WEIGHTS:
        out[metric] = numeric(out[metric])
    out["quality_score"] = np.nan
    out["quality_coverage"] = 0.
    out["quality_peer_count"] = 0
    for day, indices in out.groupby("filing_date", sort=True).groups.items():
        known = out.loc[out["filing_date"] <= day].drop_duplicates("ticker", keep="last").set_index("ticker")
        scores, coverages = [], []
        for metric, weight in WEIGHTS.items():
            values = known[metric]
            count = values.notna().sum()
            rank = values.rank(method="average")
            centered = (2 * (rank - 1) / (count - 1) - 1) if count >= min_peers else values * np.nan
            scores.append(centered * weight)
            coverages.append(centered.notna() * abs(weight))
        numerator = pd.concat(scores, axis=1).sum(axis=1, min_count=1)
        denominator = pd.concat(coverages, axis=1).sum(axis=1)
        score = (numerator / denominator.replace(0, np.nan)).where(
            denominator / sum(abs(w) for w in WEIGHTS.values()) >= .5)
        for index in indices:
            ticker = out.at[index, "ticker"]
            out.at[index, "quality_score"] = score.get(ticker, np.nan)
            out.at[index, "quality_coverage"] = denominator.get(ticker, 0) / sum(abs(w) for w in WEIGHTS.values())
            out.at[index, "quality_peer_count"] = len(known)
    return out


def match_events(earnings, features):
    left = earnings.dropna(subset=["earnings_date"]).sort_values(["earnings_date", "ticker"])
    right = features.dropna(subset=["filing_date"]).sort_values(["filing_date", "ticker"])
    events = pd.merge_asof(left, right, left_on="earnings_date", right_on="filing_date",
                           by="ticker", direction="backward", allow_exact_matches=False)
    events["filing_precedes_earnings"] = events["filing_date"] < events["earnings_date"]
    events = events.dropna(subset=["quality_score", "surprise_pct"]).copy()
    # Fixed ex-ante 20-percentage-point scale avoids same-day sparse z-scores.
    events["surprise_signal"] = np.tanh(events["surprise_pct"] / 20.)
    events["composite_score"] = .5 * events["surprise_signal"] + .5 * events["quality_score"]
    if not events["filing_precedes_earnings"].all():
        raise AssertionError("A filing did not precede its matched announcement.")
    return events.sort_values(["earnings_date", "ticker"]).reset_index(drop=True)


def attach_forward_returns(events, prices, benchmark="^GSPC", horizons=(1, 5, 21)):
    out = events.copy()
    if benchmark not in prices:
        raise ValueError("Missing benchmark prices.")
    index = prices[benchmark].dropna().index.sort_values()
    for horizon in horizons:
        entries, exits, stock_returns, adjusted_returns = [], [], [], []
        for _, event in out.iterrows():
            dates = index[index > pd.Timestamp(event["earnings_date"])]
            entry = exit_date = pd.NaT
            stock_return = adjusted = np.nan
            if event["ticker"] in prices and len(dates) > horizon:
                entry, exit_date = dates[0], dates[horizon]
                s0, s1 = prices.loc[[entry, exit_date], event["ticker"]]
                b0, b1 = prices.loc[[entry, exit_date], benchmark]
                if np.isfinite([s0, s1, b0, b1]).all() and min(s0, s1, b0, b1) > 0:
                    stock_return = s1 / s0 - 1
                    adjusted = stock_return - (b1 / b0 - 1)
            entries.append(entry); exits.append(exit_date)
            stock_returns.append(stock_return); adjusted_returns.append(adjusted)
        out[f"entry_{horizon}d"] = entries
        out[f"exit_{horizon}d"] = exits
        out[f"return_{horizon}d"] = stock_returns
        out[f"abnormal_return_{horizon}d"] = adjusted_returns
    return out


def assign_history_buckets(events, value_column, lookback_days=365, min_history=20):
    """Use only observations strictly before each announcement date for cutoffs."""
    out = pd.Series(np.nan, index=events.index)
    for day, indices in events.groupby("earnings_date", sort=True).groups.items():
        history = events.loc[(events["earnings_date"] < day) &
                             (events["earnings_date"] >= day - pd.Timedelta(days=lookback_days)), value_column].dropna()
        if len(history) < min_history or history.nunique() < 5:
            continue
        thresholds = history.quantile([.2, .4, .6, .8]).to_numpy()
        if len(np.unique(thresholds)) < 4:
            continue
        current = events.loc[indices, value_column].dropna()
        out.loc[current.index] = np.searchsorted(thresholds, current.to_numpy(), side="right") + 1
    return out


def event_profile(events, prices, bucket_value, benchmark="^GSPC", max_horizon=21):
    """Additive daily abnormal returns from entry close; includes h+1 prices."""
    sub = events[events["composite_quintile"] == bucket_value]
    index = prices[benchmark].dropna().index.sort_values()
    paths = []
    for _, event in sub.iterrows():
        dates = index[index > event["earnings_date"]][:max_horizon + 1]
        if len(dates) != max_horizon + 1:
            continue
        pair = prices.loc[dates, [event["ticker"], benchmark]]
        if pair.isna().any().any() or (pair <= 0).any().any():
            continue
        returns = pair.pct_change(fill_method=None).iloc[1:]
        paths.append((returns.iloc[:, 0] - returns.iloc[:, 1]).cumsum().to_numpy())
    return (pd.Series(np.vstack(paths).mean(axis=0), index=np.arange(1, max_horizon + 1))
            if paths else pd.Series(dtype=float))


def chronological_holdout(events, target="abnormal_return_21d", fraction=.75):
    data = events.dropna(subset=[target, "entry_21d", "exit_21d"]).sort_values(["entry_21d", "ticker"])
    dates = data["entry_21d"].drop_duplicates().sort_values()
    if len(dates) < 4:
        return data.iloc[:0], data.iloc[:0]
    cutoff = dates.iloc[min(max(1, int(len(dates) * fraction)), len(dates) - 1)]
    train = data[(data["entry_21d"] < cutoff) & (data["exit_21d"] < cutoff)]
    test = data[data["entry_21d"] >= cutoff]
    return train, test
