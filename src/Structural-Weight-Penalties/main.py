from Canard_estimations import *
from Empennage_estimations import *


if __name__ == "__main__":
    print("--- Canard Port Structural Impact Analysis ---\n")
    results = analyze_canard_structural_impact()
    
    for metric, value in results.items():
        # Add visual separators for readability
        if "NET TOTAL" in metric or "Significance -" in metric:
            print("-" * 55)
        print(f"{metric:<45}: {value}")

    print("\n--- Empennage Structural Impact Analysis ---\n")
    results = analyze_empennage_structural_impact()

    for metric, value in results.items():
        # Add visual separators for readability
        if "NET TOTAL" in metric or "Significance -" in metric:
            print("-" * 55)
        print(f"{metric:<45}: {value}")