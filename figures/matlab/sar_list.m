function c = sar_list(x)
%SAR_LIST A decoded JSON array as a 1-by-n cell, whether jsondecode made a
%   struct array, a cell array or a numeric array.
if iscell(x)
    c = reshape(x, 1, []);
elseif isstruct(x)
    c = num2cell(reshape(x, 1, []));
else
    c = num2cell(reshape(x, 1, []));
end
end
