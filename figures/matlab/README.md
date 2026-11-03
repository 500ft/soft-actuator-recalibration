# MATLAB figures and tables

MATLAB R2025b draws every committed figure under `data/gate0/` and `data/sim/`, and
writes the two headline tables as LaTeX. Python keeps every computation: the study
scripts write the result JSON, the captions, and a CSV under `<study>/figdata/` for
each curve the JSON does not hold. MATLAB only reads those files.

## Regenerate

From the repository root:

```sh
matlab -batch "addpath('figures/matlab'); render_figures"   # 34 figures, PNG (300 dpi) + vector PDF
matlab -batch "addpath('figures/matlab'); render_tables"    # docs/tables/*.tex
```

`render_figures(root, outRoot, pattern)` writes under another folder or draws only
the paths that match a regular expression, for example
`render_figures([], 'out', 'phaseB')`. A failing figure is reported and the others
still run; the call ends with an error if any figure failed.

Typeset the table fragments with the figure kit's `tex/table2img.py` (Tectonic,
booktabs, siunitx):

```sh
python table2img.py docs/tables/policy_table.tex docs/tables/policy_table
python table2img.py docs/tables/gate0_table.tex docs/tables/gate0_table
```

To refresh the inputs first, run the `--replot` commands listed in
[docs/data-and-figures.md](../../docs/data-and-figures.md#redraw-every-figure).
None of them rewrites a result JSON.

## Files

- `render_figures.m`: entry point; one `figs_<study>.m` file per study.
- `render_tables.m`: policy and Gate 0 tables (booktabs + siunitx).
- `fig_style.m`, `export_pair.m`: the approved house style and the PNG/PDF writer.
- `make_policy_graph.m`, `make_crosstalk_plot.m`: the approved demo scripts for
  `policy_comparison` and `cross_talk`, run unchanged by `figs_summary.m`.
- `sar_*.m`: small helpers (JSON reading, panel letters, saving).
