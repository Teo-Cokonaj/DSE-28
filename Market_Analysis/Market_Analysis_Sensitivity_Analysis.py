import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Project HUGO: Master Financial Analysis", layout="wide")
st.title("🚁 Project HUGO: Fleet Economics & Sensitivity Engine")

# --- STATE MANAGEMENT (LOAD/SAVE DEFAULTS) ---
DEFAULT_FILE = "hugo_defaults.json"

# Define all input keys and default values
DEFAULTS = {
    "dev_years": 2.0, "dev_engineers": 4, "eng_salary": 65000, "proto_cost": 150000, "gcs_cost": 50000,
    "cert_hourly": 250, "cert_hours_yr": 400,
    "fleet_size": 5, "days_per_drone": 30, "price_per_day": 8500, "drone_unit_cost": 50000,
    "perm_rd": 1, "num_managers": 1, "mgr_salary": 80000, "base_rent": 24000, "rent_mult": 1.5, "ins_per_drone": 5000,
    "logistics": 600, "fuel": 350, "maint": 500, "num_ops": 2, "op_wage": 40, "flight_hours": 10,
    "interest": 6.5, "loan_term": 5, "inflation": 2.5, "index_revenue": True
}

# Load defaults if they exist on the hard drive
if 'loaded_defaults' not in st.session_state:
    st.session_state.loaded_defaults = True
    if os.path.exists(DEFAULT_FILE):
        try:
            with open(DEFAULT_FILE, 'r') as f:
                saved_defaults = json.load(f)
                for k, v in saved_defaults.items():
                    if k in DEFAULTS:
                        DEFAULTS[k] = v
        except Exception as e:
            st.error(f"Could not read defaults: {e}")

# Initialize session state with our defaults
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# Function to handle file uploads
def load_config(uploaded_file):
    try:
        data = json.load(uploaded_file)
        for k, v in data.items():
            if k in st.session_state:
                st.session_state[k] = v
        st.success("Configuration Loaded!")
    except Exception as e:
        st.error(f"Error loading file: {e}")


# Function to save defaults
def save_defaults():
    current_state = {k: st.session_state[k] for k in DEFAULTS.keys()}
    with open(DEFAULT_FILE, 'w') as f:
        json.dump(current_state, f)
    st.sidebar.success("Saved as Default!")


# --- SIDEBAR: ALL INPUT CATEGORIES ---
with st.sidebar:
    st.header("💾 Configuration Control")
    save_name = st.text_input("Config Name to Save", value="my_hugo_config")

    # Generate JSON for download
    current_state_json = json.dumps({k: st.session_state[k] for k in DEFAULTS.keys()}, indent=4)
    st.download_button(label="📥 Download Config as JSON", data=current_state_json, file_name=f"{save_name}.json",
                       mime="application/json")

    uploaded_file = st.file_uploader("📤 Load Config JSON", type=["json"])
    if uploaded_file is not None:
        load_config(uploaded_file)

    st.button("💾 Set Current as Default Config", on_click=save_defaults)
    st.divider()

st.sidebar.header("Business Parameters")

with st.sidebar.expander("🛠️ R&D & Design (CAPEX)", expanded=False):
    st.session_state.dev_years = st.number_input("Development Years", value=st.session_state.dev_years, step=0.5)
    st.session_state.dev_engineers = st.number_input("Number of Dev Engineers", value=st.session_state.dev_engineers)
    st.session_state.eng_salary = st.number_input("Engineer Yearly Salary (€)", value=st.session_state.eng_salary,
                                                  step=5000)
    st.session_state.proto_cost = st.number_input("Prototyping & Testing (€)", value=st.session_state.proto_cost,
                                                  step=10000)
    st.session_state.gcs_cost = st.number_input("GCS & Setup Equip (€)", value=st.session_state.gcs_cost, step=5000)

with st.sidebar.expander("📜 Certification (CAPEX)", expanded=False):
    st.session_state.cert_hourly = st.number_input("Cert Hourly Rate (€/hr)", value=st.session_state.cert_hourly)
    st.session_state.cert_hours_yr = st.number_input("Cert Hours per Year per Eng",
                                                     value=st.session_state.cert_hours_yr)

with st.sidebar.expander("📈 Fleet Scaling & Revenue", expanded=False):
    st.session_state.fleet_size = st.number_input("Fleet Size (Total Drones)", value=st.session_state.fleet_size,
                                                  min_value=1)
    st.session_state.days_per_drone = st.number_input("Flight Days per Drone (Annual)",
                                                      value=st.session_state.days_per_drone)
    st.session_state.price_per_day = st.number_input("Charge per Test Day (€)", value=st.session_state.price_per_day,
                                                     step=500)
    st.session_state.drone_unit_cost = st.number_input("Cost per Drone (€)", value=st.session_state.drone_unit_cost)

with st.sidebar.expander("🏢 Fixed Operations (Annual)", expanded=False):
    st.session_state.perm_rd = st.number_input("Permanent R&D Staff", value=st.session_state.perm_rd)
    st.session_state.num_managers = st.number_input("Number of Managers", value=st.session_state.num_managers)
    st.session_state.mgr_salary = st.number_input("Manager Yearly Salary (€)", value=st.session_state.mgr_salary)
    st.session_state.base_rent = st.number_input("Base Annual Rent (€)", value=st.session_state.base_rent)
    st.session_state.rent_mult = st.number_input("Overhead Multiplier", value=st.session_state.rent_mult)
    st.session_state.ins_per_drone = st.number_input("Annual Insurance per Drone (€)",
                                                     value=st.session_state.ins_per_drone)

with st.sidebar.expander("⛽ Per Flight Day Cost", expanded=False):
    st.session_state.logistics = st.number_input("Logistics/Transport (€)", value=st.session_state.logistics)
    st.session_state.fuel = st.number_input("Fuel & Electricity (€)", value=st.session_state.fuel)
    st.session_state.maint = st.number_input("Maintenance Reserve (€)", value=st.session_state.maint)
    st.session_state.num_ops = st.number_input("Crew Size per Flight", value=st.session_state.num_ops)
    st.session_state.op_wage = st.number_input("Operator Hourly Wage (€)", value=st.session_state.op_wage)
    st.session_state.flight_hours = st.number_input("Hours per Flight Day", value=st.session_state.flight_hours)

with st.sidebar.expander("💰 Finances & Macroeconomics", expanded=False):
    st.session_state.interest = st.number_input("Loan Interest Rate (%)", value=st.session_state.interest, step=0.5)
    st.session_state.loan_term = st.number_input("Loan Term (Years)", value=st.session_state.loan_term)
    st.divider()
    st.session_state.inflation = st.number_input("Annual Inflation Rate (%)", value=st.session_state.inflation,
                                                 step=0.5)
    st.session_state.index_revenue = st.checkbox("Index Revenue to Inflation?", value=st.session_state.index_revenue,
                                                 help="If checked, your €8,500 test day price will automatically increase each year to match inflation. If unchecked, your revenue stays flat while costs compound.")


# --- CALCULATION CORE ---
def run_projection(rd_mult=1.0, cert_mult=1.0, rev_mult=1.0, fixed_mult=1.0, var_mult=1.0,
                   int_rate=st.session_state.interest, infl_rate=st.session_state.inflation):
    S = st.session_state

    # 1. CAPEX Breakdown (Occurs at Year 0, unaffected by forward inflation)
    dev_labor = S.dev_engineers * S.eng_salary * S.dev_years
    base_dev = (dev_labor + S.proto_cost + S.gcs_cost) * rd_mult
    base_cert = (S.cert_hourly * S.dev_engineers * S.cert_hours_yr * S.dev_years) * cert_mult
    fleet_capex = S.fleet_size * S.drone_unit_cost
    total_capex = base_dev + base_cert + fleet_capex

    # 2. Base Year (Year 1) Operations
    total_flights = S.fleet_size * S.days_per_drone
    base_rev = (total_flights * S.price_per_day) * rev_mult

    perm_rd_cost = S.perm_rd * S.eng_salary
    mgmt_cost = S.num_managers * S.mgr_salary
    rent_cost = S.base_rent * S.rent_mult
    ins_cost = S.fleet_size * S.ins_per_drone
    base_annual_fixed = (perm_rd_cost + mgmt_cost + rent_cost + ins_cost) * fixed_mult

    crew_cost = S.num_ops * S.op_wage * S.flight_hours
    base_var_cost_per_day = (S.logistics + S.fuel + S.maint + crew_cost) * var_mult
    base_annual_var_cost = total_flights * base_var_cost_per_day

    # 3. Loan (Fixed Annuity, inflation actually helps offset this in real terms)
    if int_rate > 0:
        r = (int_rate / 100)
        annuity = total_capex * (r * (1 + r) ** S.loan_term) / ((1 + r) ** S.loan_term - 1)
    else:
        annuity = 0

    cum_cash = -total_capex
    history = [cum_cash]

    # We will track Year 1 EBITDA to show on the summary page
    base_ebitda = base_rev - base_annual_fixed - base_annual_var_cost

    # 4. 10-Year Dynamic Loop (Applying Compounding Inflation)
    for y in range(1, 11):
        # Calculate inflation compounding factor (Year 1 is 1.0, Year 2 is 1 + infl, etc)
        infl_factor = (1 + (infl_rate / 100)) ** (y - 1)

        # Apply inflation to OPEX
        current_fixed = base_annual_fixed * infl_factor
        current_var = base_annual_var_cost * infl_factor

        # Apply inflation to Revenue (only if user says they can raise prices)
        if S.index_revenue:
            current_rev = base_rev * infl_factor
        else:
            current_rev = base_rev

        profit = current_rev - current_fixed - current_var

        # Deduct fixed loan payments
        if y <= S.loan_term:
            profit -= annuity

        cum_cash += profit
        history.append(cum_cash)

    # Compile Summary Data (Using Year 1 / Base logic for the table)
    summary_data = {
        "Total Flights/Year": total_flights,
        "Total R&D CAPEX": base_dev,
        "Total Cert CAPEX": base_cert,
        "GCS & Equip CAPEX": S.gcs_cost,
        "Fleet CAPEX": fleet_capex,
        "Perm R&D Staff (Base Yr)": perm_rd_cost,
        "Management & Rent (Base Yr)": mgmt_cost + rent_cost,
        "Total Var Cost per Flight (Base Yr)": base_var_cost_per_day,
        "Crew Cost per Flight (Base Yr)": crew_cost,
        "Gross Margin per Flight (Base Yr)": (S.price_per_day * rev_mult) - base_var_cost_per_day
    }

    return total_capex, base_ebitda, history, summary_data


# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Summary", "📈 ROI Analysis", "🌪️ Sensitivity Analysis"])

# Base calculation
cap, ebit, base_history, summary = run_projection()

with tab1:
    st.header("Financial Breakdown")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Upfront CAPEX", f"€{cap:,.0f}")
    c2.metric("Base Year Operating Profit", f"€{ebit:,.0f}")
    c3.metric("Annual Flights", f"{summary['Total Flights/Year']}")

    st.subheader("Cost Breakdowns (Base Year Euros)")
    df_summary = pd.DataFrame([
        {"Category": "R&D Total (CAPEX)", "Amount": f"€{summary['Total R&D CAPEX']:,.0f}"},
        {"Category": "Certification Total (CAPEX)", "Amount": f"€{summary['Total Cert CAPEX']:,.0f}"},
        {"Category": "GCS & Equipment (CAPEX)", "Amount": f"€{summary['GCS & Equip CAPEX']:,.0f}"},
        {"Category": "Perm R&D Staff (Annual OPEX)", "Amount": f"€{summary['Perm R&D Staff (Base Yr)']:,.0f}"},
        {"Category": "Overhead/Mgmt (Annual OPEX)", "Amount": f"€{summary['Management & Rent (Base Yr)']:,.0f}"},
        {"Category": "Direct Cost Per Flight Day", "Amount": f"€{summary['Total Var Cost per Flight (Base Yr)']:,.0f}"},
        {"Category": "Gross Margin Per Flight Day", "Amount": f"€{summary['Gross Margin per Flight (Base Yr)']:,.0f}"}
    ])
    st.table(df_summary)

with tab2:
    st.header("10-Year Return on Investment")
    st.markdown("This chart reflects your base configuration with compounding inflation applied over the 10 years.")
    chart_data = pd.DataFrame({"Base Scenario": base_history}, index=np.arange(0, 11))
    chart_data.index.name = "Year"
    st.line_chart(chart_data)

with tab3:
    st.header("Batch Sensitivity Sweep")
    st.write(
        "Select the levers you want to sweep. The engine will run simulations for each and generate comparative charts.")

    sweeps_available = ["R&D Multiplier", "Cert Multiplier", "Revenue Multiplier", "Fixed Ops Multiplier",
                        "Variable Ops Multiplier", "Interest Rate (%)", "Inflation Rate (%)"]
    selected_sweeps = st.multiselect("Select Variables to Sweep", sweeps_available, default=["R&D Multiplier"])

    col1, col2, col3 = st.columns(3)
    s_start = col1.number_input("Start Value (Use decimal for Mults, % for Int/Inf)", value=0.5)
    s_end = col2.number_input("End Value", value=1.5)
    s_step = col3.number_input("Step Size", value=0.1)

    if st.button("Run Batch Sweep"):
        all_sweep_data = []

        # We loop through each selected sweep category
        for target in selected_sweeps:
            st.subheader(f"Sweep: {target}")

            # DataFrame to hold the multi-line chart data for this specific sweep
            chart_df = pd.DataFrame(index=np.arange(0, 11))
            chart_df.index.name = "Year"

            steps = np.arange(s_start, s_end + (s_step / 100), s_step)
            for val in steps:
                val = round(val, 2)
                # Reset defaults
                m = {"rd": 1.0, "ce": 1.0, "rv": 1.0, "fx": 1.0, "vr": 1.0, "ir": st.session_state.interest,
                     "inf": st.session_state.inflation}

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

                _, _, history, _ = run_projection(m["rd"], m["ce"], m["rv"], m["fx"], m["vr"], m["ir"], m["inf"])

                # Add column to chart dataframe
                chart_df[f"{val}"] = history

                # Record data for the master CSV
                for year, cash in enumerate(history):
                    all_sweep_data.append({
                        "Sweep Target": target,
                        "Sweep Value": val,
                        "Year": year,
                        "Cumulative Cash": cash
                    })

            # Display the multi-line chart with legend
            st.line_chart(chart_df)
            st.divider()

        # Compile Master CSV
        if all_sweep_data:
            master_df = pd.DataFrame(all_sweep_data)
            csv = master_df.to_csv(index=False).encode('utf-8')

            st.success("All sweeps complete! You can download the raw data matrix below.")
            st.download_button(
                label="📥 Download Master Sensitivity CSV",
                data=csv,
                file_name="hugo_sensitivity_matrix.csv",
                mime="text/csv",
            )