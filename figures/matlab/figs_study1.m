function F = figs_study1()
%FIGS_STUDY1 Study 1 health-indicator figures (data/sim/study1), from study1_results.json.
F = {'data/sim/study1/fig_hi_fusion_comparison',     @fusion
     'data/sim/study1/fig_recovery_validation',      @recovery
     'data/sim/study1/fig_metric_fixtures',          @fixtures
     'data/sim/study1/fig_onset_generalization_gap', @onset
     'data/sim/study1/fig_detector_comparison',      @detector};
end

function R = load1(root)
R = sar_json(fullfile(root, 'data/sim/study1/study1_results.json'));
end

function fusion(root, outRoot, rel, S)
fu = load1(root).fusion_comparison;
c = fu.cycles(:);
series = {fu.area_hi(:), '-', S.c.blue, 'loop area'
          fu.fused_hi(:), '--', S.c.ink, 'fused $z$-mean'
          fu.compliance_hi(:), ':', S.c.orange, 'compliance'};
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
for k = 1:3
    plot(ax, c, series{k, 1}, series{k, 2}, 'Color', series{k, 3}, 'LineWidth', 1.3);
    text(ax, c(end) + 60, series{k, 1}(end), series{k, 4}, 'Color', series{k, 3}, ...
        'FontSize', S.size.note, 'VerticalAlignment', 'middle');
end
lo = min(cellfun(@min, series(:, 1))); hi = max(cellfun(@max, series(:, 1)));
set(ax, 'XLim', [c(1) - 60, c(end) * 1.33], 'XTick', 0:1000:3000, 'YLim', [lo - 0.04 * (hi - lo), hi * 1.05]);
xlabel(ax, 'Cycles');
ylabel(ax, {'Health index above baseline', '(baseline noise SDs)'});
sar_save(fig, outRoot, rel);
end

function recovery(root, outRoot, rel, S)
% The injected recovery time constant is the canonical FatigueParams value, stored in phaseB_results.json.
rec = sar_list(load1(root).recovery);
B = sar_json(fullfile(root, 'data/sim/phaseB/phaseB_results.json'));
tau = B.canonical_parameters.recovery_tau_s / 3600;
life = cellfun(@(r) r.cycles, rec);
ta = cellfun(@(r) r.fits.loop_area.tau_s, rec) / 3600;
tc = cellfun(@(r) r.fits.compliance.tau_s, rec) / 3600;
fig = sar_fig(8.9, 6.0);
ax = axes(fig); hold(ax, 'on');
yline(ax, tau, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
plot(ax, life, ta, 'o', 'MarkerSize', 8, 'MarkerEdgeColor', S.c.blue, 'MarkerFaceColor', 'w', 'LineWidth', 1.1);
plot(ax, life, tc, 'x', 'MarkerSize', 6, 'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.3);
text(ax, life(1), tau + 0.12, 'loop-area fit', 'Color', S.c.blue, 'FontSize', S.size.note, ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
text(ax, life(1), tau - 0.12, 'compliance fit', 'Color', S.c.orange, 'FontSize', S.size.note, ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'top');
text(ax, life(end), tau - 0.12, sprintf('injected $\\tau = %g$ h', tau), 'Color', S.c.grey, ...
    'FontSize', S.size.note, 'HorizontalAlignment', 'center', 'VerticalAlignment', 'top');
span = max(life) - min(life);
set(ax, 'XTick', life, 'XTickLabel', arrayfun(@(v) sprintf('%s', commas(v)), life, 'UniformOutput', false), ...
    'XLim', [min(life) - 0.18 * span, max(life) + 0.18 * span], 'YLim', [23.5 24.5]);
xlabel(ax, 'Life stage of the rest test (cycles)');
ylabel(ax, 'Recovered time constant $\tau$ (h)');
sar_save(fig, outRoot, rel);
end

function fixtures(root, outRoot, rel, S)
f = load1(root).metric_fixtures;
rows = {'Monotonicity: clean trajectory',             f.monotonicity_clean,                true
        'Monotonicity: recovery dip',                 f.monotonicity_recovery_dip,         false
        'Trendability: self-similar units',           f.trendability_self_similar,         true
        'Trendability: corrupted unit',               f.trendability_corrupted,            false
        'Prognosability: known end-of-life spread',   f.prognosability_known_spread.value, true};
n = size(rows, 1);
y = (n:-1:1)';
fig = sar_fig(11.5, 5.8);
ax = axes(fig); hold(ax, 'on');
for i = 1:n
    plot(ax, [0 rows{i, 2}], [y(i) y(i)], '-', 'Color', S.c.stem, 'LineWidth', 1.4);
end
clean = [rows{:, 3}]';
v = [rows{:, 2}]';
hIn = plot(ax, v(clean), y(clean), 'o', 'MarkerSize', 6, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
hOut = plot(ax, v(~clean), y(~clean), 'o', 'MarkerSize', 6, 'MarkerFaceColor', 'w', ...
    'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.2);
set(ax, 'YTick', flipud(y), 'YTickLabel', flipud(rows(:, 1)), 'YLim', [0.4 n + 0.6], ...
    'XLim', [0 1.05], 'XTick', 0:0.25:1, 'XTickLabel', {'0', '0.25', '0.5', '0.75', '1'});
hide_y_spine(ax, S);
xlabel(ax, 'Metric value (1 = ideal)');
legend(ax, [hIn hOut], {'clean fixture', 'corrupted fixture'}, 'Location', 'northoutside', ...
    'Orientation', 'horizontal', 'Box', 'off', 'FontSize', S.size.note);
sar_save(fig, outRoot, rel);
end

function onset(root, outRoot, rel, S)
% Onset 0.70 of life, 100-cycle probe; one panel per generator (quadratic, logistic k ascending).
R = load1(root);
cond = sar_list(R.conditions);
keep = cellfun(@(c) abs(c.onset_fraction - 0.70) < 1e-9 && c.cadence_cycles == 100, cond);
cond = cond(keep);
gen = string(cellfun(@(c) c.generator, cond, 'UniformOutput', false));
k = cellfun(@(c) sharp(c), cond);
keys = unique(table(gen(:) ~= "quadratic", k(:), gen(:), 'VariableNames', {'log', 'k', 'gen'}), 'rows');
mk = {'o', 's', '^', 'd'};
noise = R.registered_protocol.noise_percent_fs_sigma(:)';
fig = sar_fig(8.9, 8.0);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for g = 1:height(keys)
    sel = gen == keys.gen(g) & k == keys.k(g);
    rows = cond(sel);
    x = cellfun(@(c) c.noise_percent_fs_sigma, rows);
    yv = cellfun(@(c) c.models.segmented_quadratic.median_absolute_onset_error, rows);
    [x, o] = sort(x); yv = yv(o);
    ax = nexttile(tl); hold(ax, 'on');
    if keys.gen(g) == "quadratic"
        col = S.c.blue; lab = 'quadratic data';
    else
        col = S.c.orange; lab = sprintf('logistic data, $k = %g$', keys.k(g));
    end
    plot(ax, x, yv, ['-' mk{g}], 'Color', col, 'MarkerFaceColor', col, 'MarkerSize', 4, 'LineWidth', 1.1);
    set(ax, 'YLim', [-0.02 0.45], 'YTick', [0 0.2 0.4], 'XTick', noise, ...
        'XTickLabel', arrayfun(@(v) sprintf('%g', v), noise, 'UniformOutput', false), ...
        'XLim', [min(noise) - 0.04, max(noise) + 0.04]);
    if g <= 2, ax.XTickLabel = {}; end
    if mod(g, 2) == 0, ax.YTickLabel = {}; end
    text(ax, 0.04, 0.6, lab, 'Units', 'normalized', 'Color', col, 'FontSize', S.size.note);
    sar_letter(ax, char('a' + g - 1), S);
end
xlabel(tl, 'Pressure noise $\sigma$ (\% of full scale)', 'Interpreter', 'latex', 'FontSize', S.size.label);
ylabel(tl, 'Median onset error (fraction of life)', 'Interpreter', 'latex', 'FontSize', S.size.label);
sar_save(fig, outRoot, rel);
end

function v = sharp(c)
if isempty(c.logistic_sharpness), v = 0; else, v = c.logistic_sharpness; end
end

function detector(root, outRoot, rel, S)
R = load1(root);
cond = sar_list(R.conditions);
keep = cellfun(@(c) ~isempty(c.detection) && string(c.generator) == "quadratic" && ...
    abs(c.onset_fraction - 0.70) < 1e-9 && c.cadence_cycles == 100, cond);
rows = cond(keep);
noise = cellfun(@(c) c.noise_percent_fs_sigma, rows);
[noise, o] = sort(noise); rows = rows(o);
s3 = cellfun(@(c) c.detection.sustained_3sigma.median_alarm_cycle, rows);
cu = cellfun(@(c) c.detection.cusum.median_alarm_cycle, rows);
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
w = 0.34;
for i = 1:numel(rows)
    patch(ax, i - w + [0 w w 0] - 0.01, [0 0 s3(i) s3(i)], S.c.blue, 'EdgeColor', S.c.blue);
    patch(ax, i + [0 w w 0] + 0.01, [0 0 cu(i) cu(i)], 'w', 'EdgeColor', S.c.orange, 'LineWidth', 1.1);
end
hA = patch(ax, NaN, NaN, S.c.blue, 'EdgeColor', S.c.blue);
hB = patch(ax, NaN, NaN, 'w', 'EdgeColor', S.c.orange, 'LineWidth', 1.1);
set(ax, 'XTick', 1:numel(rows), 'XTickLabel', arrayfun(@(v) sprintf('%g', v), noise, 'UniformOutput', false), ...
    'XLim', [0.4 numel(rows) + 0.6], 'YLim', [0 max(cu) * 1.15], 'TickLength', [0 0.012]);
xlabel(ax, 'Pressure noise $\sigma$ (\% of full scale)');
ylabel(ax, 'Median confirmed alarm (cycle)');
legend(ax, [hA hB], {'sustained $3\sigma$', 'CUSUM, matched false alarms'}, 'Location', 'northwest', ...
    'Box', 'off', 'FontSize', S.size.note);
sar_save(fig, outRoot, rel);
end

function hide_y_spine(ax, S)
try
    ax.YAxis.Color = 'none';
    ax.YAxis.TickLabelColor = S.c.ink;
catch
    ax.YAxis.Color = S.c.ink;
end
end

function s = commas(v)
s = char(string(round(v)));
k = numel(s) - 3;
while k > 0
    s = [s(1:k) ',' s(k + 1:end)];
    k = k - 3;
end
end
