import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- stub for testing without the real module ---
try:
    from landing_gear_tuning import landing_gear_response
except ImportError:
    def landing_gear_response(k, c, downward_landing_speed=3,
                              displacement_constraint_compression=0.0775,
                              dt=0.01, t=5, m=50, **kwargs):
        import control.matlab as ml
        g = 9.80665
        L = m * g
        A = [[0, 1], [-k/m, -c/m]]
        B = [0, 1]
        C = [[1, 0], [k, c]]
        D = [[0], [0]]
        state_space = ml.ss(A, B, C, D)
        max_load = g - L/m
        t_arr = np.arange(0, t + dt, dt)
        inp = max_load * np.ones_like(t_arr)
        y, T, x = ml.lsim(state_space, inp, T=t_arr, X0=[0, downward_landing_speed])
        y_displacement = y[:, 0]
        y_force = y[:, 1]
        peak_force = np.max(np.abs(y_force))
        total_gs = peak_force * 1.5 / (m * g)
        disp_ok = np.max(np.abs(y_displacement)) < displacement_constraint_compression
        constraint_status = 1 if disp_ok else 0
        return y_displacement, y_force, constraint_status, peak_force, total_gs


def _add_contours(ax, C_grid, K_grid, data_grid, levels, color, linestyle, fmt, fontsize=10, log_scale=True):
    """Helper to add labelled contour lines, silently skipping if data is too sparse."""
    masked = np.ma.masked_invalid(data_grid)
    try:
        cs = ax.contour(C_grid, K_grid, masked, levels=levels,
                        colors=color, linewidths=0.9, linestyles=linestyle)
        labels = ax.clabel(cs, fmt=fmt, colors=color, fontsize=fontsize, inline=False)

        for txt in labels:
            txt.set_bbox(dict(facecolor=ax.get_facecolor(),
                            edgecolor='none',
                            pad=0.4))
    except Exception:
        pass


def plot_parameter_space(c_min: float = 1e-3,
                         c_max: float = 5000.0,
                         k_min: float = 1e-3,
                         k_max: float = 500000.0,
                         n_points: int = 60,
                         downward_landing_speed: float = 3,
                         displacement_constraint_compression: float = 0.0775,
                         dt: float = 0.01,
                         t: int = 5,
                         m: float = 50,
                         log_scale: bool = True,
                         save_path: str = None,
                         g_contour_step: float = 0.5,
                         disp_contour_step_cm: float = 1.0):
    """
    Sweeps k and c over a grid and plots which constraints are satisfied.

    Plots (4 panels):
        1 — Peak displacement heat-map
        2 — Peak force heat-map
        3 — Damping ratio heat-map
        4 — Constraint satisfaction map

    Every panel carries:
        · Grey dashed contour lines for g-load  (step = g_contour_step)
        · Grey dotted contour lines for peak displacement in cm (step = disp_contour_step_cm)
    """

    if log_scale:
        c_values = np.logspace(np.log10(c_min), np.log10(c_max), n_points)
        k_values = np.logspace(np.log10(k_min), np.log10(k_max), n_points)
    else:
        c_values = np.linspace(c_min, c_max, n_points)
        k_values = np.linspace(k_min, k_max, n_points)

    result_grid        = np.full((n_points, n_points), -1, dtype=int)
    peak_disp_grid     = np.full((n_points, n_points), np.nan)
    peak_force_grid    = np.full((n_points, n_points), np.nan)
    damping_ratio_grid = np.full((n_points, n_points), np.nan)
    total_gs_grid      = np.full((n_points, n_points), np.nan)

    total = n_points * n_points
    count = 0

    for ki, k in enumerate(k_values):
        for ci, c in enumerate(c_values):
            count += 1
            if count % 500 == 0:
                print(f"  Progress: {count}/{total} ({100*count/total:.0f}%)")

            if c ** 2 >= 4 * m * k:
                continue

            try:
                y_disp, y_force, _, design_force, total_gs = landing_gear_response(
                    k=k, c=c,
                    downward_landing_speed=downward_landing_speed,
                    displacement_constraint_compression=displacement_constraint_compression,
                    dt=dt, t=t, m=m,
                )
            except Exception:
                continue

            peak_disp  = np.max(np.abs(y_disp))
            peak_force = np.max(np.abs(y_force))

            peak_disp_grid[ki, ci]     = peak_disp
            peak_force_grid[ki, ci]    = peak_force
            damping_ratio_grid[ki, ci] = c / (2 * np.sqrt(m * k))
            total_gs_grid[ki, ci]      = total_gs

            result_grid[ki, ci] = 1 if peak_disp < displacement_constraint_compression else 0

    # ------------------------------------------------------------------ #
    #  Contour level arrays                                               #
    # ------------------------------------------------------------------ #

    g_max   = np.nanmax(total_gs_grid)
    g_min   = np.nanmin(total_gs_grid)
    g_start = np.ceil(g_min / g_contour_step) * g_contour_step
    g_levels = np.arange(g_start, g_max + g_contour_step, g_contour_step)

    disp_cm_grid = peak_disp_grid * 100
    d_max   = np.nanmax(disp_cm_grid)
    d_min   = np.nanmin(disp_cm_grid)
    d_start = np.ceil(d_min / disp_contour_step_cm) * disp_contour_step_cm
    disp_levels = np.arange(d_start, d_max + disp_contour_step_cm, disp_contour_step_cm)

    G_COLOR    = '#fffffe'   # grey dashed  → g-load
    D_COLOR    = '#99ddff'   # light-blue dotted → displacement
    G_STYLE    = '--'
    D_STYLE    = ':'

    # ------------------------------------------------------------------ #
    #  Plot setup  — 4 panels                                             #
    # ------------------------------------------------------------------ #

    fig, axes = plt.subplots(1, 1, figsize=(8, 8))
    axes.set_facecolor('#1a1d27')

    fig.patch.set_facecolor('#0f1117')
    # axflat = axes.flatten()
    # for ax in axflat:
    #     ax.set_facecolor('#1a1d27')

    C_grid, K_grid = np.meshgrid(c_values, k_values)

    def _style_ax(ax, xlabel=True):
        if log_scale:
            ax.set_xscale('log')
            ax.set_yscale('log')
        if xlabel:
            ax.set_xlabel('Damping coefficient  c  [Pa·s/m]', color='#c8ccd8', fontsize=10)
        ax.set_ylabel('Spring stiffness  k  [N/m]', color='#c8ccd8', fontsize=10)
        ax.tick_params(colors='#c8ccd8')
        for spine in ax.spines.values():
            spine.set_edgecolor('#3a3d50')

    def _overlay_contours(ax):
        """Add g and displacement contours to any axis."""
        _add_contours(ax, C_grid, K_grid, total_gs_grid,
                      g_levels, G_COLOR, G_STYLE, fmt='%.0fg')
        # _add_contours(ax, C_grid, K_grid, disp_cm_grid,
        #               disp_levels, D_COLOR, D_STYLE, fmt='%.1fcm')

    # # ------------------------------------------------------------------ #
    # #  Plot 1 — Peak displacement heat-map                                #
    # # ------------------------------------------------------------------ #

    # ax1 = axflat[0]
    # masked_disp = np.ma.masked_invalid(disp_cm_grid)

    # im1 = ax1.pcolormesh(C_grid, K_grid, masked_disp, cmap='plasma', shading='auto')
    # cbar1 = plt.colorbar(im1, ax=ax1, pad=0.02)
    # cbar1.set_label('Peak displacement [cm]', color='#c8ccd8', fontsize=9)
    # cbar1.ax.yaxis.set_tick_params(color='#c8ccd8')
    # plt.setp(cbar1.ax.yaxis.get_ticklabels(), color='#c8ccd8')

    # # Displacement limit boundary
    # try:
    #     ax1.contour(C_grid, K_grid, masked_disp,
    #                 levels=[displacement_constraint_compression * 100],
    #                 colors='white', linewidths=1.5, linestyles='--')
    # except Exception:
    #     pass

    # _overlay_contours(ax1)
    # _style_ax(ax1)
    # ax1.set_title(f'Peak Displacement  (– – limit: {displacement_constraint_compression*100:.2f} cm)',
    #               color='white', fontsize=11, fontweight='bold')

    # # ------------------------------------------------------------------ #
    # #  Plot 2 — Peak force heat-map                                       #
    # # ------------------------------------------------------------------ #

    # ax2 = axflat[1]
    # force_kN = peak_force_grid / 1000
    # masked_force = np.ma.masked_invalid(force_kN)

    # im2 = ax2.pcolormesh(C_grid, K_grid, masked_force, cmap='inferno', shading='auto')
    # cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
    # cbar2.set_label('Peak force [kN]', color='#c8ccd8', fontsize=9)
    # cbar2.ax.yaxis.set_tick_params(color='#c8ccd8')
    # plt.setp(cbar2.ax.yaxis.get_ticklabels(), color='#c8ccd8')

    # _overlay_contours(ax2)
    # _style_ax(ax2)
    # ax2.set_title('Peak Force [kN]', color='white', fontsize=11, fontweight='bold')

    # # ------------------------------------------------------------------ #
    # #  Plot 3 — Damping ratio heat-map                                    #
    # # ------------------------------------------------------------------ #

    # ax3 = axflat[2]
    # masked_zeta = np.ma.masked_invalid(damping_ratio_grid)

    # im3 = ax3.pcolormesh(C_grid, K_grid, masked_zeta,
    #                       cmap='coolwarm', shading='auto', vmin=0, vmax=1)
    # cbar3 = plt.colorbar(im3, ax=ax3, pad=0.02)
    # cbar3.set_label('Damping ratio  ζ  [-]', color='#c8ccd8', fontsize=9)
    # cbar3.ax.yaxis.set_tick_params(color='#c8ccd8')
    # plt.setp(cbar3.ax.yaxis.get_ticklabels(), color='#c8ccd8')

    # # ζ = 1 and ζ = 0.5 reference contours
    # try:
    #     ax3.contour(C_grid, K_grid, masked_zeta,
    #                 levels=[1.0], colors='white', linewidths=1.5, linestyles='--')
    # except Exception:
    #     pass
    # try:
    #     cs05 = ax3.contour(C_grid, K_grid, masked_zeta,
    #                        levels=[0.5], colors='#aaaaaa', linewidths=1.0, linestyles=':')
    #     ax3.clabel(cs05, fmt='ζ=0.5', colors='#aaaaaa', fontsize=7)
    # except Exception:
    #     pass

    # _overlay_contours(ax3)
    # _style_ax(ax3)
    # ax3.set_title('Damping Ratio  ζ  (– – ζ=1 critical)',
    #               color='white', fontsize=11, fontweight='bold')

    # ------------------------------------------------------------------ #
    #  Plot 4 — Constraint satisfaction map                               #
    # ------------------------------------------------------------------ #

    cmap_cat = ListedColormap(['#3a3a4a', '#e05252', '#52c97a'])
    norm_cat  = mcolors.BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap_cat.N)

    ax4 = axes
    ax4.pcolormesh(C_grid, K_grid, result_grid,
                   cmap=cmap_cat, norm=norm_cat, shading='auto')

    _overlay_contours(ax4)
    _style_ax(ax4)
    #ax4.set_title('Constraint Satisfaction Map', color='white', fontsize=11, fontweight='bold')

    legend_patches = [
        mpatches.Patch(color='#52c97a', label='Displacement met'),
        mpatches.Patch(color='#e05252', label='Displacement not met'),
        mpatches.Patch(color='#3a3a4a', label='Overdamped'),
    ]
    ax4.legend(handles=legend_patches, loc='lower right',
               facecolor='#1a1d27', edgecolor='#3a3d50',
               labelcolor='white', fontsize=10)

    # ------------------------------------------------------------------ #
    #  Shared legend for overlay contours (bottom of figure)             #
    # ------------------------------------------------------------------ #

    contour_legend = [
        mpatches.Patch(color=G_COLOR, label=f'g-load contours (step {g_contour_step} g)'),
        mpatches.Patch(color=D_COLOR, label=f'Displacement contours (step {disp_contour_step_cm} cm)'),
    ]
    fig.legend(handles=contour_legend, loc='lower center', ncol=2,
               facecolor='#1a1d27', edgecolor='#3a3d50',
               labelcolor='white', fontsize=9, bbox_to_anchor=(0.5, -0.04))

    # fig.suptitle('Landing Gear Parameter Space  ·  c vs k sweep',
    #              color='white', fontsize=14, fontweight='bold', y=1.01)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved to {save_path}")

    plt.show()

    return result_grid, peak_disp_grid, peak_force_grid, damping_ratio_grid, total_gs_grid, c_values, k_values


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    result_grid, peak_disp_grid, peak_force_grid, damping_ratio_grid, total_gs_grid, c_vals, k_vals = plot_parameter_space(
        c_min=10,
        c_max=5000,
        k_min=1000,
        k_max=500000,
        n_points=100,
        downward_landing_speed=3,
        displacement_constraint_compression=0.0775,
        dt=0.01,
        t=5,
        m=50,
        log_scale=True,
        save_path="landing_gear_parameter_space.png",
        g_contour_step=3,
        disp_contour_step_cm=1.0,
    )

    n_both = np.sum(result_grid == 1)
    n_total_valid = np.sum(result_grid >= 0)
    print(f"\nFeasible region: {n_both}/{n_total_valid} underdamped points satisfy displacement constraint "
          f"({100*n_both/max(n_total_valid,1):.1f}%)")