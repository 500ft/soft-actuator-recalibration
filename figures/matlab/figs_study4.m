function F = figs_study4()
%FIGS_STUDY4 Study 4 network sensitivity (data/sim/phaseD), from study4_results.json.
F = {'data/sim/phaseD/study4_fig_crosstalk_sensitivity', @crosstalk_sensitivity};
end

function crosstalk_sensitivity(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/phaseD/study4_results.json'));
x = R.sweep_multiplier(:);
rs = 100 * R.coupling_vs_multiplier.R_s(:);
cm = 100 * R.coupling_vs_multiplier.C_m(:);
every = 1:2:numel(x);                        % markers on every second sweep point, as in the caption
fig = sar_fig(8.9, 7.0);
ax = axes(fig); hold(ax, 'on');
th = 100 * R.thresholds(:)';
for k = 1:numel(th)
    yline(ax, th(k), ':', 'Color', S.c.grey, 'LineWidth', 0.8);
end
text(ax, x(1), th(end) + 1.2, 'reference levels', 'Color', S.c.grey, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'bottom');
plot(ax, x, cm, '--', 'Color', S.c.orange, 'LineWidth', 1.2);
plot(ax, x(every), cm(every), 's', 'MarkerSize', 3.5, 'MarkerFaceColor', S.c.orange, 'MarkerEdgeColor', S.c.orange);
plot(ax, x, rs, '-', 'Color', S.c.blue, 'LineWidth', 1.4);
plot(ax, x(every), rs(every), 'o', 'MarkerSize', 3.5, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
plot(ax, 1, 100 * R.default_coupling, 'd', 'MarkerSize', 6.5, 'MarkerFaceColor', 'w', ...
    'MarkerEdgeColor', S.c.ink, 'LineWidth', 1.0);
text(ax, 1.12, 100 * R.default_coupling - 2.2, 'default network', 'Color', S.c.ink, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'middle');
text(ax, 9, interp1(x, rs, 9) + 3.5, 'supply resistance $R_s$', 'Color', S.c.blue, 'FontSize', S.size.label, ...
    'HorizontalAlignment', 'right');
text(ax, x(end), cm(end) + 2.4, 'manifold compliance $C_m$', 'Color', S.c.orange, 'FontSize', S.size.label, ...
    'HorizontalAlignment', 'right');
ticks = [0.25 0.5 1 2 4 8 16 32];
set(ax, 'XScale', 'log', 'XLim', [x(1) / 1.15, x(end) * 1.15], 'XTick', ticks, ...
    'XTickLabel', arrayfun(@(v) sprintf('%g', v), ticks, 'UniformOutput', false), 'XMinorTick', 'off', ...
    'YLim', [0, max(rs) * 1.08]);
xlabel(ax, 'Parameter / default value');
ylabel(ax, 'Neighbour / driven amplitude (\%)');
sar_save(fig, outRoot, rel);
end
