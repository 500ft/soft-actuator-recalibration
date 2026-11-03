function F = figs_studyB()
%FIGS_STUDYB Study B identifiability figures (data/sim/studyB).
F = {'data/sim/studyB/studyB_fig_identifiability_map', @identifiability_map
     'data/sim/studyB/studyB_fig_structural',          @structural};
end

function identifiability_map(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/studyB/studyB_results.json'));
pts = sar_list(R.points);
u = R.u_grid(:)'; amps = R.amplitude_fracs(:)';
canon = cellfun(@(p) string(p.unit) == "canonical" && p.noise_scale == 1.0, pts);
pts = pts(canon);
pu = cellfun(@(p) p.u, pts); pa = cellfun(@(p) p.amp_frac, pts);
pick = @(key, amp) arrayfun(@(uu) pts{find(abs(pu - uu) < 1e-9 & abs(pa - amp) < 1e-9, 1)}.(key), u);
D = {'B1_sigma_u', 's', 'none', S.c.ink,    'B1 single snapshot'
     'B3_sigma_u', '^', '-.',   S.c.orange, 'B3 nuisance known'
     'B2_sigma_u', 'o', '-',    S.c.blue,   'B2 with young baseline'};
TOP = 1;                                      % infinite bounds are drawn at the top tick
fig = sar_fig(17.4, 7.2);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'loose', 'Padding', 'compact');
ax = nexttile(tl); hold(ax, 'on');
yline(ax, R.sigma_target, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
yline(ax, R.sigma_kill, ':', 'Color', S.c.grey, 'LineWidth', 0.9);
for k = 1:size(D, 1)
    y = pick(D{k, 1}, 0.1);
    fin = isfinite(y);
    if any(fin)
        if ~strcmp(D{k, 3}, 'none'), plot(ax, u(fin), y(fin), D{k, 3}, 'Color', D{k, 4}, 'LineWidth', 1.1); end
        plot(ax, u(fin), y(fin), D{k, 2}, 'MarkerSize', 4.5, 'MarkerFaceColor', D{k, 4}, 'MarkerEdgeColor', D{k, 4});
    end
    if any(~fin)
        plot(ax, u(~fin), TOP * ones(1, nnz(~fin)), D{k, 2}, 'MarkerSize', 6, 'MarkerFaceColor', 'w', ...
            'MarkerEdgeColor', D{k, 4}, 'LineWidth', 1.0, 'Clipping', 'off');
    end
end
b2 = pick('B2_sigma_u', 0.1); b3 = pick('B3_sigma_u', 0.1);
text(ax, u(1), b2(1) * 1.6, 'B2 with young baseline', 'Color', S.c.blue, 'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
text(ax, u(1), b3(1) / 1.6, 'B3 nuisance known', 'Color', S.c.orange, 'FontSize', S.size.note, 'VerticalAlignment', 'top');
text(ax, u(1), TOP / 1.5, 'B1 single snapshot: infinite (hollow)', 'Color', S.c.ink, 'FontSize', S.size.note, ...
    'VerticalAlignment', 'top');
text(ax, u(end), R.sigma_target / 1.15, sprintf('target %g', R.sigma_target), 'Color', S.c.grey, ...
    'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
text(ax, u(end), R.sigma_kill * 1.15, sprintf('kill %g', R.sigma_kill), 'Color', S.c.grey, ...
    'FontSize', S.size.note, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
set(ax, 'YScale', 'log', 'YLim', [1e-4 TOP], 'YTick', [1e-4 1e-3 1e-2 1e-1 1], ...
    'YTickLabel', {'$10^{-4}$', '$10^{-3}$', '$10^{-2}$', '$10^{-1}$', '$\infty$'}, 'YMinorTick', 'off', ...
    'XLim', [u(1) - 0.04, u(end) + 0.04]);
xlabel(ax, 'Normalized life $u$');
ylabel(ax, 'Cram\''er-Rao bound $\sigma_u$ (life)');
sar_letter(ax, 'a', S);

bx = nexttile(tl);
G = zeros(numel(amps), numel(u));
for i = 1:numel(amps), G(i, :) = pick('B2_sigma_u', amps(i)); end
L = log10(G); fin = isfinite(G);
L(~fin) = NaN;
im = imagesc(bx, u, 1:numel(amps), L);
set(im, 'AlphaData', double(fin));
set(bx, 'YDir', 'normal', 'Color', [0.89 0.89 0.89], 'TickLength', [0 0], 'Box', 'off');
colormap(bx, parula(256));
lim = [min(L(fin)) max(L(fin))];
clim(bx, lim);
for i = 1:numel(amps)
    for j = 1:numel(u)
        if fin(i, j)
            col = [1 1 1];
            if (L(i, j) - lim(1)) / diff(lim) > 0.55, col = S.c.ink; end
            text(bx, u(j), i, sprintf('%.2g', G(i, j) * 100), 'HorizontalAlignment', 'center', ...
                'VerticalAlignment', 'middle', 'FontSize', S.size.tick, 'Color', col);
        else
            text(bx, u(j), i, '$\infty$', 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                'FontSize', S.size.tick, 'Color', S.c.ink);
        end
    end
end
set(bx, 'XTick', u, 'XTickLabel', arrayfun(@(v) sprintf('%.1f', v), u, 'UniformOutput', false), ...
    'YTick', 1:numel(amps), 'YTickLabel', arrayfun(@(a) sprintf('$%g\\,V_0$', a), amps, 'UniformOutput', false));
bx.XAxis.Color = 'none'; bx.YAxis.Color = 'none';
try
    bx.XAxis.TickLabelColor = S.c.ink; bx.YAxis.TickLabelColor = S.c.ink;
catch
end
xlabel(bx, 'Normalized life $u$', 'Color', S.c.ink);
ylabel(bx, 'Probe amplitude', 'Color', S.c.ink);
cb = colorbar(bx);
ct = [0.015 0.02 0.03 0.04 0.06];
ct = ct(log10(ct) >= lim(1) & log10(ct) <= lim(2));
cb.Ticks = log10(ct);
cb.TickLabels = arrayfun(@(v) sprintf('%g', v * 100), ct, 'UniformOutput', false);
cb.TickLabelInterpreter = 'latex';
cb.FontSize = S.size.tick;
cb.Label.String = 'B2 bound $\sigma_u$ ($10^{-2}$ life)';
cb.Label.Interpreter = 'latex';
cb.Label.FontSize = S.size.label;
sar_letter(bx, 'b', S);
sar_save(fig, outRoot, rel);
end

function structural(root, outRoot, rel, S)
R = sar_json(fullfile(root, 'data/sim/studyB/studyB_structural.json'));
B = sar_json(fullfile(root, 'data/sim/phaseB/phaseB_results.json'));
onset = B.canonical_parameters.acceleration_onset_fraction;
poor = R.collinearity_summary.poor_flag;
CHI2 = 1.92;                                  % 95 % chi-square(1) cut, run_studyB_structural.CHI2_95
FLOOR = 1e-11;                                % profile values below this are drawn at the floor
PANEL_U = [0.5 0.9];
rowsK = {'u+onset+leak', 'life + onset + leak'; 'u+onset', 'life + onset'; 'u+leak', 'life + leak'; 'u+tau', 'life + $\tau$'};
cb = sar_list(R.collinearity_by_point);
cb = cb(cellfun(@(r) string(r.unit) == "canonical", cb));
[~, o] = sort(cellfun(@(r) r.u, cb)); cb = cb(o);

fig = sar_fig(17.4, 7.2);
tl = tiledlayout(fig, 1, 7, 'TileSpacing', 'compact', 'Padding', 'compact');
ax = nexttile(tl, [1 3]); hold(ax, 'on');
xline(ax, poor, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
n = size(rowsK, 1);
for y = 1:n
    yy = n - y + 1;
    for k = 1:numel(cb)
        r = cb{k};
        v = sar_f(r, rowsK{y, 1});
        if isempty(v), continue; end
        if r.u > onset
            plot(ax, v, yy, 'o', 'MarkerSize', 5, 'MarkerFaceColor', S.c.blue, 'MarkerEdgeColor', S.c.blue);
        else
            plot(ax, v, yy, 'o', 'MarkerSize', 8, 'MarkerFaceColor', 'none', 'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.0);
        end
    end
end
text(ax, poor * 1.4, n + 0.45, sprintf('$\\gamma_K = %g$', poor), 'Color', S.c.grey, 'FontSize', S.size.note);
text(ax, 2e4, 1.5, {'filled: after onset', 'hollow: before onset'}, 'FontSize', S.size.tick, 'Color', S.c.ink);
set(ax, 'XScale', 'log', 'XLim', [0.3 1e8], 'XTick', [1 1e2 1e4 1e6 1e8], ...
    'XTickLabel', {'1', '100', '$10^4$', '$10^6$', '$10^8$'}, 'XMinorTick', 'off', ...
    'YTick', 1:n, 'YTickLabel', flipud(rowsK(:, 2)), 'YLim', [0.5 n + 0.7]);
try
    ax.YAxis.Color = 'none'; ax.YAxis.TickLabelColor = S.c.ink;
catch
end
xlabel(ax, 'Brun collinearity index $\gamma_K$');
sar_letter(ax, 'a', S);

profs = sar_list(R.profiles);
style = struct('B1', {{'s', '-.', S.c.orange}}, 'B2', {{'o', '-', S.c.blue}});
for p = 1:2
    bx = nexttile(tl, [1 2]); hold(bx, 'on');
    if p == 2
        pp = profs{cellfun(@(q) string(q.design) == "B2" && abs(q.u_true - PANEL_U(2)) < 1e-9, profs)};
        pr = sar_list(pp.profile);
        uu = cellfun(@(q) q.u, pr); dn = cellfun(@(q) q.delta_nll, pr);
        flat = uu(dn <= CHI2 & uu >= pp.interval.u_at_minimum);
        fill(bx, [min(flat) max(flat) max(flat) min(flat)], [FLOOR / 3 FLOOR / 3 3e6 3e6], [0.9 0.9 0.9], 'EdgeColor', 'none');
    end
    for d = ["B1", "B2"]                          % B2 drawn last, so B1 is hidden where they coincide
        q = profs{cellfun(@(z) string(z.design) == d && abs(z.u_true - PANEL_U(p)) < 1e-9, profs)};
        pr = sar_list(q.profile);
        [uu, o] = sort(cellfun(@(z) z.u, pr)); pr = pr(o);
        dn = max(cellfun(@(z) z.delta_nll, pr), FLOOR);
        pinned = cellfun(@(z) isfield(z, 'at_bound') && any(z.at_bound), pr);
        st = style.(char(d));
        plot(bx, uu, dn, st{2}, 'Color', st{3}, 'LineWidth', 0.9);
        plot(bx, uu, dn, st{1}, 'MarkerSize', 2.8, 'MarkerFaceColor', st{3}, 'MarkerEdgeColor', st{3});
        if any(pinned)
            plot(bx, uu(pinned), dn(pinned), 'x', 'MarkerSize', 5, 'Color', S.c.ink, 'LineWidth', 0.9);
        end
    end
    xline(bx, PANEL_U(p), ':', 'Color', S.c.ink, 'LineWidth', 0.8);
    yline(bx, CHI2, '--', 'Color', S.c.grey, 'LineWidth', 0.9);
    set(bx, 'YScale', 'log', 'XLim', [0 1], 'YLim', [FLOOR / 3, 3e6], 'XTick', 0:0.2:1, ...
        'YTick', [1e-10 1e-6 1e-2 1e2 1e6], 'YMinorTick', 'off');
    if p == 1
        bx.YTickLabel = {'$10^{-10}$', '$10^{-6}$', '$10^{-2}$', '$10^{2}$', '$10^{6}$'};
        ylabel(bx, '$\Delta(-\log L)$');
        text(bx, 0.03, 3e4, 'B2', 'Color', S.c.blue, 'FontSize', S.size.note);
        text(bx, 0.03, 1e-4, 'B1', 'Color', S.c.orange, 'FontSize', S.size.note);
        text(bx, 0.03, 1e-6, {'$\times$: fit at', 'a nuisance', 'bound'}, 'Color', S.c.ink, 'FontSize', S.size.tick, 'VerticalAlignment', 'top');
    else
        bx.YTickLabel = {};
        text(bx, 0.03, 4, 'cut 1.92', 'Color', S.c.grey, 'FontSize', S.size.note, 'VerticalAlignment', 'bottom');
    end
    xlabel(bx, 'Normalized life $u$');
    sar_letter(bx, char('b' + p - 1), S, sprintf('true $u = %g$', PANEL_U(p)));
end
sar_save(fig, outRoot, rel);
end
