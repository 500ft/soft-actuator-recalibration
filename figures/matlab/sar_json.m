function J = sar_json(path)
%SAR_JSON Read a result JSON. Python writes Infinity and NaN tokens, which
%   jsondecode does not accept; they are mapped to 1e999 (Inf) and null first.
txt = fileread(path);
txt = regexprep(txt, '-Infinity\>', '-1e999');
txt = regexprep(txt, 'Infinity\>', '1e999');
txt = regexprep(txt, '\<NaN\>', 'null');
J = jsondecode(txt);
end
