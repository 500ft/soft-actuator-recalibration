function F = figs_studyA()
%FIGS_STUDYA Study A dispersion figures (data/sim/studyA).
F = {'data/sim/studyA/studyA_fig_indicator_spread', @indicator_spread
     'data/sim/studyA/studyA_fig_ablation',         @ablation};
end

function indicator_spread(root, outRoot, rel, S)
% Inputs: figdata/studyA_fig_indicator_spread.csv (per-unit mean trajectories) and
% studyA_results.json (between/within SD ratio and ICC per life stage).
T = readtable(fullfile(root, 'data/sim/studyA/figdata/studyA_fig_indicator_spread.csv'), 'VariableNamingRule', 'preserve');
R = sar_json(fullfile(root, 'data/sim/studyA/studyA_results.json'));
life = R.life_fractions(:)';
H = T{:, 2:end};
ratio = sar_num(R.measured.ratio)'; ratio(isnan(ratio)) = Inf;
icc = sar_num(R.measured.icc)';
fig = sar_fig(17.4, 7.0);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(tl, 1, [2 1]); hold(ax, 'on');
for i = 1:size(H, 1)
    plot(ax, life, H(i, :), '-', 'Color', [0.7 0.7 0.7], 'LineWidth', 0.7);
end
lvl = 1 + R.tau_trigger;
yline(ax, lvl, '--', 'Color', S.c.orange, 'LineWidth', 1.0);
text(ax, life(1), lvl + 0.002, sprintf('trigger at $\\tau = %g$', R.tau_trigger), 'Color', S.c.orange, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
set(ax, 'XLim', [life(1) - 0.02, life(end) + 0.02]);
xlabel(ax, 'Normalized life');
ylabel(ax, 'Measured P-V loop area / young');
sar_letter(ax, 'a', S);

bx = nexttile(tl, 2); hold(bx, 'on');
yline(bx, 2, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
plot(bx, life, ratio, '-o', 'Color', S.c.blue, 'MarkerFaceColor', S.c.blue, 'MarkerSize', 3, 'LineWidth', 1.1);
text(bx, life(end), 2.6, 'criterion 2', 'Color', S.c.grey, 'FontSize', S.size.note, ...
    'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
set(bx, 'XLim', [life(1) - 0.02, life(end) + 0.02], 'XTickLabel', {});
ylabel(bx, {'SD ratio,', 'between / within'});
sar_letter(bx, 'b', S);

cx = nexttile(tl, 4); hold(cx, 'on');
yline(cx, 0.5, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
plot(cx, life, icc, '-o', 'Color', S.c.blue, 'MarkerFaceColor', S.c.blue, 'MarkerSize', 3, 'LineWidth', 1.1);
text(cx, life(end), 0.42, 'criterion 0.5', 'Color', S.c.grey, 'FontSize', S.size.note, ...
    'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
set(cx, 'XLim', [life(1) - 0.02, life(end) + 0.02], 'YLim', [-0.35 1.1]);
xlabel(cx, 'Normalized life');
ylabel(cx, 'ICC(1)');
sar_letter(cx, 'c', S);
sar_save(fig, outRoot, rel);
end

function ablation(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/studyA/studyA_results.json'));
ab = R.ablation_one_axis;
keys = fieldnames(ab);
names = containers.Map({'none', 'rupture', 'mullins', 'fatigue_law', 'leak', 'tau', 'stiffness', 'thickness', 'temperature'}, ...
    {'none (all canonical)', 'rupture life', 'Mullins softening', 'degradation law', 'leak', 'time constant $\tau$', ...
     'stiffness', 'wall thickness', 'temperature'});
v = 1e3 * cellfun(@(k) ab.(k).ideal_sd_between_u090, keys);
[v, o] = sort(v, 'descend'); keys = keys(o);
n = numel(v);
y = (n:-1:1)';
zero = 1e-9 * 1e3;                             % spreads below 1e-9 are numerically zero (run_studyA.ZERO)
fig = sar_fig(8.9, 6.6);
ax = axes(fig); hold(ax, 'on');
for i = 1:n
    plot(ax, [0 v(i)], [y(i) y(i)], '-', 'Color', S.c.stem, 'LineWidth', 1.4);
end
up = v > zero;
hIn = plot(ax, v(up), y(up), 'o', 'MarkerSize', 6, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
hOut = plot(ax, v(~up), y(~up), 'o', 'MarkerSize', 6, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.2);
labels = cellfun(@(k) names(k), keys, 'UniformOutput', false);
set(ax, 'YTick', flipud(y), 'YTickLabel', flipud(labels), 'YLim', [0.4 n + 0.6], 'XLim', [-0.6, v(1) * 1.1]);
try
    ax.YAxis.Color = 'none'; ax.YAxis.TickLabelColor = S.c.ink;
catch
end
xlabel(ax, 'Noise-free SD between units at $u = 0.9$ ($10^{-3}$)');
legend(ax, [hIn hOut], {'above $10^{-9}$', 'below $10^{-9}$'}, 'Location', 'southeast', 'Box', 'off', ...
    'FontSize', S.size.note);
sar_save(fig, outRoot, rel);
end
