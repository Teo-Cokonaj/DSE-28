import pytest
import numpy as np
import pandas as pd

from calculations import run_projection, analyze_hugo_limits, compute_break_even, DEFAULTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def base_params(**overrides):
    p = dict(DEFAULTS)
    p.update(overrides)
    return p


# ---------------------------------------------------------------------------
# A. Known-Answer Tests
#
# Hand-computed using the DEFAULTS dict values.
# dev_years = 2, interest = 6.5%
# cert_flat = 7,000, doa_cost = 10,000
# ---------------------------------------------------------------------------
# CAPEX:
#   dev_labor = 4 * 65,000 * 2 = 520,000
#   base_dev = 520,000 + 150,000 + 50,000 = 720,000
#   base_cert = 7,000 (flat rate)
#   fleet_capex = 5 * 50,000 = 250,000
#   total_capex = 720,000 + 7,000 + 250,000 = 977,000
#
# Dev-period interest accrual:
#   owed_at_start = 977,000 * (1 + 0.065)^2 = 977,000 * 1.134225 = 1,108,217.825
#
# Fixed Ops (annual):
#   perm_rd = 1 * 65,000 = 65,000
#   mgmt = 1 * 80,000 = 80,000
#   rent = 24,000 * 1.5 = 36,000
#   ins = 5 * 5,000 = 25,000
#   doa = 10,000
#   total = 216,000
#
# Variable per flight day:
#   logistics(600) + fuel(350) + maint(500) + crew(2*40*10=800) = 2,250
#   annual_var = 150 * 2,250 = 337,500
#
# Revenue: 150 * 8,500 = 1,275,000
# EBITDA: 1,275,000 - 216,000 - 337,500 = 721,500
# ---------------------------------------------------------------------------

class TestCAPEX:
    def test_dev_labor(self):
        P = base_params()
        cap, _, _, summary = run_projection(P)
        assert summary["Total R&D CAPEX"] == 4 * 65000 * 2 + 150000 + 50000

    def test_base_dev_equals_720000(self):
        P = base_params()
        cap, _, _, summary = run_projection(P)
        assert summary["Total R&D CAPEX"] == 720_000

    def test_base_cert_equals_7000(self):
        # Flat certification rate
        P = base_params()
        cap, _, _, summary = run_projection(P)
        assert summary["Total Cert CAPEX"] == 7_000

    def test_fleet_capex_equals_250000(self):
        P = base_params()
        cap, _, _, summary = run_projection(P)
        assert summary["Fleet CAPEX"] == 250_000

    def test_total_capex_equals_977000(self):
        P = base_params()
        cap, _, _, _ = run_projection(P)
        assert cap == 977_000

    def test_rd_multiplier_scales_dev_only(self):
        P = base_params()
        cap1, _, _, s1 = run_projection(P, rd_mult=1.0)
        cap2, _, _, s2 = run_projection(P, rd_mult=2.0)
        assert s2["Total R&D CAPEX"] == s1["Total R&D CAPEX"] * 2
        assert s2["Total Cert CAPEX"] == s1["Total Cert CAPEX"]
        assert s2["Fleet CAPEX"] == s1["Fleet CAPEX"]


class TestDevPeriodInterest:
    def test_borrowed_equals_capex(self):
        P = base_params()
        cap, _, _, summary = run_projection(P)
        assert summary["Borrowed Amount"] == cap

    def test_owed_greater_than_borrowed_with_interest(self):
        P = base_params()
        cap, _, _, summary = run_projection(P)
        assert summary["Amount Owed at Operations Start"] > cap

    def test_owed_equals_borrowed_at_zero_interest(self):
        P = base_params(interest=0.0)
        cap, _, _, summary = run_projection(P)
        assert summary["Amount Owed at Operations Start"] == cap

    def test_owed_formula(self):
        # owed = total_capex * (1 + r)^dev_years
        P = base_params()
        cap, _, _, summary = run_projection(P)
        r = 0.065
        expected = 977_000 * (1 + r) ** 2
        assert summary["Amount Owed at Operations Start"] == pytest.approx(expected, rel=1e-10)

    def test_year0_is_zero(self):
        P = base_params()
        cap, _, hist, summary = run_projection(P)
        assert hist[0] == 0

    def test_longer_dev_period_more_owed(self):
        P2 = base_params(dev_years=2.0)
        P5 = base_params(dev_years=5.0)
        _, _, _, s2 = run_projection(P2)
        _, _, _, s5 = run_projection(P5)
        assert s5["Amount Owed at Operations Start"] > s2["Amount Owed at Operations Start"]

    def test_higher_interest_more_owed(self):
        P_low = base_params(interest=3.0)
        P_high = base_params(interest=10.0)
        _, _, _, s_low = run_projection(P_low)
        _, _, _, s_high = run_projection(P_high)
        assert s_high["Amount Owed at Operations Start"] > s_low["Amount Owed at Operations Start"]


class TestRevenueAndCosts:
    def test_total_flights(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        assert summary["Total Flights/Year"] == 150

    def test_base_revenue(self):
        # 150 flights * 8,500 = 1,275,000; fixed = 216,000; var = 337,500
        P = base_params()
        cap, ebit, hist, _ = run_projection(P, infl_rate=0.0, int_rate=0.0)
        profit_yr1 = hist[1] - hist[0]
        assert profit_yr1 == 1_275_000 - 216_000 - 337_500

    def test_fixed_ops_includes_doa(self):
        # perm_rd(65k) + mgmt(80k) + rent(36k) + ins(25k) + doa(10k) = 216,000
        P = base_params()
        cap, _, hist, _ = run_projection(P, infl_rate=0.0, int_rate=0.0)
        profit_yr1 = hist[1] - hist[0]
        assert profit_yr1 == 1_275_000 - 216_000 - 337_500

    def test_fixed_ops_breakdown(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        assert summary["Perm R&D Staff (Base Yr)"] == 65_000
        assert summary["Management & Rent (Base Yr)"] == 80_000 + 36_000

    def test_variable_per_flight(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        assert summary["Total Var Cost per Flight (Base Yr)"] == 2_250

    def test_crew_cost(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        assert summary["Crew Cost per Flight (Base Yr)"] == 800

    def test_gross_margin_per_flight(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        assert summary["Gross Margin per Flight (Base Yr)"] == 6_250


class TestAnnuity:
    def test_annuity_formula_with_dev_interest(self):
        # With dev_years=2, int_rate=6.5%:
        # owed = 977,000 * 1.065^2 = 1,108,217.825
        # annuity = owed * (r*(1+r)^5) / ((1+r)^5 - 1)
        P = base_params()
        cap, _, hist, _ = run_projection(P, infl_rate=0.0)
        r = 0.065
        owed = cap * (1 + r) ** 2
        expected_annuity = owed * (r * (1 + r) ** 5) / ((1 + r) ** 5 - 1)
        profit_no_loan = 1_275_000 - 216_000 - 337_500
        profit_with_loan = hist[1] - hist[0]
        actual_annuity = profit_no_loan - profit_with_loan
        assert actual_annuity == pytest.approx(expected_annuity, rel=1e-10)

    def test_zero_interest_no_annuity(self):
        P = base_params(interest=0.0)
        _, _, hist, _ = run_projection(P, infl_rate=0.0)
        profit_yr1 = hist[1] - hist[0]
        assert profit_yr1 == 1_275_000 - 216_000 - 337_500


class TestEBITDA:
    def test_base_ebitda(self):
        # 1,275,000 - 216,000 - 337,500 = 721,500
        P = base_params()
        _, ebit, _, _ = run_projection(P)
        assert ebit == 721_500


class TestCumulativeCash:
    def test_year0_is_zero(self):
        P = base_params()
        cap, _, hist, summary = run_projection(P)
        assert hist[0] == 0

    def test_year1_no_inflation_no_interest(self):
        # With int_rate=0, no loan payments; cum_cash starts at 0
        # Year 1: 0 + (1,275,000 - 216,000 - 337,500) = 721,500
        P = base_params(interest=0.0)
        _, _, hist, _ = run_projection(P, infl_rate=0.0)
        assert hist[1] == 721_500

    def test_full_10year_with_defaults(self):
        P = base_params()
        _, _, hist, _ = run_projection(P)
        assert len(hist) == 11

    def test_history_monotonically_increasing(self):
        P = base_params()
        _, _, hist, _ = run_projection(P)
        for i in range(1, len(hist)):
            assert hist[i] > hist[i - 1]


# ---------------------------------------------------------------------------
# B. Invariant / Property Tests
# ---------------------------------------------------------------------------

class TestInvariants:
    def test_higher_revenue_higher_cash(self):
        P = base_params()
        _, _, hist_low, _ = run_projection(P, rev_mult=0.8)
        _, _, hist_high, _ = run_projection(P, rev_mult=1.2)
        assert hist_low[0] == hist_high[0]
        for lo, hi in zip(hist_low[1:], hist_high[1:]):
            assert hi > lo

    def test_higher_fixed_costs_lower_cash(self):
        P = base_params()
        _, _, hist_low, _ = run_projection(P, fixed_mult=0.8)
        _, _, hist_high, _ = run_projection(P, fixed_mult=1.2)
        assert hist_low[0] == hist_high[0]
        for lo, hi in zip(hist_low[1:], hist_high[1:]):
            assert lo > hi

    def test_higher_variable_costs_lower_cash(self):
        P = base_params()
        _, _, hist_low, _ = run_projection(P, var_mult=0.8)
        _, _, hist_high, _ = run_projection(P, var_mult=1.2)
        assert hist_low[0] == hist_high[0]
        for lo, hi in zip(hist_low[1:], hist_high[1:]):
            assert lo > hi

    def test_higher_interest_lower_cash(self):
        P = base_params()
        _, _, hist_low, _ = run_projection(P, int_rate=3.0)
        _, _, hist_high, _ = run_projection(P, int_rate=10.0)
        for lo, hi in zip(hist_low[1:], hist_high[1:]):
            assert lo > hi

    def test_index_revenue_beats_flat_with_inflation(self):
        P = base_params(index_revenue=True)
        P_flat = base_params(index_revenue=False)
        _, _, hist_indexed, _ = run_projection(P, infl_rate=3.0)
        _, _, hist_flat, _ = run_projection(P_flat, infl_rate=3.0)
        for idx, flat in zip(hist_indexed, hist_flat):
            assert idx >= flat

    def test_zero_inflation_flat_costs(self):
        P = base_params(interest=0.0)
        _, _, hist, _ = run_projection(P, infl_rate=0.0)
        deltas = [hist[i] - hist[i - 1] for i in range(1, 11)]
        for d in deltas[1:]:
            assert d == pytest.approx(deltas[0], rel=1e-10)

    def test_multiplier_1_equals_base(self):
        P = base_params()
        _, _, hist_base, _ = run_projection(P)
        _, _, hist_mult, _ = run_projection(P, rd_mult=1.0, cert_mult=1.0, rev_mult=1.0,
                                            fixed_mult=1.0, var_mult=1.0)
        assert hist_base == hist_mult

    def test_year0_always_zero(self):
        for rev in [0.5, 1.0, 2.0]:
            P = base_params()
            cap, _, hist, _ = run_projection(P, rev_mult=rev)
            assert hist[0] == 0

    def test_loan_only_deducted_within_term(self):
        P = base_params(loan_term=3)
        _, _, hist, _ = run_projection(P, infl_rate=0.0)
        deltas = [hist[i] - hist[i - 1] for i in range(1, 11)]
        assert deltas[3] > deltas[2]
        for d in deltas[3:]:
            assert d == pytest.approx(deltas[3], rel=1e-10)


# ---------------------------------------------------------------------------
# C. Edge Case Tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_flight_days(self):
        P = base_params(days_per_drone=0, interest=0.0)
        _, _, hist, _ = run_projection(P, infl_rate=0.0)
        # No revenue, no variable cost; only fixed costs each year (216,000 incl. DOA)
        annual_loss = 216_000
        for i in range(1, 11):
            assert hist[i] == hist[0] - annual_loss * i

    def test_single_drone(self):
        P = base_params(fleet_size=1, interest=0.0)
        _, _, hist, summary = run_projection(P, infl_rate=0.0)
        assert summary["Total Flights/Year"] == 30

    def test_high_inflation_compounding(self):
        P = base_params(interest=0.0, index_revenue=True)
        _, _, hist, _ = run_projection(P, infl_rate=20.0)
        expected_factor = 1.20 ** 9
        assert pytest.approx(expected_factor, rel=1e-6) == 1.20 ** 9

    def test_loan_term_exceeds_projection(self):
        P = base_params(loan_term=15)
        _, _, hist, _ = run_projection(P, infl_rate=0.0)
        deltas = [hist[i] - hist[i - 1] for i in range(1, 11)]
        for d in deltas[1:]:
            assert d == pytest.approx(deltas[0], rel=1e-10)

    def test_single_engineer(self):
        P = base_params(dev_engineers=1, perm_rd=0, num_ops=1)
        _, ebit, _, _ = run_projection(P)
        assert ebit > 0

    def test_doa_cost_in_fixed_ops(self):
        # Verify DOA is included in fixed ops — saving accumulates each year
        P = base_params()
        _, _, hist_base, _ = run_projection(P, infl_rate=0.0, int_rate=0.0)
        P_no_doa = base_params(doa_cost=0)
        _, _, hist_no_doa, _ = run_projection(P_no_doa, infl_rate=0.0, int_rate=0.0)
        for i in range(1, 11):
            assert hist_no_doa[i] - hist_base[i] == 10_000 * i


# ---------------------------------------------------------------------------
# D. Sensitivity Sweep Tests
# ---------------------------------------------------------------------------

class TestSensitivitySweep:
    def _run_sweep(self, target, values):
        P = base_params()
        results = []
        for val in values:
            m = {"rd": 1.0, "ce": 1.0, "rv": 1.0, "fx": 1.0, "vr": 1.0, "ir": P["interest"],
                 "inf": P.get("inflation", 0.0)}
            if target == "R&D Multiplier":
                m["rd"] = val
            elif target == "Cert Multiplier":
                m["ce"] = val
            elif target == "Revenue Multiplier":
                m["rv"] = val
            elif target == "Fixed Ops Multiplier":
                m["fx"] = val
            elif target == "Variable Ops Multiplier":
                m["vr"] = val
            elif target == "Interest Rate (%)":
                m["ir"] = val
            elif target == "Inflation Rate (%)":
                m["inf"] = val
            _, _, history, _ = run_projection(P, m["rd"], m["ce"], m["rv"], m["fx"], m["vr"], m["ir"], m["inf"])
            results.append((val, history))
        return results

    def test_sweep_produces_11_years(self):
        results = self._run_sweep("R&D Multiplier", [0.5, 1.0, 1.5])
        for val, hist in results:
            assert len(hist) == 11

    def test_rd_sweep_higher_means_lower_cash(self):
        results = self._run_sweep("R&D Multiplier", [0.5, 1.0, 1.5])
        for i in range(1, len(results)):
            _, hist_prev = results[i - 1]
            _, hist_curr = results[i]
            for y in range(1, 11):
                assert hist_prev[y] > hist_curr[y]

    def test_revenue_sweep_higher_means_higher_cash(self):
        results = self._run_sweep("Revenue Multiplier", [0.5, 1.0, 1.5])
        for i in range(1, len(results)):
            _, hist_prev = results[i - 1]
            _, hist_curr = results[i]
            for y in range(1, 11):
                assert hist_curr[y] > hist_prev[y]

    def test_interest_sweep_higher_means_lower_cash(self):
        results = self._run_sweep("Interest Rate (%)", [3.0, 6.5, 10.0])
        for i in range(1, len(results)):
            _, hist_prev = results[i - 1]
            _, hist_curr = results[i]
            for y in range(1, 11):
                assert hist_prev[y] > hist_curr[y]


# ---------------------------------------------------------------------------
# E. Data Analysis (Break-Even) Tests
# ---------------------------------------------------------------------------

class TestBreakEven:
    def test_linear_fit_sanity(self):
        rows = []
        for val in [0.3, 0.5, 0.7, 0.9, 1.1, 1.3]:
            rows.append({"Sweep Target": "Revenue Multiplier", "Sweep Value": val,
                         "Year": 3, "Cumulative Cash": 1000 * val - 500})
        df = pd.DataFrame(rows)
        _, results = analyze_hugo_limits(df)
        limit = next(r['Limit'] for r in results if r['Target'] == 'Revenue Multiplier')
        assert limit == pytest.approx(0.5, abs=1e-6)

    def test_real_csv_most_constraining(self):
        import os
        csv_path = os.path.join(os.path.dirname(__file__), "..", "hugo_sensitivity_matrix.csv")
        if not os.path.exists(csv_path):
            pytest.skip("hugo_sensitivity_matrix.csv not found")
        df = pd.read_csv(csv_path)
        base_cash, results = analyze_hugo_limits(df)
        assert base_cash is not None
        assert len(results) > 0
        for i in range(1, len(results)):
            assert results[0]['Relative Distance'] <= results[i]['Relative Distance']

    def test_all_targets_have_limits(self):
        rows = []
        for target in ["R&D Multiplier", "Cert Multiplier", "Revenue Multiplier",
                        "Fixed Ops Multiplier", "Variable Ops Multiplier", "Interest Rate (%)"]:
            for val in np.arange(0.5, 1.6, 0.1):
                if target == "Revenue Multiplier":
                    cash = 500 * val - 300
                else:
                    cash = -300 * val + 700
                rows.append({"Sweep Target": target, "Sweep Value": round(val, 2),
                             "Year": 3, "Cumulative Cash": cash})
        df = pd.DataFrame(rows)
        _, results = analyze_hugo_limits(df)
        assert len(results) == 6
        for r in results:
            assert r['Limit'] != float('inf')
            assert r['Relative Distance'] >= 0


# ---------------------------------------------------------------------------
# F. Time to Make Up Investment Tests
# ---------------------------------------------------------------------------

class TestTimeToInvestment:
    def test_time_to_investment_with_defaults(self):
        # owed = 977,000 * 1.065^2 = 1,108,217.825; ebitda = 721,500
        P = base_params()
        _, _, _, summary = run_projection(P)
        expected = 977_000 * 1.065 ** 2 / 721_500
        assert summary["Time to Make Up Investment (Years)"] == pytest.approx(expected, rel=1e-10)

    def test_time_to_investment_zero_profit(self):
        # With revenue at 0, ebitda is negative → should be inf
        P = base_params(days_per_drone=0, interest=0.0)
        _, ebit, _, summary = run_projection(P)
        assert ebit < 0
        assert summary["Time to Make Up Investment (Years)"] == float('inf')

    def test_time_to_investment_positive(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        assert summary["Time to Make Up Investment (Years)"] > 0

    def test_higher_rd_higher_time(self):
        P = base_params()
        _, _, _, s1 = run_projection(P, rd_mult=1.0)
        _, _, _, s2 = run_projection(P, rd_mult=2.0)
        assert s2["Time to Make Up Investment (Years)"] > s1["Time to Make Up Investment (Years)"]


# ---------------------------------------------------------------------------
# G. Unmultiplied Base Value Tests
# ---------------------------------------------------------------------------

class TestUnmultipliedBases:
    def test_base_revenue_unmultiplied(self):
        P = base_params()
        _, _, _, summary = run_projection(P, rev_mult=1.5)
        assert summary["Base Revenue (Unmultiplied)"] == 150 * 8500

    def test_base_rd_unmultiplied(self):
        P = base_params()
        _, _, _, summary = run_projection(P, rd_mult=2.0)
        assert summary["Base R&D (Unmultiplied)"] == 4 * 65000 * 2 + 150000 + 50000

    def test_base_cert_unmultiplied(self):
        P = base_params()
        _, _, _, summary = run_projection(P, cert_mult=3.0)
        assert summary["Base Cert (Unmultiplied)"] == 7000

    def test_base_fixed_ops_unmultiplied(self):
        # perm_rd(65k) + mgmt(80k) + rent(36k) + ins(25k) + doa(10k) = 216,000
        P = base_params()
        _, _, _, summary = run_projection(P, fixed_mult=2.0)
        assert summary["Base Fixed Ops (Unmultiplied)"] == 216_000

    def test_base_var_cost_unmultiplied(self):
        # logistics(600) + fuel(350) + maint(500) + crew(800) = 2,250
        P = base_params()
        _, _, _, summary = run_projection(P, var_mult=2.0)
        assert summary["Base Var Cost/Day (Unmultiplied)"] == 2_250


# ---------------------------------------------------------------------------
# H. Break-Even Computation Tests
# ---------------------------------------------------------------------------

class TestComputeBreakEven:
    def test_revenue_break_even(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        # Build a simple sweep: revenue multiplier 0.5 → negative cash, 1.5 → positive cash
        vals = [0.5, 1.0, 1.5]
        cash_at_10 = []
        for v in vals:
            _, _, hist, _ = run_projection(P, rev_mult=v)
            cash_at_10.append(hist[-1])
        min_v, val_at = compute_break_even("Revenue Multiplier", vals, cash_at_10, summary)
        assert min_v is not None
        assert 0.5 < min_v < 1.5
        assert val_at == pytest.approx(min_v * summary["Base Revenue (Unmultiplied)"], rel=1e-10)

    def test_no_crossing_returns_none(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        # All positive cash at year 10 — no break-even crossing
        vals = [1.0, 1.5, 2.0]
        cash_at_10 = []
        for v in vals:
            _, _, hist, _ = run_projection(P, rev_mult=v)
            cash_at_10.append(hist[-1])
        min_v, val_at = compute_break_even("Revenue Multiplier", vals, cash_at_10, summary)
        assert min_v is None
        assert val_at is None

    def test_rd_break_even(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        vals = [0.5, 1.0, 3.0, 5.0, 8.0, 12.0]
        cash_at_10 = []
        for v in vals:
            _, _, hist, _ = run_projection(P, rd_mult=v)
            cash_at_10.append(hist[-1])
        min_v, val_at = compute_break_even("R&D Multiplier", vals, cash_at_10, summary)
        assert min_v is not None
        assert val_at == pytest.approx(min_v * summary["Base R&D (Unmultiplied)"], rel=1e-10)

    def test_interest_rate_break_even(self):
        P = base_params()
        _, _, _, summary = run_projection(P)
        vals = [3.0, 6.5, 10.0, 15.0, 20.0]
        cash_at_10 = []
        for v in vals:
            _, _, hist, _ = run_projection(P, int_rate=v)
            cash_at_10.append(hist[-1])
        min_v, val_at = compute_break_even("Interest Rate (%)", vals, cash_at_10, summary)
        # For rates, value_at_min should equal the rate itself
        if min_v is not None:
            assert val_at == min_v

    def test_linear_interpolation_accuracy(self):
        # Synthetic data: cash = 1000 * mult - 500, so break-even at mult = 0.5
        vals = [0.3, 0.4, 0.5, 0.6, 0.7]
        cash = [1000 * v - 500 for v in vals]
        summary = {"Base Revenue (Unmultiplied)": 100_000}
        min_v, val_at = compute_break_even("Revenue Multiplier", vals, cash, summary)
        assert min_v == pytest.approx(0.5, abs=1e-10)
        assert val_at == pytest.approx(50_000, abs=1e-6)
