# Guard passage and mounting-envelope CAD

This package records the executed nonpressure guard and mounting-envelope work.
It preserves the original parameter inputs, construction/oracle code, STEP/DXF
exports, check records and independent reviews. The successor experiment remains
open.

Read the delivered evidence with Python 3.9 or newer:

```sh
python check_guard_evidence.py
```

The reader uses only the standard library. It opens the ZIP in memory, checks its
explicit inventory and byte hashes, then reconciles the recorded statuses,
assertion counts, exported-file hashes, tensor arithmetic and raw expected-zero
rows. Its JSON output gives the current counts directly from the delivered
records. The [manifest](evidence_manifest.json) maps original source paths to
archive members; the reader never opens those original paths.

## What the archive contains

- `guard_candidate/`: the original executed guard, mounting and finite parameter
  study sources, specs and outputs, retaining their original hierarchy.
- `baseline_source/`: exact copies of the baseline geometry and CAD/oracle code
  referenced by those runs.
- `baseline_exports/`: the original frame/guard context and its clearance record.
- The actual independent concept-check reviews and raw expected-zero tensor CSV.

The original result JSON files are the source of consequential numbers. The
panel pilot, DXF export, nominal mounting subsystem and finite parameter study
each state their executed scope. The nominal context keeps the two prior
cell/stud engagement-envelope occurrences visible. Parameter cases distinguish
made-part changes from changed reference geometry.

## Reproduction and limits

The archived runners and specs retain their original absolute host bindings.
They are historical executed sources, not a newly verified portable CAD replay.
No archived code is imported by the reader. Source hashes are rechecked when an
explicitly mapped source is shipped; references to unshipped historical files
are counted separately and are not presented as revalidated. The manifest pins
every shipped byte, including original line endings.

Checks establish geometric consistency for the concept panel, cable reservation
and provisional mounts. They establish neither selected extrusion fasteners,
sensor interfaces, guard containment nor a clear whole fixture. No native
SOLIDWORKS verification, frame FEA, physical measurement or pressure qualification
is represented by this delivery. No pressure part is rated or released, and no
physical work or purchase is authorized. The closed predecessor study is
unchanged. Independent Codex reviews are distinct from owner, Claude or
publication acceptance.

Scripts use the repository's [MIT License](../../../LICENSE). CAD, drawings and
documents use [CC BY 4.0](../../../LICENSE-docs), as recorded for `successor/`.
