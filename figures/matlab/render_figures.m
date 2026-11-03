function render_figures(root, outRoot, only)
%RENDER_FIGURES Draw every committed study figure from committed data.
%   render_figures()                 repository root found from this file; writes in place
%   render_figures(root, outRoot)    read inputs under ROOT, write images under OUTROOT
%   render_figures(root, outRoot, pattern)   only figures whose path matches the regexp
%
%   Each figure is written as <path>.png (300 dpi) and <path>.pdf (vector) at the
%   path the docs reference. Inputs are the result JSON files and, where a curve is
%   not stored there, the CSV under <study>/figdata/ written by the Python study
%   script. Nothing here computes a result. One failed figure does not stop the
%   others; the run ends with an error if any figure failed.
%
%   Run from the repository root:  matlab -batch "addpath('figures/matlab'); render_figures"

if nargin < 1 || isempty(root)
    root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
end
if nargin < 2 || isempty(outRoot), outRoot = root; end
if nargin < 3, only = ''; end

S = fig_style();
groups = {@figs_gate0, @figs_phaseA, @figs_phaseB, @figs_study1, @figs_study2, @figs_study3, ...
          @figs_study4, @figs_studyA, @figs_studyB, @figs_studyC, @figs_dispersion, @figs_summary};
nOk = 0; failed = {};
for g = 1:numel(groups)
    F = groups{g}();
    for k = 1:size(F, 1)
        rel = F{k, 1};
        if ~isempty(only) && isempty(regexp(rel, only, 'once')), continue; end
        try
            F{k, 2}(root, outRoot, rel, S);
            fprintf('OK   %s\n', rel);
            nOk = nOk + 1;
        catch err
            fprintf('FAIL %s: %s\n', rel, err.message);
            if ~isempty(err.stack)
                fprintf('     at %s line %d\n', err.stack(1).name, err.stack(1).line);
            end
            failed{end + 1} = rel; %#ok<AGROW>
            close all force
        end
    end
end
fprintf('%d figures written, %d failed\n', nOk, numel(failed));
if ~isempty(failed)
    error('render_figures:failed', '%d figure(s) failed', numel(failed));
end
end
