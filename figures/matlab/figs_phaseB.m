function F = figs_phaseB()
%FIGS_PHASEB Phase B fatigue figures (data/sim/phaseB).
F = {'data/sim/phaseB/fig_pv_loops_over_life',       @pv_loops_over_life
     'data/sim/phaseB/fig_fatigue_trajectory',       @fatigue_trajectory
     'data/sim/phaseB/fig_pressure_decay_over_life', @pressure_decay
     'data/sim/phaseB/fig_onset_sensitivity',        @onset_sensitivity
     'data/sim/phaseB/fig_rest_recovery',            @rest_recovery
     'data/sim/phaseB/fig_leak_sensitivity',         @leak_sensitivity};
end

function key_list(ax, x, y, dy, head, items, C, S)
% Coloured list of series names stacked from (x, y) downward, in axes-normalized units.
text(ax, x, y, head, 'Units', 'normalized', 'FontSize', S.size.note, 'Color', S.c.ink, ...
    'VerticalAlignment', 'top');
for k = 1:numel(items)
    text(ax, x, y - k * dy, items{k}, 'Units', 'normalized', 'FontSize', S.size.note, ...
        'Color', C(k, :), 'VerticalAlignment', 'top');
end
end

function pv_loops_over_life(root, outRoot, rel, S)
T = readtable(fullfile(root, 'data/sim/phaseB/figdata/fig_pv_loops_over_life.csv'));
n = unique(T.cycles, 'stable');
C = sar_ramp(S.c.blue, numel(n), 0.45);
fig = sar_fig(8.9, 7.4);
ax = axes(fig); hold(ax, 'on');
for k = 1:numel(n)
    sel = T.cycles == n(k);
    V = 1e6 * T.volume_m3(sel); P = T.pressure_pa(sel) / 1e3;
    plot(ax, [V; V(1)], [P; P(1)], '-', 'Color', C(k, :), 'LineWidth', 1.0);
end
key_list(ax, 0.03, 0.98, 0.075, 'cycles', arrayfun(@(v) commas(v), n, 'UniformOutput', false), C, S);
xlabel(ax, 'Chamber volume (mL)');
ylabel(ax, 'Chamber pressure (kPa)');
sar_save(fig, outRoot, rel);
end

function fatigue_trajectory(root, outRoot, rel, S)
T = readtable(fullfile(root, 'data/sim/phaseB/figdata/fig_fatigue_trajectory.csv'));
R = sar_json(fullfile(root, 'data/sim/phaseB/phaseB_results.json'));
onset = R.acceleration_onset_cycle;
ys = {T.compliance_rise_pct, T.loop_area_rise_pct, T.leak_multiplier};
labs = {'Compliance rise (\%)', 'Loop-area rise (\%)', 'Leak (${\times}$ healthy)'};
fig = sar_fig(8.9, 10.5);
tl = tiledlayout(fig, 3, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
for k = 1:3
    ax = nexttile(tl); hold(ax, 'on');
    xline(ax, onset, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
    plot(ax, T.cycles, ys{k}, '-', 'Color', S.c.blue, 'LineWidth', 1.3);
    lo = min(ys{k}); hi = max(ys{k}); pad = 0.08 * (hi - lo);
    set(ax, 'XLim', [-70 T.cycles(end) + 70], 'YLim', [lo - pad, hi + pad]);
    ylabel(ax, labs{k});
    if k < 3, ax.XTickLabel = {}; else, xlabel(ax, 'Cycles'); end
    if k == 1
        text(ax, onset - 60, hi, sprintf('onset %s cycles', commas(onset)), 'Color', S.c.grey, ...
            'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
    end
    sar_letter(ax, char('a' + k - 1), S);
end
sar_save(fig, outRoot, rel);
end

function pressure_decay(root, outRoot, rel, S)
T = readtable(fullfile(root, 'data/sim/phaseB/figdata/fig_pressure_decay_over_life.csv'), ...
    'VariableNamingRule', 'preserve');
names = T.Properties.VariableNames(2:end);
C = sar_ramp(S.c.blue, numel(names), 0.45);
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
yline(ax, 0.5, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
items = cell(1, numel(names));
for k = 1:numel(names)
    plot(ax, T.time_s, T.(names{k}), '-', 'Color', C(k, :), 'LineWidth', 1.2);
    items{k} = commas(str2double(extractAfter(names{k}, 'p_over_p0_c')));
end
text(ax, 1.6, 0.52, 'half pressure', 'Color', S.c.grey, 'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
key_list(ax, 0.78, 0.98, 0.08, 'cycles', items, C, S);
set(ax, 'XLim', [-0.05 3.05], 'YLim', [-0.03 1.04]);
xlabel(ax, 'Hold time with valve closed (s)');
ylabel(ax, 'Pressure / initial pressure');
sar_save(fig, outRoot, rel);
end

function onset_sensitivity(root, outRoot, rel, S)
T = readtable(fullfile(root, 'data/sim/phaseB/figdata/fig_onset_sensitivity.csv'), 'VariableNamingRule', 'preserve');
names = T.Properties.VariableNames(2:end);
C = sar_ramp(S.c.blue, numel(names), 0.45);
R = sar_json(fullfile(root, 'data/sim/phaseB/phaseB_results.json'));
life = R.canonical_parameters.rupture_cycles;
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
for k = 1:numel(names)
    y = T.(names{k});
    plot(ax, T.cycles, y, '-', 'Color', C(k, :), 'LineWidth', 1.3);
    o = str2double(extractAfter(names{k}, 'accelerating_pct_onset'));
    text(ax, o * life, 0.3, sprintf('%.2f', o), 'Color', C(k, :), 'FontSize', S.size.note, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
end
text(ax, 0.03, 0.95, 'onset (fraction of life)', 'Units', 'normalized', 'Color', S.c.ink, 'FontSize', S.size.note);
top = max(T{:, 2:end}, [], 'all');
set(ax, 'XLim', [-60 T.cycles(end) + 60], 'YLim', [-0.03 * top, top * 1.08]);
xlabel(ax, 'Cycles');
ylabel(ax, 'Accelerating compliance term (\%)');
sar_save(fig, outRoot, rel);
end

function rest_recovery(root, outRoot, rel, S)
% Input: phaseB_results.json recovery. Horizontal axis linear to 1 h, logarithmic above.
R = sar_json(fullfile(root, 'data/sim/phaseB/phaseB_results.json'));
rec = sar_list(R.recovery);
h = cellfun(@(r) r.rest_hours, rec);
perm = 100 * cellfun(@(r) r.mullins_permanent, rec);
recv = 100 * cellfun(@(r) r.mullins_recoverable, rec);
tot = perm + recv;
xt = h; xt(h > 1) = 1 + log10(h(h > 1));
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
light = 1 - (1 - S.c.blue) * 0.25;
fill(ax, [xt fliplr(xt)], [zeros(size(perm)) fliplr(perm)], [0.82 0.82 0.82], 'EdgeColor', 'none');
fill(ax, [xt fliplr(xt)], [perm fliplr(tot)], light, 'EdgeColor', 'none');
plot(ax, xt, tot, '-o', 'Color', S.c.blue, 'MarkerFaceColor', S.c.blue, 'MarkerSize', 4, 'LineWidth', 1.2);
text(ax, 0.1, perm(1) / 2, 'permanent', 'Color', S.c.ink, 'FontSize', S.size.note, 'VerticalAlignment', 'middle');
text(ax, 0.1, perm(1) + 0.45 * (tot(1) - perm(1)), 'recoverable', 'Color', S.c.ink, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'middle');
text(ax, xt(2) + 0.08, tot(2) + 0.12, 'total, sampled', 'Color', S.c.blue, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'bottom');
set(ax, 'XLim', [0, 1 + log10(max(h) * 1.4)], 'XTick', [0 1 2 3], 'XTickLabel', {'0', '1', '10', '100'}, ...
    'YLim', [0 max(tot) * 1.12]);
xlabel(ax, 'Rest time (h)');
ylabel(ax, 'Mullins compliance rise (\%)');
sar_save(fig, outRoot, rel);
end

function leak_sensitivity(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/phaseB/phaseB_results.json'));
rows = sar_list(R.sensitivity.terminal_leak_multipliers);
m = cellfun(@(r) r.terminal_multiplier, rows);
hl = 1e3 * cellfun(@(r) r.rupture_half_life_s, rows);
fig = sar_fig(8.9, 6.0);
ax = axes(fig); hold(ax, 'on');
plot(ax, m, hl, '-o', 'Color', S.c.blue, 'MarkerFaceColor', S.c.blue, 'MarkerSize', 4, 'LineWidth', 1.2);
span = max(m) - min(m);
set(ax, 'XTick', m, 'XLim', [min(m) - 0.08 * span, max(m) + 0.08 * span], 'YLim', [0 max(hl) * 1.2]);
xlabel(ax, 'Leak conductance at rupture (${\times}$ healthy)');
ylabel(ax, 'Hold half-life at rupture (ms)');
sar_save(fig, outRoot, rel);
end

function s = commas(v)
% Integer with thousands separators, as in the captions (2,450).
s = char(string(round(v)));
k = numel(s) - 3;
while k > 0
    s = [s(1:k) ',' s(k + 1:end)];
    k = k - 3;
end
end
