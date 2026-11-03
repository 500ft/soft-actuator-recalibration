function fig = sar_fig(w, h)
%SAR_FIG Invisible figure of W x H centimetres.
fig = figure('Visible', 'off', 'Units', 'centimeters', 'Position', [2 2 w h]);
end
