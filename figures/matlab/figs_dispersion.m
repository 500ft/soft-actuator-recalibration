function F = figs_dispersion()
%FIGS_DISPERSION Dispersion audit (data/sim/dispersion_audit), from dispersion_audit.json.
F = {'data/sim/dispersion_audit/dispersion_audit_fig', @dispersion_audit};
end

function dispersion_audit(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/dispersion_audit/dispersion_audit.json'));
sw = R.B_transfer_sensitivity;
t = sar_list(sw.results);
cv = cellfun(@(x) x.rupture_cv, t);
nUnits = numel(sar_list(t{1}.per_unit));
target = 0.10; rule = 8;                       % Study C rule: run_dispersion_audit.PASS_RMSE, PASS_COUNT
refs = struct2cell(sw.measured_reference_values);
refs = [refs{:}];
series = {'a', 'mean_rmse',       'o', '-', S.c.blue,   'estimator'
          'a', 'mean_rmse_clock', 's', ':', S.c.orange, 'clock'
          'b', 'n_within_target', '^', '-', S.c.blue,   'within target'
          'b', 'n_beats_clock',   'd', ':', S.c.orange, 'beats clock'};
fig = sar_fig(17.4, 6.8);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'loose', 'Padding', 'compact');
axs = gobjects(1, 2);
for p = 1:2
    axs(p) = nexttile(tl); hold(axs(p), 'on');
    for v = refs
        xline(axs(p), v, '-', 'Color', [0.75 0.75 0.75], 'LineWidth', 0.5);
    end
end
yline(axs(1), target, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
yline(axs(2), rule, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
for k = 1:size(series, 1)
    ax = axs(1 + strcmp(series{k, 1}, 'b'));
    y = cellfun(@(x) x.(series{k, 2}), t);
    if series{k, 1} == 'a', meets = y <= target; else, meets = y >= rule; end
    plot(ax, cv, y, series{k, 4}, 'Color', series{k, 5}, 'LineWidth', 1.2);
    plot(ax, cv(meets), y(meets), series{k, 3}, 'MarkerSize', 6, 'MarkerFaceColor', series{k, 5}, 'MarkerEdgeColor', series{k, 5});
    plot(ax, cv(~meets), y(~meets), series{k, 3}, 'MarkerSize', 6, 'MarkerFaceColor', 'w', ...
        'MarkerEdgeColor', series{k, 5}, 'LineWidth', 1.1);
    text(ax, cv(end) + 0.012, y(end), series{k, 6}, 'Color', series{k, 5}, 'FontSize', S.size.note, ...
        'VerticalAlignment', 'middle');
end
text(axs(1), 0.005, target + 0.003, sprintf('target %.2f', target), 'Color', S.c.grey, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'bottom');
text(axs(2), 0.005, rule + 0.25, sprintf('rule: %d of %d', rule, nUnits), 'Color', S.c.grey, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'bottom');
text(axs(1), max(refs) + 0.006, 0.134, 'published CVs', 'Color', [0.55 0.55 0.55], 'FontSize', S.size.tick, ...
    'VerticalAlignment', 'top');
for p = 1:2
    set(axs(p), 'XTick', cv, 'XTickLabel', arrayfun(@(v) sprintf('%.2f', v), cv, 'UniformOutput', false), 'XLim', [0 0.37]);
    xlabel(axs(p), 'Assumed rupture-life CV');
    sar_letter(axs(p), char('a' + p - 1), S);
end
set(axs(1), 'YLim', [0 0.14]);
ylabel(axs(1), 'Mean held-out life-estimate RMSE (life)');
set(axs(2), 'YLim', [0 nUnits + 0.5], 'YTick', 0:2:nUnits);
ylabel(axs(2), sprintf('Held-out units (of %d)', nUnits));
sar_save(fig, outRoot, rel);
end
