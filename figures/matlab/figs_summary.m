function F = figs_summary()
%FIGS_SUMMARY Closed-study summaries (data/sim/summary). The policy graph and the
%   cross-talk plot are the approved demo scripts, run unchanged.
F = {'data/sim/summary/policy_comparison', @policy_comparison
     'data/sim/summary/cross_talk',        @cross_talk
     'data/sim/summary/trigger_timing',    @trigger_timing};
end

function policy_comparison(root, outRoot, rel, S)
% make_policy_graph(dataDir, outDir, S) reads policy_comparison.csv and matched_clock_audit.json
% from one folder and writes policy_comparison_matlab.{pdf,png}; this wrapper stages and renames.
run_demo(@make_policy_graph, {'data/sim/summary/policy_comparison.csv', 'data/sim/phaseD/matched_clock_audit.json'}, ...
    'policy_comparison_matlab', root, outRoot, rel, S);
end

function cross_talk(root, outRoot, rel, S)
run_demo(@make_crosstalk_plot, {'data/sim/summary/cross_talk.csv', 'data/sim/phaseD/study4_results.json'}, ...
    'cross_talk_matlab', root, outRoot, rel, S);
end

function run_demo(fn, inputs, stem, root, outRoot, rel, S)
tmp = tempname; mkdir(tmp);
cleanup = onCleanup(@() rmdir(tmp, 's'));
for k = 1:numel(inputs)
    copyfile(fullfile(root, inputs{k}), tmp);
end
fn(tmp, tmp, S);
target = fullfile(outRoot, rel);
if ~isfolder(fileparts(target)), mkdir(fileparts(target)); end
movefile(fullfile(tmp, [stem '.pdf']), [target '.pdf']);
movefile(fullfile(tmp, [stem '.png']), [target '.png']);
end

function trigger_timing(root, outRoot, rel, S)
% Input: trigger_timing.csv (saved per-actuator crossings from study3_results.json).
T = readtable(fullfile(root, 'data/sim/summary/trigger_timing.csv'));
n = height(T);
y = (n:-1:1)';
fig = sar_fig(17.4, 6.2);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
ax = nexttile(tl); hold(ax, 'on');
for i = 1:n
    plot(ax, [T.budget_violation_life(i) T.trigger_life(i)], [y(i) y(i)], '-', 'Color', S.c.stem, 'LineWidth', 1.4);
end
plot(ax, T.budget_violation_life, y, '^', 'MarkerSize', 6, 'MarkerFaceColor', S.c.orange, 'MarkerEdgeColor', S.c.orange);
plot(ax, T.trigger_life, y, 'd', 'MarkerSize', 6, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
text(ax, T.budget_violation_life(1) - 0.02, y(1) + 0.45, 'budget crossing', 'Color', S.c.orange, ...
    'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
text(ax, T.trigger_life(1) + 0.02, y(1) + 0.45, 'trigger', 'Color', S.c.blue, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'middle');
labels = arrayfun(@(a) sprintf('Actuator %d', a), T.actuator_id, 'UniformOutput', false);
set(ax, 'YTick', flipud(y), 'YTickLabel', flipud(labels), 'YLim', [0.4 n + 0.9], 'XLim', [0 1], 'XTick', 0:0.2:1);
try
    ax.YAxis.Color = 'none'; ax.YAxis.TickLabelColor = S.c.ink;
catch
end
xlabel(ax, 'Normalized life (fraction)');
sar_letter(ax, 'a', S);

bx = nexttile(tl); hold(bx, 'on');
xline(bx, 0, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
for i = 1:n
    plot(bx, [0 T.lead_life(i)], [y(i) y(i)], '-', 'Color', S.c.stem, 'LineWidth', 1.4);
end
late = T.lead_life < 0;
plot(bx, T.lead_life(late), y(late), 'd', 'MarkerSize', 6, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.1);
plot(bx, T.lead_life(~late), y(~late), 'd', 'MarkerSize', 6, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
text(bx, 0.004, n + 0.55, 'zero lead', 'Color', S.c.grey, 'FontSize', S.size.note, 'VerticalAlignment', 'middle');
text(bx, -0.345, n + 0.55, 'hollow: trigger after the crossing', 'Color', S.c.ink, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'middle');
set(bx, 'YTick', [], 'YLim', [0.4 n + 0.9], 'XLim', [-0.35 0.05], 'XTick', -0.3:0.1:0);
bx.YAxis.Color = 'none';
xlabel(bx, 'Budget crossing $-$ trigger (life fraction)');
sar_letter(bx, 'b', S);
sar_save(fig, outRoot, rel);
end
