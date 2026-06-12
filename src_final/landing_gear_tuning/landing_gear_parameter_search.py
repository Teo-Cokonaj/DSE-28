import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from landing_gear_tuning import landing_gear_response


def plot_parameter_space(c_min: float = 1e-3,
                         c_max: float = 5000.0,
                         k_min: float = 1e-3,
                         k_max: float = 500000.0,
                         n_points: int = 60,
                         downward_landing_speed: float = 3.5,
                         displacement_constraint_compression: float = 0.0095,
                         force_requirement: float = 2.67,
                         dt: float = 0.01,
                         t: int = 5,
                         m: float = 50,
                         L: float = 490,
                         log_scale: bool = True,
                         save_path: str = None):
    """
    Sweeps k and c over a grid and plots which constraints are satisfied.

    Constraint categories (encoded as integer):
        0 — Neither displacement nor force constraint met
        1 — Only displacement constraint met
        2 — Only force constraint met
        3 — Both constraints met  (underdamped system, 4mk > c²)
        -1 — Overdamped / invalid (skipped, shown as grey)

    Parameters mirror those in landing_gear_response so they can be wired
    directly to the parent aircraft constructor class.
    """

    g = 9.80665
    max_allowable_force = force_requirement * g * m  # [N]

    if log_scale:
        c_values = np.logspace(np.log10(c_min), np.log10(c_max), n_points)
        k_values = np.logspace(np.log10(k_min), np.log10(k_max), n_points)
    else:
        c_values = np.linspace(c_min, c_max, n_points)
        k_values = np.linspace(k_min, k_max, n_points)

    # Result grid: rows = k index, cols = c index
    result_grid = np.full((n_points, n_points), -1, dtype=int)

    peak_disp_grid = np.full((n_points, n_points), np.nan)
    peak_force_grid = np.full((n_points, n_points), np.nan)
    damping_ratio_grid = np.full((n_points, n_points), np.nan)

    total = n_points * n_points
    count = 0

    for ki, k in enumerate(k_values):
        for ci, c in enumerate(c_values):
            count += 1
            if count % 500 == 0:
                print(f"  Progress: {count}/{total} ({100*count/total:.0f}%)")

            # Skip overdamped: constraint c² > 4mk → system won't oscillate
            # (still valid physically, but often outside design intent)
            # Keep as -1 (grey) when overdamped
            if c ** 2 >= 4 * m * k:
                continue

            try:
                y_disp, y_force, _ = landing_gear_response(
                    k=k,
                    c=c,
                    downward_landing_speed=downward_landing_speed,
                    displacement_constraint_compression=displacement_constraint_compression,
                    force_requirement=force_requirement,
                    dt=dt,
                    t=t,
                    m=m,
                    L=L,
                )
            except Exception:
                continue

            peak_disp = np.max(np.abs(y_disp))   # [m]
            peak_force = np.max(np.abs(y_force))  # [N]

            peak_disp_grid[ki, ci] = peak_disp
            peak_force_grid[ki, ci] = peak_force
            damping_ratio_grid[ki, ci] = c / (2 * np.sqrt(m * k))  # ζ = c / (2√(mk))

            disp_ok = peak_disp < displacement_constraint_compression
            force_ok = peak_force < max_allowable_force

            if disp_ok and force_ok:
                result_grid[ki, ci] = 3
            elif disp_ok:
                result_grid[ki, ci] = 1
            elif force_ok:
                result_grid[ki, ci] = 2
            else:
                result_grid[ki, ci] = 0

    # ------------------------------------------------------------------ #
    #  Plot 1 — Constraint satisfaction map                               #
    # ------------------------------------------------------------------ #

    fig, axes = plt.subplots(1, 4, figsize=(24, 6))
    fig.patch.set_facecolor('#0f1117')
    for ax in axes:
        ax.set_facecolor('#1a1d27')

    C_grid, K_grid = np.meshgrid(c_values, k_values)

    # Colour map: -1=grey, 0=red, 1=orange, 2=yellow, 3=green
    cmap = ListedColormap(['#3a3a4a', '#e05252', '#f0a050', '#f5e642', '#52c97a'])
    bounds_cmap = [-1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

    norm = mcolors.BoundaryNorm(bounds_cmap, cmap.N)

    ax = axes[0]
    mesh = ax.pcolormesh(C_grid, K_grid, result_grid,
                         cmap=cmap, norm=norm,
                         shading='auto')

    if log_scale:
        ax.set_xscale('log')
        ax.set_yscale('log')

    ax.set_xlabel('Damping coefficient  c  [Pa·s/m]', color='#c8ccd8', fontsize=10)
    ax.set_ylabel('Spring stiffness  k  [N/m]', color='#c8ccd8', fontsize=10)
    ax.set_title('Constraint Satisfaction Map', color='white', fontsize=12, fontweight='bold')
    ax.tick_params(colors='#c8ccd8')
    for spine in ax.spines.values():
        spine.set_edgecolor('#3a3d50')

    legend_patches = [
        mpatches.Patch(color='#52c97a', label='Both met'),
        mpatches.Patch(color='#f0a050', label='Displacement only'),
        mpatches.Patch(color='#f5e642', label='Force only'),
        mpatches.Patch(color='#e05252', label='Neither met'),
        mpatches.Patch(color='#3a3a4a', label='Overdamped'),
    ]
    ax.legend(handles=legend_patches, loc='upper left',
              facecolor='#1a1d27', edgecolor='#3a3d50',
              labelcolor='white', fontsize=8)

    # ------------------------------------------------------------------ #
    #  Plot 2 — Peak displacement heat-map                                #
    # ------------------------------------------------------------------ #

    ax2 = axes[1]
    disp_cm = peak_disp_grid * 100  # convert to cm for readability
    masked_disp = np.ma.masked_invalid(disp_cm)

    im2 = ax2.pcolormesh(C_grid, K_grid, masked_disp,
                          cmap='plasma', shading='auto')
    cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
    cbar2.set_label('Peak displacement [cm]', color='#c8ccd8', fontsize=9)
    cbar2.ax.yaxis.set_tick_params(color='#c8ccd8')
    plt.setp(cbar2.ax.yaxis.get_ticklabels(), color='#c8ccd8')

    # Overlay the constraint boundary as a contour
    try:
        ax2.contour(C_grid, K_grid, masked_disp,
                    levels=[displacement_constraint_compression * 100],
                    colors='white', linewidths=1.5, linestyles='--')
    except Exception:
        pass

    if log_scale:
        ax2.set_xscale('log')
        ax2.set_yscale('log')

    ax2.set_xlabel('Damping coefficient  c  [Pa·s/m]', color='#c8ccd8', fontsize=10)
    ax2.set_ylabel('Spring stiffness  k  [N/m]', color='#c8ccd8', fontsize=10)
    ax2.set_title(f'Peak Displacement  (– – limit: {displacement_constraint_compression*100:.2f} cm)',
                  color='white', fontsize=12, fontweight='bold')
    ax2.tick_params(colors='#c8ccd8')
    for spine in ax2.spines.values():
        spine.set_edgecolor('#3a3d50')

    # ------------------------------------------------------------------ #
    #  Plot 3 — Peak force heat-map                                       #
    # ------------------------------------------------------------------ #

    ax3 = axes[2]
    force_kN = peak_force_grid / 1000
    limit_kN = max_allowable_force / 1000
    masked_force = np.ma.masked_invalid(force_kN)

    im3 = ax3.pcolormesh(C_grid, K_grid, masked_force,
                          cmap='inferno', shading='auto')
    cbar3 = plt.colorbar(im3, ax=ax3, pad=0.02)
    cbar3.set_label('Peak force [kN]', color='#c8ccd8', fontsize=9)
    cbar3.ax.yaxis.set_tick_params(color='#c8ccd8')
    plt.setp(cbar3.ax.yaxis.get_ticklabels(), color='#c8ccd8')

    try:
        ax3.contour(C_grid, K_grid, masked_force,
                    levels=[limit_kN],
                    colors='white', linewidths=1.5, linestyles='--')
    except Exception:
        pass

    if log_scale:
        ax3.set_xscale('log')
        ax3.set_yscale('log')

    ax3.set_xlabel('Damping coefficient  c  [Pa·s/m]', color='#c8ccd8', fontsize=10)
    ax3.set_ylabel('Spring stiffness  k  [N/m]', color='#c8ccd8', fontsize=10)
    ax3.set_title(f'Peak Force  (– – limit: {limit_kN:.2f} kN  /  {force_requirement}g)',
                  color='white', fontsize=12, fontweight='bold')
    ax3.tick_params(colors='#c8ccd8')
    for spine in ax3.spines.values():
        spine.set_edgecolor('#3a3d50')

    # ------------------------------------------------------------------ #
    #  Plot 4 — Damping ratio heat-map                                    #
    # ------------------------------------------------------------------ #

    ax4 = axes[3]
    masked_zeta = np.ma.masked_invalid(damping_ratio_grid)

    im4 = ax4.pcolormesh(C_grid, K_grid, masked_zeta,
                          cmap='coolwarm', shading='auto', vmin=0, vmax=1)
    cbar4 = plt.colorbar(im4, ax=ax4, pad=0.02)
    cbar4.set_label('Damping ratio  ζ  [-]', color='#c8ccd8', fontsize=9)
    cbar4.ax.yaxis.set_tick_params(color='#c8ccd8')
    plt.setp(cbar4.ax.yaxis.get_ticklabels(), color='#c8ccd8')

    # ζ = 1 contour marks critical damping boundary
    try:
        ax4.contour(C_grid, K_grid, masked_zeta,
                    levels=[1.0],
                    colors='white', linewidths=1.5, linestyles='--')
    except Exception:
        pass

    # ζ = 0.5 contour as a useful secondary reference
    try:
        cs = ax4.contour(C_grid, K_grid, masked_zeta,
                         levels=[0.5],
                         colors='#aaaaaa', linewidths=1.0, linestyles=':')
        ax4.clabel(cs, fmt='ζ=0.5', colors='#aaaaaa', fontsize=7)
    except Exception:
        pass

    if log_scale:
        ax4.set_xscale('log')
        ax4.set_yscale('log')

    ax4.set_xlabel('Damping coefficient  c  [Pa·s/m]', color='#c8ccd8', fontsize=10)
    ax4.set_ylabel('Spring stiffness  k  [N/m]', color='#c8ccd8', fontsize=10)
    ax4.set_title('Damping Ratio  ζ  (– – ζ=1 critical)',
                  color='white', fontsize=12, fontweight='bold')
    ax4.tick_params(colors='#c8ccd8')
    for spine in ax4.spines.values():
        spine.set_edgecolor('#3a3d50')

    # ------------------------------------------------------------------ #

    fig.suptitle('Landing Gear Parameter Space  ·  c vs k sweep',
                 color='white', fontsize=14, fontweight='bold', y=1.01)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved to {save_path}")

    plt.show()

    return result_grid, peak_disp_grid, peak_force_grid, damping_ratio_grid, c_values, k_values

# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    result_grid, peak_disp_grid, peak_force_grid, damping_ratio_grid, c_vals, k_vals = plot_parameter_space(
        c_min=10,
        c_max=5000,
        k_min=1000,
        k_max=500000,
        n_points=60,            # increase for higher resolution (slower)
        downward_landing_speed=2,
        displacement_constraint_compression=0.0775,
        force_requirement=4,
        dt=0.01,
        t=5,
        m=25,
        L=25*9.81,
        log_scale=True,
        save_path="landing_gear_parameter_space.png",
    )

    n_both = np.sum(result_grid == 3)
    n_total_valid = np.sum(result_grid >= 0)
    print(f"\nFeasible region: {n_both}/{n_total_valid} underdamped points satisfy both constraints "
          f"({100*n_both/max(n_total_valid,1):.1f}%)")
    
    """
    # Create a header row using the c_values (rounded for readability)
    header_string = ",".join([f"c={c:.2f}" for c in c_vals])

    # Save the result grid with the k_values as the first index column
    # Combining k values and the data grid side-by-side
    csv_data = np.hstack((k_vals.reshape(-1, 1), result_grid))

    # Save to file
    np.savetxt("landing_gear_mesh_results.csv", 
            csv_data, 
            delimiter=",", 
            header="k_value/c_value," + header_string, 
            comments="")

    print("\n📊 Full 60x60 matrix successfully exported to 'landing_gear_mesh_results.csv'!")

    """