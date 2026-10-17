"""Render closed-study summaries from committed JSON only; no fitting or simulation.

Run: python -m scripts.plot_result_summaries
Figures follow scripts/figure_style.py: the canvas carries data only, and every
word about it is in the <stem>.caption.md written beside the image and repeated
under the image in README.md and docs/results.md. The CSV views and tables keep
their values.
"""
from pathlib import Path
import csv
import hashlib
import json

import matplotlib
import numpy as np

from scripts import figure_style as style
import matplotlib.pyplot as plt  # noqa: E402  (after figure_style selects the Agg backend)
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/sim/summary'
INPUTS = [f'data/sim/phaseD/{name}.json' for name in
          ('matched_clock_audit', 'study3_results', 'study4_results')]
STYLE_REFERENCE = 'https://github.com/500ft/evidence-sufficiency-benchmark/pull/26'
# Policy key -> marker; the shape names the policy wherever it appears.
POLICY_MARKERS = {'fixed': 'o', 'clock_2700': '^', 'clock_2400': 's', 'trigger': 'D', 'always': 'X'}
POLICY_SHAPES = {'o': 'circle', '^': 'triangle', 's': 'square', 'D': 'diamond', 'X': 'cross'}


def load():
    return [json.loads((ROOT / p).read_text()) for p in INPUTS]


def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def replace_table(path, table):
    start, end = '<!-- policy-summary:start -->', '<!-- policy-summary:end -->'
    text = path.read_text()
    before, tail = text.split(start)
    _, after = tail.split(end)
    path.write_text(before + start + '\n' + table + '\n' + end + after)


def policies(audit, study):
    # Keep the audited policies together, and retain original context policies.
    rows = []
    for key, label in [('fixed', 'Initial calibration only'),
                       ('clock_2700', f"Clock: {audit['period_star_reported']:,.0f} cycles (train-selected)"),
                       ('clock_2400', f"Clock: {audit['clock_periods_matching_trigger_schedule_on_all_actuators'][0]:,.0f} cycles (matched cost)"),
                       ('trigger', f"P-V trigger: τ = {audit['tau_star']:.2f}"),
                       ('always', 'Calibration at every stage')]:
        if key in audit['heldout']:
            val = audit['heldout'][key]
            error, count = val['error_mm'], val['recalibrations']
        else:
            val = study['policies_on_heldout'][key]
            error, count = val['mean_pose_rmse_mm'], val['recal_per_actuator']
        rows.append(dict(policy=key, label=label, mean_pose_rmse_mm=error,
                         recalibrations_per_actuator=count))
    return rows


def tick(label):
    """cmr10 has no Greek glyphs; the tick label writes tau in mathtext."""
    return label.replace('τ', r'$\tau$')


def policy_caption(rows, audit, study):
    by = {r['policy']: r for r in rows}
    tie = by['clock_2400']
    assert (tie['mean_pose_rmse_mm'], tie['recalibrations_per_actuator']) == \
        (by['trigger']['mean_pose_rmse_mm'], by['trigger']['recalibrations_per_actuator'])
    names = {'fixed': 'initial calibration only',
             'clock_2700': f"the train-selected clock at {audit['period_star_reported']:,.0f} cycles",
             'clock_2400': f"the matched-cost clock at {audit['clock_periods_matching_trigger_schedule_on_all_actuators'][0]:,.0f} cycles",
             'trigger': f"the P-V trigger at τ = {audit['tau_star']:.2f}",
             'always': 'calibration at every stage'}
    shapes = ', '.join(f"{names[r['policy']]} ({POLICY_SHAPES[POLICY_MARKERS[r['policy']]]})" for r in rows)
    over = [names[r['policy']] for r in rows if r['mean_pose_rmse_mm'] > audit['budget_mm']]
    return (
        f"Saved simulation point summaries for {len(study['test_actuators'])} held-out actuators; "
        "no uncertainty bars. Panel (a) shows mean pose RMSE [mm] and panel (b) calibrations per "
        f"actuator for five policies, marked by shape: {shapes}. Left is better in both panels. "
        "The dashed line in (a) is the train-derived error budget, "
        f"{audit['budget_mm']:.3f} mm. A filled marker means the policy is within the budget; a hollow "
        f"marker means it exceeds it: {' and '.join(over)}. At matched cost the "
        f"clock ties the P-V trigger: both reach {tie['mean_pose_rmse_mm']:.3f} mm with "
        f"{tie['recalibrations_per_actuator']:.1f} calibrations per actuator. Counts include the initial "
        "calibration; error averages life stages, then actuators. Values: the policy table and "
        "policy_comparison.csv. Sources: matched_clock_audit.json and study3_results.json; no physical "
        "measurements.")


def policy_figure(rows, audit):
    style.apply()
    fig, axes = plt.subplots(1, 2, figsize=(style.FULL, 2.4), sharey=True,
                             gridspec_kw={'width_ratios': [1.5, 1]})
    fig.subplots_adjust(left=.27, right=.98, top=.76, bottom=.18, wspace=.12)
    for i, (ax, field, label, xmax) in enumerate(zip(
            axes, ['mean_pose_rmse_mm', 'recalibrations_per_actuator'],
            ['Mean pose RMSE (mm)', 'Calibrations per actuator'], [.45, 5.5])):
        for y, row in enumerate(rows):
            ax.plot(row[field], y, marker=POLICY_MARKERS[row['policy']],
                    mfc=style.FILL[row['mean_pose_rmse_mm'] <= audit['budget_mm']], zorder=3, **style.MARKER)
        ax.set_xlim(0, xmax)
        ax.set_ylim(len(rows) - .5, -.6)
        ax.set_xlabel(label)
        ax.tick_params(axis='y', length=0)
        style.letter(ax, i)
    axes[1].spines['left'].set_visible(False)
    axes[1].tick_params(axis='y', left=False)
    axes[0].set_yticks(range(len(rows)), [tick(r['label']) for r in rows])
    axes[0].axvline(audit['budget_mm'], zorder=1, **style.REFERENCE)
    handles = [Line2D([], [], marker='o', mfc=style.FILL[True], label='Filled: within budget', **style.MARKER),
               Line2D([], [], marker='o', mfc=style.FILL[False], label='Hollow: over budget', **style.MARKER),
               Line2D([], [], label='Error budget', **style.REFERENCE)]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .995), ncol=3,
               columnspacing=1.4, handletextpad=.5, borderaxespad=0)
    return fig


def lead_caption(study):
    rows = study['lead_time_heldout']['per_actuator']
    lt = study['lead_time_heldout']
    late = sum(r['lead_life'] < 0 for r in rows)
    late = 'every held-out actuator' if late == len(rows) else f'{late} of {len(rows)} held-out actuators'
    return (
        f"Saved Study 3 crossing estimates for the {len(rows)} held-out actuators at the deployed "
        f"threshold τ = {study['tau_selected']:.2f}; {lt['n_excluded']} excluded. Panel (a) shows, per "
        "actuator, the normalized life at which pose error crosses the error budget (triangle) and at "
        "which the P-V trigger fires (diamond); the thin line joins each pair and is not an interval. "
        "Panel (b) shows the lead, budget-crossing life minus trigger life, with the dashed line at zero "
        "lead; a hollow diamond marks a late trigger (negative lead). The trigger fires after the budget "
        f"crossing on {late}, with leads from {lt['min_lead_life']:.3f} to {lt['max_lead_life']:.3f} "
        "life. Crossings are interpolated from the saved life-stage analysis, with no new trajectories or "
        "exclusions. Values: trigger_timing.csv. Source: study3_results.json.")


def lead_figure(study):
    rows = study['lead_time_heldout']['per_actuator']
    style.apply()
    fig, (timing, lead) = plt.subplots(1, 2, figsize=(style.FULL, 2.4), sharey=True)
    fig.subplots_adjust(left=.11, right=.98, top=.76, bottom=.18, wspace=.12)
    for y, row in enumerate(rows):
        a, b = row['budget_violation_life'], row['trigger_life']
        timing.plot([a, b], [y, y], color=style.INK, lw=.6, zorder=1)
        timing.plot(a, y, marker='^', mfc=style.FILL[True], zorder=3, **style.MARKER)
        timing.plot(b, y, marker='D', mfc=style.FILL[True], zorder=3, **style.MARKER)
        lead.plot([0, row['lead_life']], [y, y], color=style.INK, lw=.6, zorder=1)
        lead.plot(row['lead_life'], y, marker='D', mfc=style.FILL[row['lead_life'] >= 0], zorder=3, **style.MARKER)
    timing.set_xlim(0, 1)
    timing.set_xlabel('Normalized life (fraction)')
    timing.set_yticks(range(len(rows)), [f"Actuator {r['actuator_id']}" for r in rows])
    lead.set_xlim(-.35, .05)
    lead.axvline(0, zorder=1, **style.REFERENCE)
    lead.set_xlabel(r'Budget crossing $-$ trigger (life fraction)')
    lead.spines['left'].set_visible(False)
    lead.tick_params(axis='y', left=False)
    for i, ax in enumerate((timing, lead)):
        ax.set_ylim(len(rows) - .5, -.6)
        ax.tick_params(axis='y', length=0)
        style.letter(ax, i)
    handles = [Line2D([], [], marker='^', mfc=style.FILL[True], label='Budget crossing', **style.MARKER),
               Line2D([], [], marker='D', mfc=style.FILL[True], label='Trigger', **style.MARKER),
               Line2D([], [], marker='D', mfc=style.FILL[False], label='Hollow: late trigger', **style.MARKER),
               Line2D([], [], label='Zero lead', **style.REFERENCE)]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .995), ncol=4,
               columnspacing=1.4, handletextpad=.5, borderaxespad=0)
    return fig


def coupling_caption(study):
    at = study['softness_multiplier_at_threshold']
    assert all(v is None for v in at['C_m'].values()), at['C_m']
    rs = ' and '.join(f"{float(k):.0%} at {v:.1f} times the default" for k, v in at['R_s'].items())
    cm = np.asarray(study['coupling_vs_multiplier']['C_m']) * 100
    refs = ' and '.join(f'{t:.0%}' for t in study['thresholds'])
    return (
        "Saved deterministic Study 4 sweep of the lumped three-chamber network at a "
        f"{study['probe']['freq_hz']:g} Hz probe. Cross-talk is the neighbour pressure amplitude divided "
        "by the driven amplitude. One parameter is varied at a time, as a ratio to its default on a "
        "logarithmic axis, with all others fixed. Solid line and circles: supply resistance R_s; dashed "
        "line and squares: manifold compliance C_m. The filled diamond is the default network, "
        f"{study['default_coupling'] * 100:.1f}%. Dotted lines are the original sweep reference levels, "
        f"{refs}; they are not confidence limits. Cross-talk rises with supply resistance, reaching {rs}, "
        f"and stays between {cm.min():.1f}% and {cm.max():.1f}% across the compliance sweep. No uncertainty "
        "band; no physical gripper tested. Values: cross_talk.csv. Source: study4_results.json.")


def coupling_figure(study):
    style.apply()
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.subplots_adjust(left=.11, right=.97, top=.83, bottom=.16)
    x = study['sweep_multiplier']
    for threshold in study['thresholds']:
        ax.axhline(threshold * 100, color=style.INK, ls=':', lw=.8, zorder=1)
    curves = [('R_s', 'Supply resistance $R_s$', 'o', '-'),
              ('C_m', 'Manifold compliance $C_m$', 's', '--')]
    handles = []
    for key, label, marker, ls in curves:
        y = np.asarray(study['coupling_vs_multiplier'][key]) * 100
        handles += ax.plot(x, y, color=style.INK, lw=1.0, ls=ls, marker=marker, markevery=3, ms=3.5,
                           mfc=style.FILL[True], label=label, zorder=2)
    handles += ax.plot(1, study['default_coupling'] * 100, marker='D', mfc=style.FILL[True], zorder=3,
                       label='Default network', **{**style.MARKER, 'ms': 5.5})
    handles.append(Line2D([], [], color=style.INK, ls=':', lw=.8, label='Reference levels'))
    ax.set_xscale('log', base=2)
    ax.set_xlim(min(x) / 1.08, max(x) * 1.08)
    ticks = [.25, .5, 1, 2, 4, 8, 16, 32]
    ax.set_xticks(ticks, [f'{v:g}' for v in ticks])
    ax.minorticks_off()
    ax.set_ylim(0, 45)
    ax.set_xlabel('Varied parameter / default (ratio, log scale)')
    ax.set_ylabel('Neighbour / driven amplitude (%)')
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.54, .995), ncol=2,
               columnspacing=1.4, handletextpad=.5, borderaxespad=0)
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    audit, study3, study4 = load()
    rows = policies(audit, study3)
    for stem, fig, caption in (('policy_comparison', policy_figure(rows, audit), policy_caption(rows, audit, study3)),
                               ('trigger_timing', lead_figure(study3), lead_caption(study3)),
                               ('cross_talk', coupling_figure(study4), coupling_caption(study4))):
        style.save(fig, OUT / stem, formats=('png', 'svg'), caption=caption)
        plt.close(fig)
    write_csv('trigger_timing.csv', study3['lead_time_heldout']['per_actuator'])
    write_csv('cross_talk.csv', [dict(multiplier=m, R_s_coupling_ratio=a, C_m_coupling_ratio=b)
              for m, a, b in zip(study4['sweep_multiplier'], study4['coupling_vs_multiplier']['R_s'],
                                 study4['coupling_vs_multiplier']['C_m'])])
    write_csv('policy_comparison.csv', rows)
    table = '| Policy | Mean pose error, RMSE (mm) | Calibrations per actuator |\n|:---|---:|---:|\n'
    table += '\n'.join(f"| {r['label']} | {r['mean_pose_rmse_mm']:.3f} | {r['recalibrations_per_actuator']:.1f} |"
                       for r in rows)
    for path in ('README.md', 'docs/results.md'):
        replace_table(ROOT / path, table)
    provenance = {'evidence': 'Saved simulation outputs only; no new evaluation or physical data',
                  'inputs_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS},
                  'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'style_sha256': hashlib.sha256((ROOT / 'scripts/figure_style.py').read_bytes()).hexdigest(),
                  'matplotlib_version': matplotlib.__version__,
                  'style_reference': STYLE_REFERENCE,
                  'csv_note': 'Generated views; original JSON remains the numeric source of truth.'}
    (OUT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(OUT)


if __name__ == '__main__':
    main()
