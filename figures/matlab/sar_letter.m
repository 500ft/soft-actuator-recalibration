function sar_letter(ax, L, S, extra)
%SAR_LETTER Panel letter as a left-aligned axes title (exportgraphics keeps it).
%   Optional EXTRA is a short condition label, set as a subtitle at annotation size.
if nargin < 4, extra = ''; end
if isempty(extra)
    title(ax, ['\textbf{' L '}'], 'FontSize', S.size.letter, 'FontWeight', 'normal');
else
    [~, st] = title(ax, ['\textbf{' L '}'], extra, 'FontSize', S.size.letter, 'FontWeight', 'normal');
    st.FontSize = S.size.note;
    st.Color = S.c.ink;
end
ax.TitleHorizontalAlignment = 'left';
end
