import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import itertools


# ── Constraint calculations ────────────────────────────────────────────────────

def compute_angles(L1, L2, L3, x_cg, up_sweep_angle_rad, diameter_fuselage,
                   wing_height_from_centre_line, wing_span,
                   l_gear, x_mlg, Y_lg, x_nlg):
    """
    Compute all constraint angles for a given set of landing gear parameters.
    Returns a dict of angle values (in degrees) and pass/fail for each constraint.
    """
    sigma = up_sweep_angle_rad
    R = diameter_fuselage / 2
    theta_min = 15.0
    phi_min   =  7.0
    psi_max   = 55.0

    x_cone_start = L1 + L2
    x_tail_tip   = L1 + L2 + L3
    keel         = l_gear - R

    # Tail check points
    p1 = (x_cone_start, keel)
    p2 = (x_tail_tip,   keel + L3 * np.tan(sigma))

    # Scrape angles
    theta1 = np.degrees(np.arctan2(p1[1], p1[0] - x_mlg))
    theta2 = np.degrees(np.arctan2(p2[1], p2[0] - x_mlg))

    # Tip-back angle
    beta = np.degrees(np.arctan2(x_mlg - x_cg, l_gear))

    # Turnover angle
    d     = x_mlg - x_nlg
    alpha = np.arctan2(Y_lg, d)
    c     = (x_cg - x_nlg) * np.sin(alpha)
    psi   = np.degrees(np.arctan2(c, l_gear))

    # Wing tip angle
    vertical   = l_gear + wing_height_from_centre_line
    horizontal = (wing_span / 2) - Y_lg
    phi = np.degrees(np.arctan2(vertical, horizontal))

    theta_crit = max(theta1, theta2)

    results = {
        'theta1': theta1, 'theta2': theta2,
        'beta':   beta,   'psi':    psi,   'phi': phi,
        'pass_theta1':   theta1   >= theta_min,
        'pass_theta2':   theta2   >= theta_min,
        'pass_beta':     beta     >  theta_crit,
        'pass_psi':      psi      <= psi_max,
        'pass_phi':      phi      >= phi_min,
        'pass_keel':     l_gear   >  R,
        'pass_all':      all([theta1 >= theta_min, theta2 >= theta_min,
                              beta > theta_crit, psi <= psi_max, phi >= phi_min,
                              l_gear > R]),
    }
    return results


# ── 3D aircraft plot ───────────────────────────────────────────────────────────

def plot_aircraft_3d(ax, L1, L2, L3, x_cg, sigma, R, wing_h, wing_span,
                     l_gear, x_mlg, Y_lg, x_nlg, show_constraints=True):
    """Draw aircraft geometry and constraint lines on a 3D axis."""

    # Fuselage centreline
    ax.plot([0, L1+L2], [l_gear, l_gear], [0, 0], 'k-', lw=2, alpha=0.3)

    # Fuselage cylinder (drawn as a tube using circles)
    t = np.linspace(0, 2*np.pi, 32)
    for x in np.linspace(0, L1+L2, 12):
        ax.plot(x + 0*t, l_gear + R*np.cos(t), R*np.sin(t),
                color='steelblue', alpha=0.08, lw=0.5)
    # Fuselage rails
    for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
        ax.plot([0, L1+L2],
                [l_gear + R*np.cos(angle), l_gear + R*np.cos(angle)],
                [R*np.sin(angle), R*np.sin(angle)],
                color='steelblue', alpha=0.25, lw=0.8)

    # Tail cone
    x_cone = L1 + L2
    x_tip  = L1 + L2 + L3
    tip_R  = max(R - L3*np.tan(sigma), 0.01)
    keel   = l_gear - R
    tip_y_centre = keel + L3*np.tan(sigma) + tip_R
    for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
        ax.plot([x_cone, x_tip],
                [l_gear + R*np.cos(angle), tip_y_centre + tip_R*np.cos(angle)],
                [R*np.sin(angle),           tip_R*np.sin(angle)],
                color='gray', alpha=0.25, lw=0.8)

    # Wings
    wy = l_gear + wing_h
    for side in [-1, 1]:
        ax.plot([x_cg-0.45, x_cg+0.45, x_cg+0.45, x_cg-0.45, x_cg-0.45],
                [wy, wy, wy, wy, wy],
                [side*0.1, side*0.1, side*wing_span/2, side*wing_span/2, side*0.1],
                color='royalblue', lw=1.2, alpha=0.7)

    # Ground plane
    xx, zz = np.meshgrid([0, x_tip+0.5], [-wing_span/2-0.3, wing_span/2+0.3])
    ax.plot_surface(xx, np.zeros_like(xx)-0.01, zz,
                    alpha=0.12, color='green', linewidth=0)

    # MLG struts
    for side in [-1, 1]:
        ax.plot([x_mlg, x_mlg], [0, l_gear], [side*Y_lg, side*Y_lg],
                color='goldenrod', lw=2.5)
        # Wheel ring
        t2 = np.linspace(0, 2*np.pi, 24)
        ax.plot(x_mlg + 0.12*np.cos(t2), 0.12*np.sin(t2), side*Y_lg + 0*t2,
                color='goldenrod', lw=1.5)

    # NLG
    ax.plot([x_nlg, x_nlg], [0, l_gear], [0, 0], color='goldenrod', lw=2.0)
    t2 = np.linspace(0, 2*np.pi, 24)
    ax.plot(x_nlg + 0.10*np.cos(t2), 0.10*np.sin(t2), 0*t2,
            color='goldenrod', lw=1.5)

    # CG marker
    ax.scatter([x_cg], [l_gear], [0], color='red', s=60, zorder=5)

    if show_constraints:
        p1 = (x_cone,  keel)
        p2 = (x_tip,   keel + L3*np.tan(sigma))

        for side in [-1, 1]:
            # Scrape angles (orange/red)
            ax.plot([x_mlg, p1[0]], [0, p1[1]], [side*Y_lg, 0],
                    color='tomato', lw=1.2, ls='--', alpha=0.8)
            ax.plot([x_mlg, p2[0]], [0, p2[1]], [side*Y_lg, 0],
                    color='darkorange', lw=1.2, ls=':', alpha=0.8)
            # Tip-back beta (blue)
            ax.plot([x_mlg, x_cg], [0, l_gear], [side*Y_lg, 0],
                    color='dodgerblue', lw=1.2, ls='--', alpha=0.7)
            # Wing tip phi (green)
            ax.plot([x_mlg, x_cg], [0, wy], [side*Y_lg, side*wing_span/2],
                    color='mediumseagreen', lw=1.2, ls='--', alpha=0.7)

        # Turnover triangle on ground
        tri_x = [x_nlg, x_mlg, x_mlg, x_nlg]
        tri_z = [0,      Y_lg, -Y_lg,  0]
        ax.plot(tri_x, [0,0,0,0], tri_z,
                color='mediumpurple', lw=1.5, ls='--', alpha=0.8)
        # CG projected to ground
        ax.plot([x_cg, x_cg], [0, l_gear], [0, 0],
                color='mediumpurple', lw=0.8, ls=':', alpha=0.5)

    ax.set_xlabel('x (m)', fontsize=8)
    ax.set_ylabel('y / height (m)', fontsize=8)
    ax.set_zlabel('z / lateral (m)', fontsize=8)
    ax.tick_params(labelsize=7)


# ── Constraint summary bar ─────────────────────────────────────────────────────

def plot_constraint_summary(ax, results, title=''):
    """Bar chart showing each constraint angle vs its limit."""
    constraints = [
        ('θ₁ (scrape P1)', results['theta1'], 15,  '≥', 'tomato'),
        ('θ₂ (scrape P2)', results['theta2'], 15,  '≥', 'darkorange'),
        ('β  (tip-back)',  results['beta'],   max(results['theta1'], results['theta2']), '≥', 'dodgerblue'),
        ('ψ  (turnover)',  results['psi'],    55,  '≤', 'mediumpurple'),
        ('φ  (wing tip)',  results['phi'],    7,   '≥', 'mediumseagreen'),
    ]
    names   = [c[0] for c in constraints]
    vals    = [c[1] for c in constraints]
    limits  = [c[2] for c in constraints]
    dirs    = [c[3] for c in constraints]
    colours = [c[4] for c in constraints]

    passes = [
        v >= l if d == '≥' else v <= l
        for v, l, d in zip(vals, limits, dirs)
    ]

    bars = ax.barh(names, vals, color=[c if p else 'salmon' for c, p in zip(colours, passes)],
                   alpha=0.75, height=0.55)
    # Limit lines
    for i, (lim, d, p) in enumerate(zip(limits, dirs, passes)):
        ax.axvline(lim if i < 3 else lim, color='red' if not p else 'gray',
                   lw=0.8, ls='--', alpha=0.5)
        ax.plot(lim, i, marker='|', color='dimgray', markersize=10, lw=2)
        ax.text(lim + 0.5, i, f'{d}{lim:.1f}°', va='center', fontsize=7,
                color='dimgray')

    # Value labels
    for i, (v, p) in enumerate(zip(vals, passes)):
        ax.text(max(v - 1, 0.5), i, f'{v:.1f}°', va='center', ha='right',
                fontsize=8, color='white' if p else 'darkred', fontweight='bold')

    status = '✓ ALL PASS' if results['pass_all'] else '✗ VIOLATIONS'
    ax.set_title(f'{title}\n{status}',
                 fontsize=9,
                 color='darkgreen' if results['pass_all'] else 'crimson')
    ax.set_xlabel('Angle (°)', fontsize=8)
    ax.tick_params(labelsize=8)
    ax.set_xlim(0, max(vals + limits) * 1.25)
    ax.invert_yaxis()


# ── Main visualiser ────────────────────────────────────────────────────────────

def visualise_landing_gear(
    L1, L2, L3, x_cg, up_sweep_angle_rad, diameter_fuselage,
    wing_height_from_centre_line, wing_span,
    l_gear_values,
    x_mlg_values,
    Y_lg_values,
    x_nlg_values=None,
    show_3d=True,
):
    """
    Visualise constraint satisfaction for all combinations of the provided
    landing gear parameter lists.

    Parameters
    ----------
    L1, L2, L3, x_cg, up_sweep_angle_rad, diameter_fuselage,
    wing_height_from_centre_line, wing_span : floats — fixed aircraft parameters

    l_gear_values  : list of strut lengths to check [m]
    x_mlg_values   : list of MLG x-positions to check [m]
    Y_lg_values    : list of MLG lateral half-tracks to check [m]
    x_nlg_values   : list of NLG x-positions to check [m]
                     (if None, derived from 85/15 load split)
    show_3d        : bool — whether to include the 3D aircraft view
    """

    if x_nlg_values is None:
        x_nlg_values = [(x_cg - x * 0.85) / 0.15 for x in x_mlg_values]

    combos = list(itertools.product(l_gear_values, x_mlg_values,
                                    Y_lg_values, x_nlg_values))
    n = len(combos)
    print(f"Checking {n} combinations...")

    all_results = []
    for l_gear, x_mlg, Y_lg, x_nlg in combos:
        r = compute_angles(L1, L2, L3, x_cg, up_sweep_angle_rad,
                           diameter_fuselage, wing_height_from_centre_line,
                           wing_span, l_gear, x_mlg, Y_lg, x_nlg)
        r.update({'l_gear': l_gear, 'x_mlg': x_mlg,
                  'Y_lg': Y_lg, 'x_nlg': x_nlg})
        all_results.append(r)

    passing = [r for r in all_results if r['pass_all']]
    failing = [r for r in all_results if not r['pass_all']]
    print(f"  Passing: {len(passing)} / {n}")
    print(f"  Failing: {len(failing)} / {n}")

    # ── Figure layout ──────────────────────────────────────────────────────────
    # For a single combo: show 3D + summary side by side
    # For multiple combos: show a grid of summary bars + a pass/fail heatmap

    if n == 1:
        r = all_results[0]
        if show_3d:
            fig = plt.figure(figsize=(13, 5))
            ax3d = fig.add_subplot(121, projection='3d')
            ax_bar = fig.add_subplot(122)
        else:
            fig, ax_bar = plt.subplots(1, 1, figsize=(7, 4))
            ax3d = None

        if ax3d:
            plot_aircraft_3d(ax3d, L1, L2, L3, x_cg, up_sweep_angle_rad,
                             diameter_fuselage/2, wing_height_from_centre_line,
                             wing_span, r['l_gear'], r['x_mlg'], r['Y_lg'],
                             r['x_nlg'])
            ax3d.set_title(f"Aircraft geometry\nl={r['l_gear']:.2f}m  "
                           f"x_mlg={r['x_mlg']:.2f}m  Y={r['Y_lg']:.2f}m",
                           fontsize=9)

        title = (f"l={r['l_gear']:.2f}m  x_mlg={r['x_mlg']:.2f}m  "
                 f"Y_lg={r['Y_lg']:.2f}m  x_nlg={r['x_nlg']:.2f}m")
        plot_constraint_summary(ax_bar, r, title)
        fig.tight_layout()

    else:
        # ── Multiple combinations ──────────────────────────────────────────────
        # 1. Grid of bar charts (up to 12 shown, paginated by figure)
        max_per_fig = 9
        n_pages = int(np.ceil(n / max_per_fig))

        for page in range(n_pages):
            batch = all_results[page*max_per_fig : (page+1)*max_per_fig]
            nb = len(batch)
            ncols = min(3, nb)
            nrows = int(np.ceil(nb / ncols))
            fig, axes = plt.subplots(nrows, ncols,
                                     figsize=(5*ncols, 3.5*nrows))
            axes = np.array(axes).flatten()
            for i, r in enumerate(batch):
                title = (f"l={r['l_gear']:.2f}  x={r['x_mlg']:.2f}  "
                         f"Y={r['Y_lg']:.2f}  xn={r['x_nlg']:.2f}")
                plot_constraint_summary(axes[i], r, title)
            for j in range(nb, len(axes)):
                axes[j].set_visible(False)
            fig.suptitle(f'Constraint check — page {page+1}/{n_pages}',
                         fontsize=11, fontweight='bold')
            fig.tight_layout()

        # 2. Pass/fail heatmap over l_gear vs x_mlg (if multiple of each)
        if len(l_gear_values) > 1 and len(x_mlg_values) > 1:
            _plot_heatmap(all_results, l_gear_values, x_mlg_values,
                          Y_lg_values, x_nlg_values)

        # 3. Spider / radar chart comparing passing vs failing envelope
        if passing and failing:
            _plot_radar(passing, failing)

    plt.show()
    return all_results


# ── Heatmap: pass/fail over l_gear × x_mlg ────────────────────────────────────

def _plot_heatmap(all_results, l_gear_values, x_mlg_values,
                  Y_lg_values, x_nlg_values):
    """
    For each (l_gear, x_mlg) pair, count how many Y_lg/x_nlg combinations pass.
    Shows one heatmap per constraint angle as well as the overall pass map.
    """
    angle_keys   = ['theta1', 'theta2', 'beta', 'psi', 'phi']
    angle_labels = ['θ₁ scrape P1', 'θ₂ scrape P2', 'β tip-back',
                    'ψ turnover', 'φ wing tip']
    pass_keys    = ['pass_theta1','pass_theta2','pass_beta','pass_psi','pass_phi']

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()

    nL = len(l_gear_values)
    nX = len(x_mlg_values)

    for k, (pk, lbl) in enumerate(zip(pass_keys + ['pass_all'],
                                       angle_labels + ['ALL pass'])):
        grid = np.zeros((nL, nX))
        for i, lg in enumerate(l_gear_values):
            for j, xm in enumerate(x_mlg_values):
                subset = [r for r in all_results
                          if r['l_gear'] == lg and r['x_mlg'] == xm]
                if subset:
                    grid[i, j] = np.mean([r[pk] for r in subset])

        im = axes[k].imshow(grid, origin='lower', aspect='auto',
                             cmap='RdYlGn', vmin=0, vmax=1)
        axes[k].set_xticks(range(nX))
        axes[k].set_xticklabels([f'{v:.2f}' for v in x_mlg_values],
                                 fontsize=7, rotation=45, ha='right')
        axes[k].set_yticks(range(nL))
        axes[k].set_yticklabels([f'{v:.2f}' for v in l_gear_values], fontsize=7)
        axes[k].set_xlabel('x_mlg (m)', fontsize=8)
        axes[k].set_ylabel('l_gear (m)', fontsize=8)
        axes[k].set_title(lbl, fontsize=9)
        plt.colorbar(im, ax=axes[k], fraction=0.04,
                     label='Fraction passing')

    fig.suptitle('Pass fraction heatmap  (l_gear × x_mlg,  averaged over Y_lg / x_nlg)',
                 fontsize=11, fontweight='bold')
    fig.tight_layout()


# ── Radar chart comparing passing vs failing envelope ─────────────────────────

def _plot_radar(passing, failing):
    labels = ['θ₁/15°', 'θ₂/15°', 'β/θ_crit', 'ψ/55°', 'φ/7°']

    def normalise(r):
        theta_crit = max(r['theta1'], r['theta2'])
        return [
            r['theta1'] / 15,
            r['theta2'] / 15,
            r['beta']   / max(theta_crit, 1),
            r['psi']    / 55,
            r['phi']    / 7,
        ]

    N = len(labels)
    angles = [n / N * 2*np.pi for n in range(N)] + [0]

    fig, ax = plt.subplots(figsize=(6, 6),
                           subplot_kw=dict(polar=True))

    def draw_group(group, colour, label):
        vals_all = [normalise(r) for r in group]
        mean_v   = np.mean(vals_all, axis=0).tolist() + [np.mean(vals_all, axis=0)[0]]
        min_v    = np.min(vals_all,  axis=0).tolist() + [np.min(vals_all,  axis=0)[0]]
        max_v    = np.max(vals_all,  axis=0).tolist() + [np.max(vals_all,  axis=0)[0]]
        ax.plot(angles, mean_v, color=colour, lw=2,   label=label)
        ax.fill(angles, min_v,  color=colour, alpha=0.08)
        ax.fill(angles, max_v,  color=colour, alpha=0.08)

    if passing: draw_group(passing, 'mediumseagreen', f'Passing (n={len(passing)})')
    if failing: draw_group(failing, 'tomato',         f'Failing (n={len(failing)})')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticks([0.5, 1.0, 1.5])
    ax.set_yticklabels(['0.5×', '1× limit', '1.5×'], fontsize=7)
    ax.axhline(y=1.0, color='gray', lw=0.8, ls='--', alpha=0.6)
    ax.set_title('Constraint envelope\n(values normalised to limit = 1)',
                 fontsize=10, pad=15)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=9)
    fig.tight_layout()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':

    # ── Fixed aircraft parameters ──────────────────────────────────────────────
    AIRCRAFT = dict(
        L1=1.0,
        L2=2.5,
        L3=1.5,
        x_cg=3.0,
        up_sweep_angle_rad=17 * np.pi / 180,
        diameter_fuselage=1.25,
        wing_height_from_centre_line=-0.625,
        wing_span=6.0,
    )

    # ── Option A: single combination ──────────────────────────────────────────
    # Paste optimiser outputs here to check a single result visually.
    visualise_landing_gear(
        **AIRCRAFT,
        l_gear_values  = [1.5],
        x_mlg_values   = [3.4],
        Y_lg_values    = [0.7],
        x_nlg_values   = [0.5],
        show_3d=True,
    )

    # ── Option B: sweep over multiple values ──────────────────────────────────
    # Uncomment to scan a parameter space.
    #
    # visualise_landing_gear(
    #     **AIRCRAFT,
    #     l_gear_values = np.linspace(1.2, 2.0, 5).tolist(),
    #     x_mlg_values  = np.linspace(3.0, 3.8, 5).tolist(),
    #     Y_lg_values   = [0.65, 0.75],
    #     x_nlg_values  = [0.4, 0.5, 0.6],
    #     show_3d=False,
    # )