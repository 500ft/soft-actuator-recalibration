function F = figs_phaseA()
%FIGS_PHASEA Phase A plant figures (data/sim/phaseA).
F = {'data/sim/phaseA/fig_pv_loops',          @pv_loops
     'data/sim/phaseA/fig_loop_area_vs_freq', @loop_area
     'data/sim/phaseA/fig_gate0_consistency', @gate0_consistency};
end

function pv_loops(root, outRoot, rel, S)
% Input: figdata/fig_pv_loops.csv (one cycle at 0.1x, 1x and 10x the corner frequency).
T = readtable(fullfile(root, 'data/sim/phaseA/figdata/fig_pv_loops.csv'));
mult = [0.1 1 10];
style = {'--', '-', ':'};
col = {S.c.orange, S.c.blue, S.c.ink};
lw = [1.2 1.6 1.3];
fig = sar_fig(8.9, 7.4);
ax = axes(fig); hold(ax, 'on');
order = [1 3 2];                                   % corner loop drawn last, on top
for k = order
    sel = abs(T.freq_multiple - mult(k)) < 1e-9;
    V = 1e6 * T.volume_m3(sel); P = T.pressure_pa(sel) / 1e3;
    plot(ax, [V; V(1)], [P; P(1)], style{k}, 'Color', col{k}, 'LineWidth', lw(k));
    [~, i] = max(V);
    lab = sprintf('%.2f Hz', T.freq_hz(find(sel, 1)));
    if k == 2, lab = [lab ' (corner)']; end
    text(ax, V(i) + 0.1, P(i), lab, 'Color', col{k}, 'FontSize', S.size.note, 'VerticalAlignment', 'middle');
end
set(ax, 'XLim', [2.85 8.6], 'XTick', 3:7);
xlabel(ax, 'Chamber volume (mL)');
ylabel(ax, 'Chamber pressure (kPa)');
sar_save(fig, outRoot, rel);
end

function loop_area(root, outRoot, rel, S)
% Inputs: figdata/fig_loop_area_vs_freq.csv and phaseA_results.json (corner frequency).
T = readtable(fullfile(root, 'data/sim/phaseA/figdata/fig_loop_area_vs_freq.csv'));
R = sar_json(fullfile(root, 'data/sim/phaseA/phaseA_results.json'));
fpk = R.sls.f_loss_peak_hz;
f = T.freq_hz; num = 1e3 * T.area_numeric_j; ana = 1e3 * T.area_analytic_j;
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
xline(ax, fpk, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
plot(ax, f, ana, '-', 'Color', S.c.grey, 'LineWidth', 1.4);
plot(ax, f, num, 'o', 'MarkerSize', 3.5, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', 'none');
ymax = max([num; ana]) * 1.12;
text(ax, fpk * 1.12, 0.03 * ymax, sprintf('corner %.2f Hz', fpk), 'Color', S.c.grey, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
[~, j] = min(abs(f - 0.45));
text(ax, f(j) / 1.25, num(j) + 0.02 * ymax, 'numerical $\oint P\,dV$', 'Color', S.c.blue, ...
    'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
[~, i] = min(abs(f - 7));
text(ax, f(i) * 1.3, ana(i) + 0.04 * ymax, {'analytic SLS', 'dissipation'}, 'Color', S.c.grey, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
set(ax, 'XScale', 'log', 'XLim', [f(1) / 1.15, f(end) * 1.15], 'XTick', [0.1 1 10], ...
    'XTickLabel', {'0.1', '1', '10'}, 'YLim', [0 ymax]);
xlabel(ax, 'Drive frequency (Hz)');
ylabel(ax, 'Loop area (mJ per cycle)');
sar_save(fig, outRoot, rel);
end

function gate0_consistency(root, outRoot, rel, S)
% Input: figdata/fig_gate0_consistency.csv.
T = readtable(fullfile(root, 'data/sim/phaseA/figdata/fig_gate0_consistency.csv'));
f = T.freq_hz;
g0 = 100 * T.crosstalk_gate0; cc = 100 * T.crosstalk_sls_constant_c; sls = 100 * T.crosstalk_sls;
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
plot(ax, f, g0, '-', 'Color', [0.78 0.78 0.78], 'LineWidth', 3.2);
plot(ax, f, cc, '--', 'Color', S.c.blue, 'LineWidth', 1.3);
plot(ax, f, sls, '-', 'Color', S.c.orange, 'LineWidth', 1.3);
text(ax, f(1) * 1.2, 11, {'Gate 0 model (grey) and', 'SLS network with', 'constant $C = 1/k_1$'}, ...
    'Color', S.c.blue, 'FontSize', S.size.note, 'VerticalAlignment', 'middle');
text(ax, f(end), 6, {'SLS network,', 'frequency-dependent $C(\omega)$'}, ...
    'Color', S.c.orange, 'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
set(ax, 'XScale', 'log', 'XLim', [f(1) / 1.15, f(end) * 1.15], 'XTick', [0.01 0.1 1 10 100], ...
    'XTickLabel', {'0.01', '0.1', '1', '10', '100'}, 'YLim', [0, max([g0; sls]) * 1.1]);
xlabel(ax, 'Drive frequency (Hz)');
ylabel(ax, 'Cross-talk $|H_{21}/H_{11}|$ (\%)');
sar_save(fig, outRoot, rel);
end
