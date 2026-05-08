import math

def analyze_canard_structural_impact(
    mtow_kg=100.0,
    max_g_load=4.0,
    canard_lift_fraction=0.20,
    distance_to_bulkhead_m=0.5,
    fuselage_diameter_m=0.15,
    minimum_gauge_m=0.001,           # 1mm practical handling/manufacturing limit
    skin_density_kg_m3=1600.0,       # Default: CFRP density
    skin_yield_strength_pa=600e6,    # Default: CFRP Quasi-isotropic yield
    safety_factor=1.5,
    rod_outer_diameter_m=0.02,
    rod_wall_thickness_m=0.002,
    rod_density_kg_m3=2810.0         # Default: Aluminum 7075-T6 density
):
    """
    Evaluates the total structural weight penalty and comparative significance 
    of adding a transverse canard port to a drone fuselage.
    """
    
    # ---------------------------------------------------------
    # 1. Aerodynamic Loads & Bending Moment
    # ---------------------------------------------------------
    total_lift_n = mtow_kg * max_g_load * 9.81
    canard_force_n = total_lift_n * canard_lift_fraction
    max_bending_moment_nm = canard_force_n * distance_to_bulkhead_m
    radius = fuselage_diameter_m / 2.0
    
    # ---------------------------------------------------------
    # 2. Skin Thickness Sizing (Bending vs. Min Gauge)
    # ---------------------------------------------------------
    # Theoretical thickness required to survive the bending moment
    theoretical_thickness_m = (max_bending_moment_nm * safety_factor) / (math.pi * (radius**2) * skin_yield_strength_pa)
    
    # Actual thickness is bounded by what we can physically manufacture/handle
    actual_required_thickness_m = max(theoretical_thickness_m, minimum_gauge_m)
    design_driven_by = "Bending Loads" if theoretical_thickness_m > minimum_gauge_m else "Minimum Gauge"
    
    # ---------------------------------------------------------
    # 3. Baseline "Clean" Nose Mass
    # ---------------------------------------------------------
    # The baseline is a simple continuous tube sized only to minimum gauge
    baseline_nose_volume = 2 * math.pi * radius * minimum_gauge_m * distance_to_bulkhead_m
    baseline_nose_mass = baseline_nose_volume * skin_density_kg_m3
    
    # ---------------------------------------------------------
    # 4. Global Weight Penalty (Thickening the Nose)
    # ---------------------------------------------------------
    delta_thickness_m = actual_required_thickness_m - minimum_gauge_m
    volume_global_reinforcement = 2 * math.pi * radius * delta_thickness_m * distance_to_bulkhead_m
    mass_global_reinforcement = volume_global_reinforcement * skin_density_kg_m3
    
    # ---------------------------------------------------------
    # 5. Local Weight Penalty (The Hole & Doublers)
    # ---------------------------------------------------------
    cutout_area = math.pi * (rod_outer_diameter_m / 2)**2
    
    # Mass of the skin we are physically removing for the two holes
    mass_removed_skin = 2 * cutout_area * actual_required_thickness_m * skin_density_kg_m3
    
    # Using Kt = 3, we add 3x the removed mass back as local reinforcements
    mass_local_doubler = mass_removed_skin * 3.0 
    
    # ---------------------------------------------------------
    # 6. Hardware Mass (The Rod)
    # ---------------------------------------------------------
    rod_inner_diameter = rod_outer_diameter_m - (2 * rod_wall_thickness_m)
    rod_cross_section = math.pi * ((rod_outer_diameter_m / 2)**2 - (rod_inner_diameter / 2)**2)
    mass_rod = rod_cross_section * fuselage_diameter_m * rod_density_kg_m3
    
    # ---------------------------------------------------------
    # 7. Final Tally & Comparative Significance
    # ---------------------------------------------------------
    net_weight_penalty = mass_global_reinforcement + mass_local_doubler + mass_rod - mass_removed_skin
    new_total_nose_mass = baseline_nose_mass + net_weight_penalty
    
    percentage_increase_local = (net_weight_penalty / baseline_nose_mass) * 100
    percentage_increase_mtow = (net_weight_penalty / mtow_kg) * 100
    
    return {
        "Aerodynamics - Canard Force (N)": round(canard_force_n, 2),
        "Aerodynamics - Max Bending Moment (Nm)": round(max_bending_moment_nm, 2),
        "Sizing - Theoretical Min Thickness (mm)": round(theoretical_thickness_m * 1000, 3),
        "Sizing - Actual Sized Thickness (mm)": round(actual_required_thickness_m * 1000, 3),
        "Sizing - Design Driven By": design_driven_by,
        "Mass - Baseline 'Clean' Nose (kg)": round(baseline_nose_mass, 4),
        "Penalty - Global Nose Thickening (kg)": round(mass_global_reinforcement, 4),
        "Penalty - Local Hole Doublers (kg)": round(mass_local_doubler, 4),
        "Penalty - Aluminum Rod (kg)": round(mass_rod, 4),
        "Savings - Removed Skin (kg)": round(-mass_removed_skin, 4),
        "NET TOTAL WEIGHT PENALTY (kg)": round(net_weight_penalty, 4),
        "Mass - New Total Nose Mass (kg)": round(new_total_nose_mass, 4),
        "Significance - Local (% increase to nose)": f"{round(percentage_increase_local, 1)} %",
        "Significance - Global (% increase to MTOW)": f"{round(percentage_increase_mtow, 2)} %"
    }

# ==========================================
# Execution & Output
# ==========================================
if __name__ == "__main__":
    print("--- Canard Port Structural Impact Analysis ---\n")
    results = analyze_canard_structural_impact()
    
    for metric, value in results.items():
        # Add visual separators for readability
        if "NET TOTAL" in metric or "Significance -" in metric:
            print("-" * 55)
        print(f"{metric:<45}: {value}")