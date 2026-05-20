import numpy as np
import pandas as pd


DEFAULTS = {
    "dev_years": 2.0, "dev_engineers": 4, "eng_salary": 65000, "proto_cost": 150000, "gcs_cost": 50000,
    "cert_flat": 7000,
    "fleet_size": 5, "days_per_drone": 30, "price_per_day": 8500, "drone_unit_cost": 50000,
    "perm_rd": 1, "num_managers": 1, "mgr_salary": 80000, "base_rent": 24000, "rent_mult": 1.5, "ins_per_drone": 5000,
    "doa_cost": 10000,
    "logistics": 600, "fuel": 350, "maint": 500, "num_ops": 2, "op_wage": 40, "flight_hours": 10,
    "interest": 6.5, "loan_term": 5, "inflation": 2.5, "index_revenue": True
}


def run_projection(params, rd_mult=1.0, cert_mult=1.0, rev_mult=1.0, fixed_mult=1.0, var_mult=1.0,
                   int_rate=None, infl_rate=None, total_flights_override=None, price_override=None):
    P = params

    if int_rate is None:
        int_rate = P["interest"]
    if infl_rate is None:
        infl_rate = P.get("inflation", 0.0)

    # 1. CAPEX Breakdown
    dev_labor = P["dev_engineers"] * P["eng_salary"] * P["dev_years"]
    base_dev = (dev_labor + P["proto_cost"] + P["gcs_cost"]) * rd_mult
    base_cert = P["cert_flat"] * cert_mult
    fleet_capex = P["fleet_size"] * P["drone_unit_cost"]
    total_capex = base_dev + base_cert + fleet_capex

    # 2. Base Year (Year 1) Operations
    total_flights = P["fleet_size"] * P["days_per_drone"]
    if total_flights_override is not None:
        total_flights = total_flights_override
    effective_price = price_override if price_override is not None else P["price_per_day"]
    base_rev = (total_flights * effective_price) * rev_mult

    perm_rd_cost = P["perm_rd"] * P["eng_salary"]
    mgmt_cost = P["num_managers"] * P["mgr_salary"]
    rent_cost = P["base_rent"] * P["rent_mult"]
    ins_cost = P["fleet_size"] * P["ins_per_drone"]
    base_annual_fixed = (perm_rd_cost + mgmt_cost + rent_cost + ins_cost + P["doa_cost"]) * fixed_mult

    crew_cost = P["num_ops"] * P["op_wage"] * P["flight_hours"]
    base_var_cost_per_day = (P["logistics"] + P["fuel"] + P["maint"] + crew_cost) * var_mult
    base_annual_var_cost = total_flights * base_var_cost_per_day

    # 3. Loan (Fixed Annuity) — interest accrues during development
    if int_rate > 0:
        r = int_rate / 100
        owed_at_start = total_capex * (1 + r) ** P["dev_years"]
        annuity = owed_at_start * (r * (1 + r) ** P["loan_term"]) / ((1 + r) ** P["loan_term"] - 1)
    else:
        owed_at_start = total_capex
        annuity = 0

    cum_cash = 0
    history = [cum_cash]

    base_ebitda = base_rev - base_annual_fixed - base_annual_var_cost

    # 4. 10-Year Dynamic Loop
    for y in range(1, 11):
        infl_factor = (1 + (infl_rate / 100)) ** (y - 1)

        current_fixed = base_annual_fixed * infl_factor
        current_var = base_annual_var_cost * infl_factor

        if P.get("index_revenue", False):
            current_rev = base_rev * infl_factor
        else:
            current_rev = base_rev

        profit = current_rev - current_fixed - current_var

        if y <= P["loan_term"]:
            profit -= annuity

        cum_cash += profit
        history.append(cum_cash)

    summary_data = {
        "Total Flights/Year": total_flights,
        "Total R&D CAPEX": base_dev,
        "Total Cert CAPEX": base_cert,
        "GCS & Equip CAPEX": P["gcs_cost"],
        "Fleet CAPEX": fleet_capex,
        "Borrowed Amount": total_capex,
        "Amount Owed at Operations Start": owed_at_start,
        "Perm R&D Staff (Base Yr)": perm_rd_cost,
        "Management & Rent (Base Yr)": mgmt_cost + rent_cost,
        "Total Var Cost per Flight (Base Yr)": base_var_cost_per_day,
        "Crew Cost per Flight (Base Yr)": crew_cost,
        "Gross Margin per Flight (Base Yr)": (effective_price * rev_mult) - base_var_cost_per_day,
        "Time to Make Up Investment (Years)": owed_at_start / base_ebitda if base_ebitda > 0 else float('inf'),
        "Base Revenue (Unmultiplied)": total_flights * effective_price,
        "Base R&D (Unmultiplied)": dev_labor + P["proto_cost"] + P["gcs_cost"],
        "Base Cert (Unmultiplied)": P["cert_flat"],
        "Base Fixed Ops (Unmultiplied)": perm_rd_cost + mgmt_cost + rent_cost + ins_cost + P["doa_cost"],
        "Base Var Cost/Day (Unmultiplied)": P["logistics"] + P["fuel"] + P["maint"] + crew_cost,
        "First Year Infeasible": history[1] < 0 if len(history) > 1 else False,
    }

    return total_capex, base_ebitda, history, summary_data


def analyze_hugo_limits(df):
    df_yr3 = df[df['Year'] == 3]

    baseline_row = df_yr3[(df_yr3['Sweep Target'] == 'R&D Multiplier') & (np.isclose(df_yr3['Sweep Value'], 1.0))]
    base_cash = baseline_row['Cumulative Cash'].iloc[0] if not baseline_row.empty else None

    results = []

    for target in df_yr3['Sweep Target'].unique():
        subset = df_yr3[df_yr3['Sweep Target'] == target]
        x = subset['Sweep Value'].values
        y = subset['Cumulative Cash'].values

        slope, intercept = np.polyfit(x, y, 1)

        if abs(slope) > 1e-5:
            limit = -intercept / slope
        else:
            limit = float('inf')

        if target == 'Interest Rate (%)':
            distance = abs(limit - 6.5) / 6.5
        else:
            distance = abs(limit - 1.0) / 1.0

        results.append({
            'Target': target,
            'Limit': limit,
            'Relative Distance': distance
        })

    results = sorted(results, key=lambda x: x['Relative Distance'])
    return base_cash, results


def compute_break_even(target, sweep_values, year_n_cash, summary_data, year1_cash=None):
    """Find the break-even sweep value where cumulative cash at year N crosses zero.

    If year1_cash is provided, also requires year 1 cash flow >= 0 (feasible).
    Returns (min_viable, value_at_min) or (None, None) if no crossing found.
    """
    pairs = sorted(zip(sweep_values, year_n_cash))
    financial_be = None
    for i in range(len(pairs) - 1):
        v1, c1 = pairs[i]
        v2, c2 = pairs[i + 1]
        if (c1 <= 0 < c2) or (c2 <= 0 < c1):
            t = -c1 / (c2 - c1)
            financial_be = v1 + t * (v2 - v1)
            break

    feasibility_be = None
    if year1_cash is not None:
        if all(f < 0 for f in year1_cash):
            return None, None
        feas_pairs = sorted(zip(sweep_values, year1_cash))
        for i in range(len(feas_pairs) - 1):
            v1, f1 = feas_pairs[i]
            v2, f2 = feas_pairs[i + 1]
            if f1 < 0 <= f2:
                t = -f1 / (f2 - f1)
                feasibility_be = v1 + t * (v2 - v1)
                break

    candidates = [v for v in [financial_be, feasibility_be] if v is not None]
    if not candidates:
        return None, None

    min_viable = max(candidates)

    if target == "Revenue Multiplier":
        value_at_min = min_viable * summary_data.get("Base Revenue (Unmultiplied)", 0)
    elif target == "R&D Multiplier":
        value_at_min = min_viable * summary_data.get("Base R&D (Unmultiplied)", 0)
    elif target == "Cert Multiplier":
        value_at_min = min_viable * summary_data.get("Base Cert (Unmultiplied)", 0)
    elif target == "Fixed Ops Multiplier":
        value_at_min = min_viable * summary_data.get("Base Fixed Ops (Unmultiplied)", 0)
    elif target == "Variable Ops Multiplier":
        value_at_min = min_viable * summary_data.get("Base Var Cost/Day (Unmultiplied)", 0)
    else:
        value_at_min = min_viable

    return min_viable, value_at_min
