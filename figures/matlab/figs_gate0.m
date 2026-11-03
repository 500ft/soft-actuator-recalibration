function F = figs_gate0()
%FIGS_GATE0 Gate 0 lumped R-C figures (data/gate0).
F = {'data/gate0/fig_crosstalk_vs_freq',        @crosstalk_vs_freq
     'data/gate0/fig_dc_independence',          @dc_independence
     'data/gate0/fig_crosstalk_vs_compliance',  @crosstalk_vs_compliance};
end

function crosstalk_vs_freq(root, outRoot, rel, S)
% Inputs: figdata/fig_crosstalk_vs_freq.csv (curves) and gate0_results.json (actuation frequency).
T = readtable(fullfile(root, 'data/gate0/figdata/fig_crosstalk_vs_freq.csv'), 'VariableNamingRule', 'preserve');
R = sar_json(fullfile(root, 'data/gate0/gate0_results.json'));
f = T.freq_hz;
names = T.Properties.VariableNames;
rc = names(startsWith(names, 'ratio_c'));
ac = names(startsWith(names, 'abs_c'));
n = numel(rc);
C = sar_ramp(S.c.blue, n, 0.3);
fact = R.params.f_actuation_hz;

fig = sar_fig(17.4, 6.6);
tl = tiledlayout(fig, 1, 9, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(tl, 1, [1 4]); hold(ax, 'on');
xline(ax, fact, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
top = 0;
for k = 1:n
    y = 100 * T.(rc{k});
    plot(ax, f, y, '-', 'Color', C(k, :), 'LineWidth', 1.2);
    text(ax, f(end) * 1.3, y(end), [extractAfter(rc{k}, 'ratio_c') '${\times}$'], 'Color', C(k, :), ...
        'FontSize', S.size.note, 'VerticalAlignment', 'middle');
    top = max(top, max(y));
end
text(ax, f(end) * 1.3, top * 1.13, {'chamber-1', 'compliance'}, 'Color', S.c.ink, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
text(ax, fact * 1.15, top * 0.03, sprintf('%g Hz actuation', fact), 'Color', S.c.grey, ...
    'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
set(ax, 'XScale', 'log', 'XLim', [f(1) / 1.2, f(end) * 1.2], 'XTick', [0.01 0.1 1 10 100], ...
    'XTickLabel', {'0.01', '0.1', '1', '10', '100'}, 'YLim', [0, top * 1.3]);
xlabel(ax, 'Drive frequency (Hz)');
ylabel(ax, 'Relative cross-talk $|H_{21}/H_{11}|$ (\%)');
sar_letter(ax, 'a', S);

bx = nexttile(tl, 6, [1 4]); hold(bx, 'on');
xline(bx, fact, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
for k = 1:n
    plot(bx, f, T.(ac{k}), '-', 'Color', C(k, :), 'LineWidth', 1.2);
end
set(bx, 'XScale', 'log', 'YScale', 'log', 'XLim', [f(1) / 1.2, f(end) * 1.2], ...
    'XTick', [0.01 0.1 1 10 100], 'XTickLabel', {'0.01', '0.1', '1', '10', '100'}, ...
    'YLim', [2.5e10 9e11], 'YTick', [3e10 1e11 3e11], ...
    'YTickLabel', {'$3\times10^{10}$', '$10^{11}$', '$3\times10^{11}$'}, 'YMinorTick', 'off');
xlabel(bx, 'Drive frequency (Hz)');
ylabel(bx, 'Neighbour pressure $|H_{21}|$ (Pa per unit $\Delta g$)');
sar_letter(bx, 'b', S);
sar_save(fig, outRoot, rel);
end

function dc_independence(root, outRoot, rel, S)
% Input: figdata/fig_dc_independence.csv (3x3 static gain matrices, healthy and 2x compliance).
T = readtable(fullfile(root, 'data/gate0/figdata/fig_dc_independence.csv'), 'TextType', 'string');
cases = ["healthy", "fatigued"];
labels = {'healthy chamber 1', 'chamber-1 compliance $2{\times}$'};
G = cell(1, 2);
for c = 1:2
    sel = T(T.condition == cases(c), :);
    M = zeros(max(sel.pressure_row), max(sel.valve_col));
    M(sub2ind(size(M), sel.pressure_row, sel.valve_col)) = sel.dc_gain / 1e12;
    G{c} = M;
end
lim = max(abs([G{1}(:); G{2}(:)]));
m = 128;
t = linspace(0, 1, m)';
cmap = [1 - (1 - S.c.blue) .* flipud(t); 1 - (1 - S.c.orange) .* t];   % blue (negative) - white - orange

fig = sar_fig(13.5, 6.6);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for c = 1:2
    ax = nexttile(tl);
    imagesc(ax, G{c}, [-lim lim]);
    colormap(ax, cmap);
    axis(ax, 'image');
    n = size(G{c}, 1);
    set(ax, 'XTick', 1:n, 'YTick', 1:n, 'TickLength', [0 0], 'Box', 'off');
    ax.XAxis.Color = 'none'; ax.YAxis.Color = 'none';
    ax.XAxis.Label.Color = S.c.ink; ax.YAxis.Label.Color = S.c.ink;
    try
        ax.XAxis.TickLabelColor = S.c.ink; ax.YAxis.TickLabelColor = S.c.ink;
    catch
    end
    for r = 1:n
        for q = 1:n
            v = G{c}(r, q);
            col = S.c.ink;
            if abs(v) / lim >= 0.55, col = [1 1 1]; end
            text(ax, q, r, sprintf('$%s$', strrep(sprintf('%.3g', v), '-', '-')), ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                'FontSize', S.size.note, 'Color', col);
        end
    end
    xlabel(ax, 'Driven valve');
    if c == 1, ylabel(ax, 'Chamber pressure'); end
    sar_letter(ax, char('a' + c - 1), S, labels{c});
end
cb = colorbar(ax);
cb.Layout.Tile = 'east';
cb.TickLabelInterpreter = 'latex';
cb.FontSize = S.size.tick;
cb.Label.String = 'DC gain ($10^{12}$ Pa per unit $\Delta g$)';
cb.Label.Interpreter = 'latex';
cb.Label.FontSize = S.size.label;
sar_save(fig, outRoot, rel);
end

function crosstalk_vs_compliance(root, outRoot, rel, S)
% Input: gate0_results.json headline_metric.
R = sar_json(fullfile(root, 'data/gate0/gate0_results.json'));
hm = R.headline_metric;
x = hm.fatigue_levels(:);
y = 100 * hm.crosstalk_vs_fatigue(:);
fig = sar_fig(8.9, 6.4);
ax = axes(fig); hold(ax, 'on');
plot(ax, x, y, '-o', 'Color', S.c.blue, 'MarkerFaceColor', S.c.blue, 'MarkerSize', 4, 'LineWidth', 1.2);
pad = 0.06 * (max(y) - min(y));
set(ax, 'XLim', [0.94 2.06], 'XTick', 1:0.2:2, 'YLim', [min(y) - pad, max(y) + pad]);
xlabel(ax, 'Chamber-1 compliance (${\times}$ healthy)');
ylabel(ax, sprintf('Cross-talk at %g Hz (\\%%)', hm.actuation_freq_hz));
sar_save(fig, outRoot, rel);
end
