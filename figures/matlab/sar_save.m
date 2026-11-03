function sar_save(fig, outRoot, rel)
%SAR_SAVE Write <outRoot>/<rel>.pdf (vector) and .png (300 dpi) and close the figure.
target = fullfile(outRoot, rel);
d = fileparts(target);
if ~isfolder(d), mkdir(d); end
true_minus(fig);
export_pair(fig, target);
end

function true_minus(fig)
% Auto tick labels print a hyphen for negative values; set them in math mode.
for cb = reshape(findall(fig, 'Type', 'colorbar'), 1, [])
    if strcmp(cb.TickLabelsMode, 'auto')
        lab = cellstr(cb.TickLabels);
        neg = startsWith(lab, '-');
        lab(neg) = cellfun(@(t) ['$-' t(2:end) '$'], lab(neg), 'UniformOutput', false);
        cb.TickLabels = lab;
    end
end
for ax = reshape(findall(fig, 'Type', 'axes'), 1, [])
    for name = {'XAxis', 'YAxis'}
        r = ax.(name{1});
        if ~isa(r, 'matlab.graphics.axis.decorator.NumericRuler') || ~strcmp(r.TickLabelsMode, 'auto')
            continue
        end
        lab = cellstr(r.TickLabels);
        if ~any(startsWith(lab, '-')), continue; end
        for k = 1:numel(lab)
            if startsWith(lab{k}, '-'), lab{k} = ['$-' lab{k}(2:end) '$']; end
        end
        r.TickLabels = lab;
    end
end
end
