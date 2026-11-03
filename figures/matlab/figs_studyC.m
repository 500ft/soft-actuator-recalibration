function F = figs_studyC()
%FIGS_STUDYC Study C transfer and failure-map figures (data/sim/studyC).
F = {'data/sim/studyC/studyC_fig_transfer',    @transfer
     'data/sim/studyC/studyC_fig_failure_map', @failure_map};
end

function transfer(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/studyC/studyC_results.json'));
H = sar_list(R.heldout);
r = cellfun(@(h) h.rmse, H); rc = cellfun(@(h) h.rmse_clock, H);
ids = R.test_units(:)';
target = 0.10;                                 % preregistered life target, run_studyC.PASS_RMSE
dodge = 0.14;
n = numel(r); i = 1:n;
fig = sar_fig(13.5, 6.8);
ax = axes(fig); hold(ax, 'on');
yline(ax, target, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
for k = i
    plot(ax, [k - dodge, k + dodge], [r(k) rc(k)], '-', 'Color', S.c.stem, 'LineWidth', 0.9);
end
mark(ax, i + dodge, rc, 's', S.c.orange, rc <= target);
hE = mark(ax, i - dodge, r, 'o', S.c.blue, r <= target);
hC = plot(ax, NaN, NaN, 's', 'MarkerSize', 5.5, 'MarkerFaceColor', S.c.orange, 'MarkerEdgeColor', S.c.orange);
text(ax, 0.5, target + 0.006, sprintf('target %.2f', target), 'Color', S.c.grey, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'bottom');
set(ax, 'XTick', i, 'XTickLabel', arrayfun(@(v) sprintf('%d', v), ids, 'UniformOutput', false), ...
    'XLim', [0.4 n + 0.6], 'YLim', [0 max([r rc]) * 1.1], 'TickLength', [0 0.012]);
xlabel(ax, 'Held-out unit');
ylabel(ax, 'Life-estimate RMSE (life)');
legend(ax, [hE(1) hC], {'pressure features + clock', 'clock only'}, 'Location', 'northeast', ...
    'Box', 'off', 'FontSize', S.size.note);
sar_save(fig, outRoot, rel);
end

function h = mark(ax, x, y, m, col, filled)
h = gobjects(0);
if any(filled)
    h(end + 1) = plot(ax, x(filled), y(filled), m, 'MarkerSize', 5.5, 'MarkerFaceColor', col, 'MarkerEdgeColor', col);
end
if any(~filled)
    h(end + 1) = plot(ax, x(~filled), y(~filled), m, 'MarkerSize', 5.5, 'MarkerFaceColor', 'w', ...
        'MarkerEdgeColor', col, 'LineWidth', 1.1);
end
end

function failure_map(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/studyC/studyC_failure_analysis.json'));
U = sar_list(R.per_unit);
y = cellfun(@(u) u.rmse, U);
ok = cellfun(@(u) logical(u.within_target), U);
xs = {cellfun(@(u) u.n_post_onset, U), cellfun(@(u) u.rupture_deviation_from_training_median, U)};
labs = {'Post-onset probes (count)', 'Rupture-life distance from training median (fraction)'};
target = 0.10;
fig = sar_fig(17.4, 6.6);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
yl = [0.015, max(y) + 0.08 * (max(y) - 0.015)];
for p = 1:2
    ax = nexttile(tl); hold(ax, 'on');
    yline(ax, target, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
    x = xs{p};
    plot(ax, x(ok), y(ok), 'o', 'MarkerSize', 5.5, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
    plot(ax, x(~ok), y(~ok), 'o', 'MarkerSize', 5.5, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.1);
    span = max(x) - min(x);
    set(ax, 'XLim', [min(x) - 0.08 * span, max(x) + 0.08 * span], 'YLim', yl);
    xlabel(ax, labs{p});
    if p == 1
        ylabel(ax, 'Held-out life-estimate RMSE (life)');
        text(ax, max(x) + 0.06 * span, target + 0.004, sprintf('target %.2f', target), 'Color', S.c.grey, ...
            'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
        text(ax, max(x) + 0.06 * span, yl(2), {'filled: within target', 'hollow: misses target'}, ...
            'FontSize', S.size.note, 'Color', S.c.ink, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
    else
        ax.YTickLabel = {};
    end
    sar_letter(ax, char('a' + p - 1), S);
end
sar_save(fig, outRoot, rel);
end
