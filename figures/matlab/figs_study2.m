function F = figs_study2()
%FIGS_STUDY2 Study 2 drift and corrector figures (data/sim/phaseD), from study2_results.json.
F = {'data/sim/phaseD/study2_fig1_drift',             @drift
     'data/sim/phaseD/study2_fig2_static_vs_dynamic', @corrector};
end

function drift(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/phaseD/study2_results.json'));
A = R.experimentA_static_drift_over_life;
life = A.life_fractions(:); sh = A.shared(:); iso = A.isolated(:);
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
plot(ax, life, iso, '--s', 'Color', S.c.orange, 'MarkerSize', 7, 'MarkerFaceColor', 'w', 'LineWidth', 1.1);
plot(ax, life, sh, '-o', 'Color', S.c.blue, 'MarkerSize', 4, 'MarkerFaceColor', S.c.blue, 'LineWidth', 1.2);
top = max([sh; iso]) * 1.08;
text(ax, 0.05, 0.95, 'isolated supply (hollow squares)', 'Units', 'normalized', 'Color', S.c.orange, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'top');
text(ax, 0.05, 0.86, 'shared manifold (filled circles)', 'Units', 'normalized', 'Color', S.c.blue, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'top');
set(ax, 'XTick', life, 'XLim', [life(1) - 0.05, life(end) + 0.05], 'YLim', [0 top]);
xlabel(ax, 'Normalized life');
ylabel(ax, 'Curvature RMSE (m$^{-1}$)');
sar_save(fig, outRoot, rel);
end

function corrector(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/phaseD/study2_results.json'));
B = R.experimentB_static_vs_dynamic_young_to_old;
topo = {'isolated', 'shared'}; names = {'Isolated supply', 'Shared manifold'};
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
w = 0.34; top = 0;
for i = 1:2
    st = B.(topo{i}).static_kappa_rmse; dy = B.(topo{i}).dynamic_kappa_rmse;
    patch(ax, i - w + [0 w w 0] - 0.01, [0 0 st st], 'w', 'EdgeColor', S.c.orange, 'LineWidth', 1.1);
    patch(ax, i + [0 w w 0] + 0.01, [0 0 dy dy], S.c.blue, 'EdgeColor', S.c.blue);
    top = max(top, st);
end
hA = patch(ax, NaN, NaN, 'w', 'EdgeColor', S.c.orange, 'LineWidth', 1.1);
hB = patch(ax, NaN, NaN, S.c.blue, 'EdgeColor', S.c.blue);
set(ax, 'XTick', 1:2, 'XTickLabel', names, 'XLim', [0.4 2.6], 'YLim', [0 top * 1.25], 'TickLength', [0 0.012]);
ylabel(ax, 'Curvature RMSE (m$^{-1}$)');
legend(ax, [hA hB], {'static ridge', sprintf('dynamic, %d lags', R.n_lags)}, 'Location', 'north', ...
    'Orientation', 'horizontal', 'Box', 'off', 'FontSize', S.size.note);
sar_save(fig, outRoot, rel);
end
