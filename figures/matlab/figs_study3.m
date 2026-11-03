function F = figs_study3()
%FIGS_STUDY3 Study 3 and cluster-interval figures (data/sim/phaseD).
F = {'data/sim/phaseD/study3_fig3_leading_indicator',       @leading_indicator
     'data/sim/phaseD/study3_fig4_recal_tradeoff',          @tradeoff
     'data/sim/phaseD/study3_fig3b_correlation_cluster_ci', @correlation_ci
     'data/sim/phaseD/study3_fig4b_recal_cluster_ci',       @tradeoff_ci};
end

function P = policies(period, tau)
% Policy key, marker, direct label; same order and shapes as scripts/run_study3.py POLICIES.
P = {'fixed',     'o', 'initial calibration only'
     'scheduled', '^', sprintf('clock, %s cycles', commas(period))
     'triggered', 'd', sprintf('P-V trigger, $\\tau = %g$', tau)
     'always',    'x', 'every life stage'};
end

function h = policy_marker(ax, x, y, mk, within, S)
if within
    col = S.c.blue; face = S.c.blue;
else
    col = S.c.orange; face = 'w';
end
if mk == 'x', face = 'none'; end
h = plot(ax, x, y, mk, 'MarkerSize', 6.5, 'MarkerEdgeColor', col, 'MarkerFaceColor', face, 'LineWidth', 1.3);
end

function leading_indicator(root, outRoot, rel, S)
T = readtable(fullfile(root, 'data/sim/phaseD/figdata/study3_fig3_leading_indicator.csv'));
fig = sar_fig(8.9, 8.6);
tl = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
ax = nexttile(tl); hold(ax, 'on');
plot(ax, T.life_fraction, T.loop_area_over_young, '-o', 'Color', S.c.blue, 'MarkerFaceColor', S.c.blue, ...
    'MarkerSize', 4, 'LineWidth', 1.3);
ylabel(ax, {'P-V loop area', '(${\times}$ young)'});
set(ax, 'XTick', T.life_fraction, 'XTickLabel', {}, 'XLim', [0.05 0.95]);
sar_letter(ax, 'a', S);
bx = nexttile(tl); hold(bx, 'on');
plot(bx, T.life_fraction, T.fixed_error_mm, '-s', 'Color', S.c.orange, 'MarkerFaceColor', S.c.orange, ...
    'MarkerSize', 4.5, 'LineWidth', 1.3);
ylabel(bx, {'Pose RMSE, young', 'calibration (mm)'});
set(bx, 'XTick', T.life_fraction, 'XLim', [0.05 0.95], 'YLim', [-0.08 max(T.fixed_error_mm) * 1.1]);
xlabel(bx, 'Normalized life');
sar_letter(bx, 'b', S);
sar_save(fig, outRoot, rel);
end

function tradeoff(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/phaseD/study3_results.json'));
pol = R.policies_on_heldout; budget = R.accuracy_budget_mm;
P = policies(R.period_selected_cycles, R.tau_selected);
fig = sar_fig(8.9, 7.0);
ax = axes(fig); hold(ax, 'on');
yline(ax, budget, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
top = 0;
for k = 1:size(P, 1)
    p = pol.(P{k, 1});
    x = p.recal_per_actuator; y = p.mean_pose_rmse_mm;
    policy_marker(ax, x, y, P{k, 2}, y <= budget, S);
    if x > 4
        text(ax, x, y + 0.025, P{k, 3}, 'FontSize', S.size.note, 'Color', S.c.ink, ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
    else
        text(ax, x + 0.22, y, P{k, 3}, 'FontSize', S.size.note, 'Color', S.c.ink, 'VerticalAlignment', 'middle');
    end
    top = max(top, y);
end
text(ax, 5.6, budget + 0.008, sprintf('error budget %.3f mm', budget), 'FontSize', S.size.note, ...
    'Color', S.c.grey, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
set(ax, 'XLim', [0.5 5.7], 'XTick', 1:5, 'YLim', [0 top * 1.12]);
xlabel(ax, 'Calibrations per actuator over life');
ylabel(ax, 'Mean pose RMSE (mm)');
sar_save(fig, outRoot, rel);
end

function correlation_ci(root, outRoot, rel, S)
T = readtable(fullfile(root, 'data/sim/phaseD/figdata/study3_fig3b_correlation_cluster_ci.csv'));
FT = readtable(fullfile(root, 'data/sim/phaseD/figdata/study3_fig3b_correlation_cluster_ci_fit.csv'));
R = sar_json(fullfile(root, 'data/sim/phaseD/study3_cluster_ci_results.json'));
C = R.correlation;
ids = unique(T.actuator_id, 'stable');
fig = sar_fig(17.4, 6.8);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'loose', 'Padding', 'compact');

ax = nexttile(tl); hold(ax, 'on');
ends = zeros(numel(ids), 1); xe = 0;
for k = 1:numel(ids)
    sel = T.actuator_id == ids(k);
    x = T.loop_area_growth(sel); y = T.fixed_error_mm(sel);
    plot(ax, x, y, '-o', 'Color', [0.6 0.6 0.6], 'MarkerFaceColor', [0.6 0.6 0.6], ...
        'MarkerEdgeColor', 'w', 'MarkerSize', 4, 'LineWidth', 0.9);
    ends(k) = y(end); xe = x(end);
end
xs = linspace(FT.x_min, FT.x_max, 50);
plot(ax, xs, FT.intercept_mm + FT.slope_mm * xs, '--', 'Color', S.c.orange, 'LineWidth', 1.3);
% labels at the right end, pushed apart so neighbours do not touch
[sv, o] = sort(ends);
gap = 0.06 * (max(ends) - min(T.fixed_error_mm));
lab = sv;
for k = 2:numel(lab), lab(k) = max(lab(k), lab(k - 1) + gap); end
for k = 1:numel(o)
    text(ax, xe * 1.04, lab(k), sprintf('\\#%d', ids(o(k))), 'FontSize', S.size.tick, ...
        'Color', [0.45 0.45 0.45], 'VerticalAlignment', 'middle');
end
text(ax, 0.002, 0.85 * max(T.fixed_error_mm), {'pooled fit (dashed)', sprintf('$r = %.3f$', C.r)}, ...
    'Color', S.c.orange, 'FontSize', S.size.note, 'VerticalAlignment', 'middle');
set(ax, 'XLim', [-0.004, xe * 1.2]);
xlabel(ax, 'P-V loop-area growth from young');
ylabel(ax, 'Pose error, young calibration (mm)');
sar_letter(ax, 'a', S);

bx = nexttile(tl); hold(bx, 'on');
n = C.n_clusters;
rows = {'point bootstrap (superseded)', C.committed_point_level_bootstrap, [0.65 0.65 0.65], C.r, 'o'
        sprintf('cluster bootstrap ($%d^{%d}$)', n, n), C.actuator_cluster_bootstrap, S.c.blue, C.r, 'o'
        'leave one actuator out (Fisher $z$)', C.leave_one_actuator_out_fisher_z, S.c.blue, C.r, 'o'
        'within-actuator $r$ (other estimand)', C.within_actuator, S.c.ink, C.within_actuator.r_within_actuator, 's'};
m = size(rows, 1);
y = (m:-1:1)';
for i = 1:m
    v = rows{i, 2}; col = rows{i, 3};
    plot(bx, [v.ci_low v.ci_high], [y(i) y(i)], '-', 'Color', col, 'LineWidth', 2.2);
    plot(bx, rows{i, 4}, y(i), rows{i, 5}, 'MarkerSize', 6, 'MarkerFaceColor', col, 'MarkerEdgeColor', 'w');
    text(bx, v.ci_high + 0.012, y(i), sprintf('%.2f--%.2f', v.ci_low, v.ci_high), 'FontSize', S.size.note, ...
        'Color', col, 'VerticalAlignment', 'middle');
end
set(bx, 'YTick', flipud(y), 'YTickLabel', flipud(rows(:, 1)), 'YLim', [0.4 m + 0.6], ...
    'XLim', [0.5 1.13], 'XTick', 0.6:0.1:1.0);
try
    bx.YAxis.Color = 'none'; bx.YAxis.TickLabelColor = S.c.ink;
catch
end
xlabel(bx, 'Pearson $r$, point and 95\% interval');
sar_letter(bx, 'b', S);
sar_save(fig, outRoot, rel);
end

function tradeoff_ci(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/phaseD/study3_cluster_ci_results.json'));
Pd = R.policies_on_heldout_with_cluster_ci; FR = sar_list(R.lead_frontier_with_cluster_ci);
prov = R.provenance; budget = prov.accuracy_budget_mm; tau0 = prov.tau_selected;
P = policies(prov.period_selected_cycles, tau0);
fig = sar_fig(17.4, 7.4);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'loose', 'Padding', 'compact');

ax = nexttile(tl); hold(ax, 'on');
yline(ax, budget, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
for k = 1:size(P, 1)
    v = Pd.(P{k, 1});
    x = v.recal_per_actuator; y = v.mean_pose_rmse_mm;
    if v.recal_ci_low ~= v.recal_ci_high      % an interval of zero width is not drawn
        plot(ax, [v.recal_ci_low v.recal_ci_high], [y y], '-|', 'Color', S.c.ink, 'LineWidth', 0.8, 'MarkerSize', 5);
    end
    if v.rmse_ci_low ~= v.rmse_ci_high
        plot(ax, [x x], [v.rmse_ci_low v.rmse_ci_high], '-_', 'Color', S.c.ink, 'LineWidth', 0.8, 'MarkerSize', 5);
    end
    policy_marker(ax, x, y, P{k, 2}, y <= budget, S);
    if x > 4
        text(ax, x, max(y, v.rmse_ci_high) + 0.03, P{k, 3}, 'FontSize', S.size.note, 'Color', S.c.ink, ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
    else
        text(ax, max(x, v.recal_ci_high) + 0.18, y, P{k, 3}, 'FontSize', S.size.note, 'Color', S.c.ink, ...
            'VerticalAlignment', 'middle');
    end
end
text(ax, 5.6, budget + 0.01, sprintf('error budget %.3f mm', budget), 'FontSize', S.size.note, ...
    'Color', S.c.grey, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
set(ax, 'XLim', [0.5 5.7], 'XTick', 1:5, 'YLim', [0 0.62]);
xlabel(ax, 'Calibrations per actuator over life');
ylabel(ax, 'Mean pose RMSE (mm)');
sar_letter(ax, 'a', S);

bx = nexttile(tl); hold(bx, 'on');
taus = cellfun(@(p) p.tau, FR);
mean_lead = cellfun(@(p) p.mean_lead_life, FR);
lo = cellfun(@(p) p.lead_ci_low, FR); hi = cellfun(@(p) p.lead_ci_high, FR);
per = cell2mat(cellfun(@(p) p.lead_per_actuator(:)', FR(:), 'UniformOutput', false));   % tau x actuator
fill(bx, [taus fliplr(taus)], [lo fliplr(hi)], [0.85 0.85 0.85], 'EdgeColor', 'none');
for j = 1:size(per, 2)
    plot(bx, taus, per(:, j), '-', 'Color', [0.6 0.6 0.6], 'LineWidth', 0.6);
end
yline(bx, 0, '-', 'Color', S.c.ink, 'LineWidth', 0.6);
xline(bx, tau0, '-.', 'Color', S.c.ink, 'LineWidth', 0.8);
plot(bx, taus, mean_lead, '-', 'Color', S.c.ink, 'LineWidth', 1.0);
early = mean_lead > 0;
plot(bx, taus(early), mean_lead(early), 'o', 'MarkerSize', 5.5, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
plot(bx, taus(~early), mean_lead(~early), 'o', 'MarkerSize', 5.5, 'MarkerFaceColor', 'w', ...
    'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.1);
text(bx, tau0 - 0.001, 0.5, sprintf('deployed $\\tau = %g$', tau0), 'FontSize', S.size.note, 'Color', S.c.ink, ...
    'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
text(bx, taus(1) + 0.002, mean_lead(1) + 0.03, 'mean lead', 'FontSize', S.size.note, 'Color', S.c.ink, ...
    'VerticalAlignment', 'bottom');
text(bx, 0.002, -0.25, {'grey band: 95\% cluster interval', 'thin lines: single actuators'}, ...
    'FontSize', S.size.tick, 'Color', [0.45 0.45 0.45]);
set(bx, 'XLim', [0, max(taus) * 1.08], 'YLim', [-0.36 0.56], 'XTick', 0.01:0.01:0.05);
xlabel(bx, 'Trigger threshold $\tau$ (loop-area growth)');
ylabel(bx, 'Lead over the budget crossing (life)');
sar_letter(bx, 'b', S);
sar_save(fig, outRoot, rel);
end

function s = commas(v)
s = char(string(round(v)));
k = numel(s) - 3;
while k > 0
    s = [s(1:k) ',' s(k + 1:end)];
    k = k - 3;
end
end
