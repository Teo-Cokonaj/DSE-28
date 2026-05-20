import pandas as pd
import numpy as np


def analyze_hugo_limits(csv_file="hugo_sensitivity_matrix.csv"):
    print(f"Analyzing {csv_file}...\n")

    # Load the sweep data
    df = pd.read_csv(csv_file)

    # Filter for the end of the 10-year projection to assess long-term viability
    df_yr10 = df[df['Year'] == 3]

    # Get the baseline cash (where multipliers = 1.0)
    baseline_row = df_yr10[(df_yr10['Sweep Target'] == 'R&D Multiplier') & (np.isclose(df_yr10['Sweep Value'], 1.0))]
    if not baseline_row.empty:
        base_cash = baseline_row['Cumulative Cash'].iloc[0]
        print(f"Base 3-Year Cumulative Cash: €{base_cash:,.0f}\n")

    print("--- Viability Limits (Break-Even Threshold at Year 3) ---")

    results = []

    for target in df_yr10['Sweep Target'].unique():
        subset = df_yr10[df_yr10['Sweep Target'] == target]
        x = subset['Sweep Value'].values
        y = subset['Cumulative Cash'].values

        # Use linear extrapolation to find where Cash = 0 (y = mx + c  => x = -c/m)
        slope, intercept = np.polyfit(x, y, 1)

        if abs(slope) > 1e-5:
            limit = -intercept / slope
        else:
            limit = float('inf')

        # Calculate how far this limit is from the baseline
        # (Assuming baseline interest rate was 6.5%, and multipliers are 1.0)
        if target == 'Interest Rate (%)':
            distance = abs(limit - 6.5) / 6.5
        else:
            distance = abs(limit - 1.0) / 1.0

        results.append({
            'Target': target,
            'Limit': limit,
            'Relative Distance': distance
        })

    # Sort by the most constraining (smallest relative distance to break the business)
    results = sorted(results, key=lambda x: x['Relative Distance'])

    for r in results:
        target = r['Target']
        limit = r['Limit']

        if target == 'Revenue Multiplier':
            print(
                f"{target:25}: Must remain ABOVE {limit:6.2f}x baseline")
        elif target == 'Interest Rate (%)':
            print(f"{target:25}: Must remain BELOW {limit:6.1f}%")
        else:
            print(
                f"{target:25}: Must remain BELOW {limit:6.2f}x baseline")

    print(f"\n=> Most Constraining Factor: {results[0]['Target']}")


if __name__ == "__main__":
    analyze_hugo_limits()