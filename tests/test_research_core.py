"""Deterministic boundary checks. Fixtures are not empirical research results."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from research_core import (fact_table, choose_ttm_flow, choose_balance, compute_quality,
    match_events, attach_forward_returns, event_profile, assign_history_buckets,
    chronological_holdout)


class ResearchChecks(unittest.TestCase):
    def test_one_session_return_is_not_entry_to_itself(self):
        prices = pd.DataFrame({'A': [100., 110., 121.], '^GSPC': [100., 100., 100.]},
                              index=pd.bdate_range('2024-01-02', periods=3))
        events = pd.DataFrame({'ticker':['A'], 'earnings_date':[pd.Timestamp('2024-01-01')]})
        result = attach_forward_returns(events, prices, horizons=(1, 2))
        self.assertAlmostEqual(result.loc[0, 'return_1d'], .1)
        self.assertAlmostEqual(result.loc[0, 'return_2d'], .21)
        self.assertNotEqual(result.loc[0, 'entry_1d'], result.loc[0, 'exit_1d'])

    def test_insufficient_forward_history_is_missing(self):
        prices = pd.DataFrame({'A':[100.], '^GSPC':[100.]}, index=pd.to_datetime(['2024-01-02']))
        event = pd.DataFrame({'ticker':['A'], 'earnings_date':pd.to_datetime(['2024-01-01'])})
        self.assertTrue(np.isnan(attach_forward_returns(event, prices).loc[0, 'return_1d']))

    def test_missing_entry_price_is_not_zero_return(self):
        prices = pd.DataFrame({'A':[np.nan, 100.], '^GSPC':[100., 100.]}, index=pd.bdate_range('2024-01-02', periods=2))
        event = pd.DataFrame({'ticker':['A'], 'earnings_date':pd.to_datetime(['2024-01-01'])})
        self.assertTrue(np.isnan(attach_forward_returns(event, prices).loc[0, 'return_1d']))

    def test_event_profile_uses_all_horizon_observations(self):
        prices = pd.DataFrame({'A':[100., 110., 121.], '^GSPC':[100., 100., 100.]}, index=pd.bdate_range('2024-01-02', periods=3))
        events = pd.DataFrame({'ticker':['A'], 'earnings_date':pd.to_datetime(['2024-01-01']), 'composite_quintile':[5]})
        result = event_profile(events, prices, 5, max_horizon=2)
        self.assertAlmostEqual(result.iloc[0], .1)
        self.assertAlmostEqual(result.iloc[1], .2)  # additive daily CAR

    def test_instant_facts_do_not_require_start(self):
        facts = {'facts':{'us-gaap':{'Assets':{'units':{'USD':[{'val':50, 'end':'2023-12-31','filed':'2024-02-01'}]}}}}}
        result = fact_table(facts, 'assets', {'assets':[('us-gaap','Assets')]})
        self.assertEqual(choose_balance(result, '2024-02-02', '2023-12-31'), 50)

    def test_ttm_uses_annual_plus_current_ytd_less_prior_ytd(self):
        frame = pd.DataFrame([
            {'start':'2023-01-01','end':'2023-12-31','filed':'2024-02-01','value':100.,'tag_priority':0},
            {'start':'2024-01-01','end':'2024-06-30','filed':'2024-08-01','value':70.,'tag_priority':0},
            {'start':'2023-01-01','end':'2023-06-30','filed':'2023-08-01','value':40.,'tag_priority':0},
            {'start':'2024-01-01','end':'2024-06-30','filed':'2025-08-01','value':999.,'tag_priority':0}])
        for col in ['start','end','filed']: frame[col] = pd.to_datetime(frame[col])
        self.assertEqual(choose_ttm_flow(frame, '2024-08-02', '2024-06-30'), 130.)

    def test_asof_merge_is_globally_sorted_and_strict(self):
        earnings = pd.DataFrame({'ticker':['B','A','A'], 'earnings_date':pd.to_datetime(['2024-02-03','2024-02-02','2024-02-04']), 'surprise_pct':[1.,2.,3.]})
        filings = pd.DataFrame({'ticker':['A','B','A'], 'filing_date':pd.to_datetime(['2024-02-01','2024-02-01','2024-02-02']), 'quality_score':[.2,.3,.9]})
        result = match_events(earnings, filings)
        self.assertEqual(result.iloc[0]['quality_score'], .2)
        self.assertTrue(result['filing_precedes_earnings'].all())
        self.assertTrue(result['composite_score'].notna().all())

    def test_history_buckets_ignore_future_extremes(self):
        past = pd.DataFrame({'earnings_date':pd.date_range('2024-01-01', periods=25), 'signal':np.arange(25.)})
        before = assign_history_buckets(past, 'signal')
        future = pd.concat([past, pd.DataFrame({'earnings_date':[pd.Timestamp('2025-01-01')], 'signal':[1e12]})], ignore_index=True)
        after = assign_history_buckets(future, 'signal').iloc[:25]
        pd.testing.assert_series_equal(before, after)

    def test_holdout_purges_overlapping_labels(self):
        entries = pd.bdate_range('2024-01-01', periods=100)
        events = pd.DataFrame({'ticker':['A']*100, 'entry_21d':entries, 'exit_21d':entries+pd.offsets.BDay(21), 'abnormal_return_21d':np.arange(100.)/1000})
        train, test = chronological_holdout(events.sample(frac=1, random_state=1))
        self.assertTrue(train['exit_21d'].max() < test['entry_21d'].min())
        self.assertTrue(train['entry_21d'].is_monotonic_increasing)

    def test_quality_scores_do_not_change_when_future_filings_are_appended(self):
        rows=[]
        for i in range(6):
            rows.append(dict(ticker=str(i), filing_date=pd.Timestamp('2024-02-01'), revenue=100.+i,
                prior_year_revenue=90., gross_profit=40.+i, prior_year_gross_margin=.4,
                assets=200.+i, prior_year_assets=180., net_income=10.+i, cfo=12.+i, liabilities=100.))
        past = pd.DataFrame(rows)
        future = past.copy(); future['filing_date']=pd.Timestamp('2025-02-01'); future['net_income']=100000.
        before = compute_quality(past)['quality_score']
        after = compute_quality(pd.concat([past,future], ignore_index=True)).iloc[:6]['quality_score']
        pd.testing.assert_series_equal(before, after)


if __name__ == '__main__':
    unittest.main(verbosity=2)
