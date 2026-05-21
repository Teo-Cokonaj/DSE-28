import math

#Evaluate the total structural weight penalty and of adding a transverse canard port to a drone fuselage.
def analyze_canard_structural_impact(mtow, W, canard_lift_fraction, cg_location, tip_to_canard_distance, fuselage_diameter, minimum_thickness, skin_density, skin_yield_strength, bearing_strength, rod_outer_diameter, rod_density, reinforcement_diameter, thickness_multiplier, oem_fraction, rod_wall_thickness, canard_z_location):
    
    distance_to_canard = cg_location - tip_to_canard_distance # Distance from CG to canard port [m]
    
    # Aerodynamic Loads & Bending Moment
    
    total_lift = W # Total lift in Newtons
    canard_lift = total_lift * canard_lift_fraction # Force on the canard in Newtons
    max_bending_moment = canard_lift * distance_to_canard # Bending moment at the canard in Nm
    radius = fuselage_diameter / 2.0 # Radius of the fuselage in meters
    

    # No Port Front-half Fuselage Mass
       
    baseline_fronthalf_volume = 2 * math.pi * radius * minimum_thickness * distance_to_canard
    baseline_fronthalf_mass = baseline_fronthalf_volume * skin_density
   
    # Skin Thickness Sizing (Bending vs. Minimum Thickness)
    
    bending_thickness = (max_bending_moment) / (math.pi * (radius**2) * skin_yield_strength) # Thickness required to resist bending loads with safety factor
    required_thickness = max(bending_thickness, minimum_thickness) # Final required thickness is the maximum between bending load thickness and manufacturing minimum
    design_driven_by = "Bending Loads" if bending_thickness > minimum_thickness else "Minimum Thickness"
     
    # Global Weight Penalty (Thickening the front half of the fuselage)
    
    delta_thickness = required_thickness - minimum_thickness # If the required thickness is greater than the minimum, this is the additional thickness added
    volume_fronthalf_reinforcement = 2 * math.pi * radius * delta_thickness * distance_to_canard # Volume of the front half reinforcement
    mass_fronthalf_reinforcement = volume_fronthalf_reinforcement * skin_density # Mass of the front half reinforcement
    

    

    # Ring Reinforcement Weight Penalty

    bearing_thickness = canard_lift / (rod_outer_diameter * 2 * bearing_strength)
    required_thickness = max(bearing_thickness, minimum_thickness)
    if required_thickness == minimum_thickness:
        mass_ring = 0
    else:
        ring_volume = rod_outer_diameter * required_thickness * (radius*2*(math.asin(canard_z_location/radius)-math.pi/2))
        mass_ring = ring_volume * skin_density


    # Hole Reinforcement Weight Penalty
    cutout_area = math.pi * (rod_outer_diameter / 2)**2
    mass_removed_skin = 2 * cutout_area * required_thickness * skin_density # Mass of the skin removed for the cutout (both sides of the fuselage)
    mass_local_reinforcement = (math.pi*((rod_outer_diameter * reinforcement_diameter)/2)**2 - math.pi*(rod_outer_diameter/2)**2) * (required_thickness * (thickness_multiplier-1)) * skin_density #  Week 5-2 of SAD lecture slides page 18. 
    


    # Mass of canard port hollow rod

    rod_inner_diameter = rod_outer_diameter - (2 * rod_wall_thickness) 
    rod_cross_section = math.pi * ((rod_outer_diameter / 2)**2 - (rod_inner_diameter / 2)**2)
    mass_rod = rod_cross_section * fuselage_diameter * rod_density
    

    # Final Mass Penalty Calculation
    oem = mtow * oem_fraction
    print(oem)
    net_weight_penalty = mass_fronthalf_reinforcement + mass_ring + mass_local_reinforcement + mass_rod - mass_removed_skin
    new_oem = oem + net_weight_penalty
    print(new_oem)
    oem_fraction = new_oem / mtow
    print(f"Net Weight Penalty: {net_weight_penalty:.2f} = {mass_fronthalf_reinforcement:.2f} + {mass_ring:.2f} + {mass_local_reinforcement:.2f} + {mass_rod:.2f} - {mass_removed_skin:.2f}")
    return oem_fraction