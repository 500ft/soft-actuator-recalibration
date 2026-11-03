function v = sar_num(x)
%SAR_NUM A decoded JSON number array as a column of doubles; null becomes NaN.
if iscell(x)
    v = nan(numel(x), 1);
    for i = 1:numel(x)
        if ~isempty(x{i}), v(i) = x{i}; end
    end
else
    v = double(x(:));
end
end
