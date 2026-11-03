function make_policy_graph(dataDir, outDir, S)
%MAKE_POLICY_GRAPH Redraw soft-actuator-recalibration policy_comparison.
%   Inputs: policy_comparison.csv (five policies) and the error budget from
%   matched_clock_audit.json. Panel a: mean pose RMSE as a lollipop from 0.
%   Panel b: calibrations per actuator as bars from 0. Rows are shared, so
%   one set of policy names serves both panels. Fill and colour both encode
%   budget status (filled blue = within, hollow orange = over).

T = readtable(fullfile(dataDir, 'policy_comparison.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
audit = jsondecode(fileread(fullfile(dataDir, 'matched_clock_audit.json')));
budget = audit.budget_mm;

n = height(T);
y = (n:-1:1)';                       % first CSV row at the top
rmse = T.mean_pose_rmse_mm;
cals = T.recalibrations_per_actuator;
within = rmse <= budget;
names = replace(T.label, "τ = 0.05", "$\tau = 0.05$");

fig = figure('Visible', 'off', 'Units', 'centimeters', 'Position', [2 2 17.4 6.4]);
tl = tiledlayout(fig, 1, 5, 'TileSpacing', 'compact', 'Padding', 'compact');

% ---- a: error -------------------------------------------------------------
ax = nexttile(tl, [1 3]); hold(ax, 'on');
for i = 1:n
    plot(ax, [0 rmse(i)], [y(i) y(i)], '-', 'Color', S.c.stem, 'LineWidth', 1.4);
end
hIn  = plot(ax, rmse(within),  y(within),  'o', 'MarkerSize', 6, ...
    'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue, 'LineStyle', 'none');
hOut = plot(ax, rmse(~within), y(~within), 'o', 'MarkerSize', 6, 'LineWidth', 1.2, ...
    'MarkerFaceColor', 'w', 'MarkerEdgeColor', S.c.orange, 'LineStyle', 'none');
xline(ax, budget, '--', 'Color', S.c.grey, 'LineWidth', 0.8);
text(ax, budget + 0.006, n + 0.55, sprintf('error budget %.3f mm', budget), ...
    'FontSize', S.size.note, 'Color', S.c.ink, 'VerticalAlignment', 'middle');

% headline: the matched-cost clock and the trigger tie (annotated in panel b)
tie = find(T.policy == "clock_2400" | T.policy == "trigger");
assert(numel(tie) == 2 && abs(diff(rmse(tie))) < 1e-12 && abs(diff(cals(tie))) < 1e-12, ...
    'expected the matched-cost clock and the P-V trigger to tie');

set(ax, 'YTick', flipud(y), 'YTickLabel', flipud(names), 'YLim', [0.4 n + 0.9], ...
    'XLim', [0 0.45], 'XTick', 0:0.1:0.4);
hide_y_spine(ax, S);
xlabel(ax, 'Mean pose RMSE (mm)');
legend(ax, [hIn hOut], {'within budget', 'over budget'}, 'Location', 'southeast', ...
    'Box', 'off', 'FontSize', S.size.note);
panel_letter(ax, 'a', S);

% ---- b: cost --------------------------------------------------------------
bx = nexttile(tl, [1 2]); hold(bx, 'on');
h = 0.28;
for x = 1:5
    plot(bx, [x x], [0.4 n + 0.5], '-', 'Color', [0.92 0.92 0.92], 'LineWidth', 0.5);
end
for i = 1:n
    if within(i)
        patch(bx, [0 cals(i) cals(i) 0], y(i) + [-h -h h h], S.c.blue, 'EdgeColor', S.c.blue);
    else
        patch(bx, [0 cals(i) cals(i) 0], y(i) + [-h -h h h], 'w', 'EdgeColor', S.c.orange, 'LineWidth', 1.1);
    end
end
% tie bracket to the right of the two equal bars
xb = max(cals(tie)) + 0.15;
y0 = min(y(tie)); y1 = max(y(tie));
plot(bx, [xb xb], [y0 y1], '-', 'Color', S.c.ink, 'LineWidth', 0.7);
plot(bx, [xb-0.08 xb], [y0 y0], '-', 'Color', S.c.ink, 'LineWidth', 0.7);
plot(bx, [xb-0.08 xb], [y1 y1], '-', 'Color', S.c.ink, 'LineWidth', 0.7);
text(bx, xb + 0.12, mean([y0 y1]), {sprintf('tie: %.3f mm', rmse(tie(1))), ...
    sprintf('at %.1f calibrations', cals(tie(1)))}, ...
    'FontSize', S.size.note, 'Color', S.c.ink, 'VerticalAlignment', 'middle');

set(bx, 'YTick', [], 'YLim', [0.4 n + 0.9], 'XLim', [0 5.4], 'XTick', 0:5);
bx.YAxis.Color = 'none';
xlabel(bx, 'Calibrations per actuator');
text(bx, 5.4, n + 0.55, 'left is better in both panels', 'HorizontalAlignment', 'right', ...
    'FontSize', S.size.note, 'Color', S.c.grey);
panel_letter(bx, 'b', S);

export_pair(fig, fullfile(outDir, 'policy_comparison_matlab'));
end

function hide_y_spine(ax, S)
% Hide the y spine and ticks but keep the policy names readable. Older
% releases without ruler TickLabelColor keep a normal y axis instead.
try
    ax.YAxis.TickLabelColor = S.c.ink;
    ax.YAxis.Color = 'none';
    ax.YAxis.TickLabelColor = S.c.ink;
catch
    ax.YAxis.Color = S.c.ink;
end
end

function panel_letter(ax, L, S)
% The letter is the axes title, so tiledlayout reserves space for it and
% exportgraphics does not crop it.
title(ax, ['\textbf{' L '}'], 'FontSize', S.size.letter, 'FontWeight', 'normal');
ax.TitleHorizontalAlignment = 'left';
end


