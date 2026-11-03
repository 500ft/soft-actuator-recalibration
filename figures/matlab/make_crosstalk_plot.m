function make_crosstalk_plot(dataDir, outDir, S)
%MAKE_CROSSTALK_PLOT Redraw soft-actuator-recalibration cross_talk.
%   Inputs: cross_talk.csv (28-point one-at-a-time sweep) and, from
%   study4_results.json, the default-network coupling and the supply
%   multipliers at which cross-talk reaches 10 % and 20 %. Series are
%   labelled directly; the two crossings and the default are the only notes.

T = readtable(fullfile(dataDir, 'cross_talk.csv'));
R = jsondecode(fileread(fullfile(dataDir, 'study4_results.json')));
m  = T.multiplier;
rs = 100 * T.R_s_coupling_ratio;
cm = 100 * T.C_m_coupling_ratio;
def = 100 * R.default_coupling;
lev = 100 * R.thresholds(:)';                          % [10 20]
xs  = [R.softness_multiplier_at_threshold.R_s.x0_10, ...
       R.softness_multiplier_at_threshold.R_s.x0_20];

% check the stored crossings against the plotted curve (log-x interpolation)
xi = exp(interp1(rs, log(m), lev));
assert(all(abs(xi ./ xs - 1) < 0.02), 'stored crossings disagree with cross_talk.csv');

fig = figure('Visible', 'off', 'Units', 'centimeters', 'Position', [2 2 11.5 7.2]);
ax = axes(fig); hold(ax, 'on');
set(ax, 'XScale', 'log', 'XLim', [0.23 34], 'YLim', [0 44], ...
    'XTick', [0.25 0.5 1 2 4 8 16 32], ...
    'XTickLabel', {'0.25', '0.5', '1', '2', '4', '8', '16', '32'}, 'YTick', 0:10:40);

for k = 1:numel(lev)
    yline(ax, lev(k), ':', 'Color', S.c.grey, 'LineWidth', 0.8);
end
text(ax, 0.245, lev(2) + 1.3, 'reference levels', 'FontSize', S.size.note, 'Color', S.c.grey);

plot(ax, m, cm, '--', 'Color', S.c.orange, 'LineWidth', 1.3);
plot(ax, m, rs, '-',  'Color', S.c.blue, 'LineWidth', 1.6);
plot(ax, m, cm, 's', 'MarkerSize', 3, 'MarkerFaceColor', S.c.orange, 'MarkerEdgeColor', 'none');
plot(ax, m, rs, 'o', 'MarkerSize', 3, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', 'none');

% direct series labels, coloured like their lines
text(ax, 9.5, interp1(m, rs, 9.5) + 3.8, 'supply resistance $R_s$', ...
    'Color', S.c.blue, 'FontSize', S.size.label, 'HorizontalAlignment', 'right');
text(ax, 32, cm(end) + 2.2, 'manifold compliance $C_m$', ...
    'Color', S.c.orange, 'FontSize', S.size.label, 'HorizontalAlignment', 'right');

% crossings of the reference levels by the supply-resistance curve:
% marked on the curve, labelled above the level line, left of the crossing
for k = 1:numel(lev)
    plot(ax, xs(k), lev(k), 'o', 'MarkerSize', 5, 'MarkerFaceColor', 'w', ...
        'MarkerEdgeColor', S.c.blue, 'LineWidth', 1.0);
    text(ax, xs(k) / 1.12, lev(k) + 0.7, sprintf('%.0f\\%% at %.1f$\\times$', lev(k), xs(k)), ...
        'FontSize', S.size.note, 'Color', S.c.ink, 'HorizontalAlignment', 'right', ...
        'VerticalAlignment', 'bottom');
end

% default network, labelled in the empty space below-right of the marker
plot(ax, 1, def, 'd', 'MarkerSize', 6, 'MarkerFaceColor', S.c.ink, 'MarkerEdgeColor', 'w');
text(ax, 1.12, def - 2.4, sprintf('default network, %.1f\\%%', def), ...
    'FontSize', S.size.note, 'Color', S.c.ink, 'VerticalAlignment', 'middle');

xlabel(ax, 'Varied parameter / default value (log scale)');
ylabel(ax, 'Cross-talk: neighbour / driven amplitude (\%)');
export_pair(fig, fullfile(outDir, 'cross_talk_matlab'));
end
