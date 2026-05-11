import streamlit as st
import pandas as pd
import numpy as np
import json
import os

from calculations import run_projection as _run_projection, DEFAULTS, compute_break_even

# --- PAGE CONFIG ---
st.set_page_config(page_title="Project HUGO: Master Financial Analysis", layout="wide")
st.title("🚁 Project HUGO: Fleet Economics & Sensitivity Engine")

# --- STATE MANAGEMENT (LOAD/SAVE DEFAULTS) ---
DEFAULT_FILE = "hugo_defaults.json"

# Define all input keys and default values (imported from calculations.py, mutable copy for session)
DEFAULTS = dict(DEFAULTS)

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
    st.session_state.cert_flat = st.number_input("Certification Flat Rate (€)", value=st.session_state.cert_flat,
                                                  step=1000)

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
    st.session_state.doa_cost = st.number_input("DOA Certification (Annual) (€)", value=st.session_state.doa_cost,
                                                 step=1000)

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
                   int_rate=None, infl_rate=None, total_flights_override=None, price_override=None):
    return _run_projection(dict(st.session_state), rd_mult, cert_mult, rev_mult, fixed_mult, var_mult,
                           int_rate, infl_rate, total_flights_override, price_override)


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

    time_to_inv = summary["Time to Make Up Investment (Years)"]
    t1, t2, t3 = st.columns(3)
    if time_to_inv != float('inf'):
        t1.metric("Time to Make Up Investment", f"{time_to_inv:.1f} years",
                   help="Loan / Yearly Operating Profit — years to fully exit debt if all profit goes to repayment")
    else:
        t1.metric("Time to Make Up Investment", "N/A (negative profit)")

    borrowed = summary["Borrowed Amount"]
    owed = summary["Amount Owed at Operations Start"]
    interest_accrued = owed - borrowed

    st.subheader("Loan Summary (Development-Period Interest)")
    l1, l2, l3 = st.columns(3)
    l1.metric("Borrowed Amount", f"€{borrowed:,.0f}")
    l2.metric("Amount Owed at Operations Start", f"€{owed:,.0f}",
              delta=f"€{interest_accrued:,.0f} interest accrued over {st.session_state.dev_years:.1f} dev years",
              delta_color="inverse")
    l3.metric("Interest Accrued During Dev", f"€{interest_accrued:,.0f}")

    st.subheader("CAPEX Breakdown")
    capex_labels = ["R&D (Labor + Proto + GCS)", "Certification", "Fleet (Drones)"]
    capex_values = [summary["Total R&D CAPEX"], summary["Total Cert CAPEX"], summary["Fleet CAPEX"]]
    capex_df = pd.DataFrame({"Category": capex_labels, "Amount (€)": capex_values})

    import plotly.express as px
    fig = px.pie(capex_df, values="Amount (€)", names="Category",
                 title="CAPEX Allocation",
                 hole=0.4)
    fig.update_traces(textposition="inside", textinfo="percent+label+value")
    st.plotly_chart(fig, width="stretch")

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
                        "Variable Ops Multiplier", "Interest Rate (%)", "Inflation Rate (%)",
                        "Total Flights/Year", "Price per Flight (€)"]
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

            roi_rows = []
            sweep_vals_be = []
            year10_cash_be = []
            year1_cash_be = []

            steps = np.arange(s_start, s_end + (s_step / 100), s_step)
            for val in steps:
                val = round(val, 2)
                actual_val = val
                kwargs = {"rd_mult": 1.0, "cert_mult": 1.0, "rev_mult": 1.0, "fixed_mult": 1.0, "var_mult": 1.0,
                          "int_rate": st.session_state.interest, "infl_rate": st.session_state.inflation}

                if target == "R&D Multiplier":
                    kwargs["rd_mult"] = val
                    actual_val = val * summary['Base R&D (Unmultiplied)']
                elif target == "Cert Multiplier":
                    kwargs["cert_mult"] = val
                    actual_val = val * summary['Base Cert (Unmultiplied)']
                elif target == "Revenue Multiplier":
                    kwargs["rev_mult"] = val
                    actual_val = val * summary['Base Revenue (Unmultiplied)']
                elif target == "Fixed Ops Multiplier":
                    kwargs["fixed_mult"] = val
                    actual_val = val * summary['Base Fixed Ops (Unmultiplied)']
                elif target == "Variable Ops Multiplier":
                    kwargs["var_mult"] = val
                    actual_val = val * summary['Base Var Cost/Day (Unmultiplied)']
                elif target == "Interest Rate (%)":
                    kwargs["int_rate"] = val
                elif target == "Inflation Rate (%)":
                    kwargs["infl_rate"] = val
                elif target == "Total Flights/Year":
                    actual_val = val * st.session_state.fleet_size * st.session_state.days_per_drone
                    kwargs["total_flights_override"] = actual_val
                elif target == "Price per Flight (€)":
                    actual_val = val * st.session_state.price_per_day
                    kwargs["price_override"] = actual_val

                _, _, history, summary_sweep = run_projection(**kwargs)

                # Add column to chart dataframe
                chart_df[f"{actual_val:g}"] = history

                # Compute display value for the table
                if target == "Revenue Multiplier":
                    display_val = f"€{val * summary['Base Revenue (Unmultiplied)']:,.0f}"
                elif target == "R&D Multiplier":
                    display_val = f"€{val * summary['Base R&D (Unmultiplied)']:,.0f}"
                elif target == "Cert Multiplier":
                    display_val = f"€{val * summary['Base Cert (Unmultiplied)']:,.0f}"
                elif target == "Fixed Ops Multiplier":
                    display_val = f"€{val * summary['Base Fixed Ops (Unmultiplied)']:,.0f}"
                elif target == "Variable Ops Multiplier":
                    display_val = f"€{val * summary['Base Var Cost/Day (Unmultiplied)']:,.0f}"
                elif target in ["Interest Rate (%)", "Inflation Rate (%)"]:
                    display_val = f"{val:.1f}%"
                elif target == "Total Flights/Year":
                    display_val = f"{int(actual_val)}"
                elif target == "Price per Flight (€)":
                    display_val = f"€{actual_val:,.0f}"
                else:
                    display_val = f"{val:.2f}x"

                # ROI time for this sweep step
                roi_time = summary_sweep["Time to Make Up Investment (Years)"]
                if summary_sweep.get("First Year Infeasible", False):
                    time_display = "Infeasible"
                elif roi_time != float('inf'):
                    time_display = f"{roi_time:.2f}"
                else:
                    time_display = "Never"

                roi_rows.append({
                    target: display_val,
                    "Time to Make Up Investment (Years)": time_display
                })
                sweep_vals_be.append(actual_val)
                year10_cash_be.append(history[-1])
                year1_cash_be.append(history[1])

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

            # ROI time table
            st.markdown("**Time to Make Up Investment**")
            st.table(pd.DataFrame(roi_rows))

            # Profitability threshold (where year 1 cash flow crosses zero)
            min_viable, _ = compute_break_even(target, sweep_vals_be, year1_cash_be, summary)
            if min_viable is not None:
                if target == "Revenue Multiplier":
                    st.metric("Min Revenue for Profitability", f"€{min_viable:,.0f}")
                elif target == "R&D Multiplier":
                    st.metric("Max R&D for Profitability", f"€{min_viable:,.0f}")
                elif target == "Cert Multiplier":
                    st.metric("Max Cert for Profitability", f"€{min_viable:,.0f}")
                elif target == "Fixed Ops Multiplier":
                    st.metric("Max Fixed Ops for Profitability", f"€{min_viable:,.0f}")
                elif target == "Variable Ops Multiplier":
                    st.metric("Max Variable Ops for Profitability", f"€{min_viable:,.0f}")
                elif target == "Interest Rate (%)":
                    st.metric("Max Interest Rate for Profitability", f"{min_viable:.2f}%")
                elif target == "Inflation Rate (%)":
                    st.metric("Max Inflation Rate for Profitability", f"{min_viable:.2f}%")
                elif target == "Total Flights/Year":
                    st.metric("Min Flights for Profitability", f"{int(round(min_viable))}")
                elif target == "Price per Flight (€)":
                    st.metric("Min Price for Profitability", f"€{min_viable:,.0f}")
            else:
                st.info("No profitability threshold found within sweep range")

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