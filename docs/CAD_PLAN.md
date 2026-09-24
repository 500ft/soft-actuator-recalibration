# P-V-Fatigue-Manifold-Proprioception — revised CAD work orders

For the plain-language list of physical parts and assemblies, see [CAD_ITEMS.md](CAD_ITEMS.md). It maps to the existing work orders without adding tasks, estimates or completion status.

Amended 2026-09-06 after source review. Planning only: no CAD, fixture, fabrication or calibration result exists from this amendment.

**Main-branch placement authorized — 2026-09-06 (America/New_York).** The owner explicitly requested merging these PRs to their respective main branches. This supersedes the earlier placement hold for this PR's current documents and prerequisite integrity changes; it is not a blanket policy for future private material. Hardware, measurement and disclosure gates remain unchanged. See [CAD_REVIEW_DISPOSITION.md](CAD_REVIEW_DISPOSITION.md).

[CAD_TASKS.csv](CAD_TASKS.csv) is the sole CAD status ledger. [SPRINT_TASKS.csv](SPRINT_TASKS.csv) remains byte-preserved for the earlier integrity sprint. [Scope tiers](specs/cad-development/scope.md) and [reproduction checks](CAD_PLAN_CHECKS.md) describe this amendment, not physical validation.

## Verified source context

The physical protocol calls for cast actuators, volumetric drive and independent pose measurement but does not decompose the apparatus CAD. The newer prospective integrity core makes hardware optional. The older protocol's leading-indicator and guaranteed-result language is not evidence or the v2 claim contract.

Inspected source documents:

- [docs/Experimental_Protocol.md](Experimental_Protocol.md)
- [docs/specs/v2-integrity-core/design.md](specs/v2-integrity-core/design.md)


## Revised finish line and priority

Entire CAD branch parked until manuscript decisions and explicit owner election. One reused specimen is the conditional finish line; no N=10 campaign or new mold development.

## Tool and verification decision

**Reusable tooling reference, 2026-09-21.** Before planning CAD or FEA, also read
[CAD_PLANNING_ADDENDUM_2026-09-21.txt](CAD_PLANNING_ADDENDUM_2026-09-21.txt). It maps documented
CAD machinery in `500ft/engineering-audit` (pinned revision `cf56cdf`) onto the work orders below
and sets a minimum acceptance workflow and FEA limits. It is a planning reference only: it selects
no tooling, proves no host access, and leaves every task below `deferred`. If a SOLIDWORKS host is
chosen at activation, amend the selection below through PV-CAD-08 rather than silently.

**Unattended-host requirement, recorded 2026-09-23 (owner).** The CAD host has no monitor — a GPU only —
so nothing may wait on a human to accept a dimension, confirm a rebuild or dismiss a prompt. Two parts, and
only the first is currently met:

- *Met.* `cadloop`'s host-side scripts already set `sw.Visible = False`, so SOLIDWORKS runs without a
  visible window and needs no display for normal operation.
- **Not met.** Running invisibly is not the same as raising no dialogs. A modal prompt — a rebuild error, a
  missing reference, a units mismatch, a "document was saved in a different version" notice — can still
  block a COM call with no one to dismiss it, and the job would hang rather than fail. Neither
  `docs/host_setup.md` nor `docs/solidworks_api_findings.md` in the tooling repository documents dialog
  suppression or a hang timeout.

So PV-CAD-08 acquires two acceptance conditions before any project part is authored on the host: every job
must run to a recorded verdict with no interactive input, and a job that stalls must **time out and report**
rather than wait. A successful launch is not a completed build, and a hung job must not be silently counted
as one. This is a requirement note; it selects no tooling and proves no host access.

**Selected design approach:** CadQuery code-CAD for parameterized families and neutral STEP verification; Onshape for hand-modeled fixtures with confirmed owner account/access. No Onshape automation, credentials or paid access is assumed. Agent owns code-CAD generators/tests; Owner or an authorized CAD operator owns interactive Onshape work. Lack of Onshape access blocks only affected fixture modeling and requires a documented alternative, not the entire parameter pipeline.

The dedicated tooling task budgets environment locking and CI setup. Pin actual Python/CadQuery/OCP versions only after a clean isolated install plus STEP export/reimport smoke test. No version, environment or geometry CI is claimed tested today. CadQuery's official [installation](https://cadquery.readthedocs.io/en/stable/installation.html) and [STEP import/export](https://cadquery.readthedocs.io/en/stable/importexport.html) docs establish the chosen workflow, not a completed build.

Required future automated sequence: read reviewed parameters.csv → reject invalid/missing dimensions and units → regenerate native geometry → export STEP → reimport into a fresh process → calculate geometric metrics → assert against predeclared tolerances. Geometry acceptance uses numeric JSON plus source/export identity; retain screenshots only for explanatory views. A golden image or a hash is not a geometry test. Tests include analytic nominal cases, registered bounds and invalid cases; expected values cannot be copied from the candidate's own output. CAD geometry tests do not validate physical stiffness, safety or fatigue.

Proposed commands (files DO NOT exist yet): `python cad/generate.py --parameters <registered-parameters.csv> --output <temporary-output>`; `python -m pytest cad/tests -q`. The tooling task must replace placeholders with actual checked-in defaults and wire CI before a model task can close.

## Rebaselined allocation

**0 estimated hours in the prioritized phase; 18 estimated hours parked.** This supersedes the previous CAD allocation, not the original 30-hour software sprint. Only tasks marked todo are executable now; blocked/parked estimates are not scheduled work. Owner decisions, fabrication lead times and external calibration do not shrink into focused hours.

| Workload day | Hours | Order |
| --- | ---: | --- |
| Parked | 0 active | Owner/research entry decision required |

## Individual work orders

IDs retain continuity with the first PR. New IDs represent split inputs, tooling or release tasks; display order is execution priority rather than numerical ID order. Proposed deliverables below are NEW, not present artifacts. Current status exists only in CAD_TASKS.csv.

### PV-CAD-02 — Confirm pilot access, reference geometry and fabrication method

- Owner: Owner; priority: P2; estimate: 2 h; day: conditional.
- Dependencies: none.
- Proposed output: `NEW cad/pilot/owner-inputs.md`.
- Done when: Resolve manuscript/publication decisions first; explicitly elect a ONE-specimen feasibility pilot using an existing released mold/specimen, volumetric drive and pose apparatus. New mold development and N=10 campaign are OUT; if reuse is unavailable stop and rescope.
- Verification/evidence: Owner signs dated decisions and availability references; identify material/process, operator and laboratory approval still needed.

### PV-CAD-01 — Reconcile physical-pilot geometry and measurement requirements

- Owner: Agent; priority: P2; estimate: 2 h; day: conditional.
- Dependencies: PV-CAD-02.
- Proposed output: `NEW cad/pilot/requirements.md; cad/pilot/parameters.csv`.
- Done when: Separate chamber volume from syringe displacement, tubing dead volume, gas compressibility and leaks; identify critical geometry, camera accuracy and pressure limits as sourced values or unresolved inputs. Map each fixture to an observable endpoint, not a health claim.
- Verification/evidence: Review against both source documents; retain a requirement-to-part table with units and unresolved decisions.

### PV-CAD-08 — Establish code-CAD regeneration and CI geometry tests

- Owner: Agent; priority: P2; estimate: 3 h; day: conditional.
- Dependencies: PV-CAD-01.
- Proposed output: `NEW cad/requirements.lock; cad/generate.py; cad/tests/; .github/workflows/cad-geometry.yml`.
- Done when: Use CadQuery for parameter-driven families and neutral STEP checks, Onshape for hand-modeled fixtures after confirming account/access. Pin Python/CadQuery/OCP dependencies after a clean isolated install and export/reimport smoke test. Add geometry CI before accepting a parametric model; screenshots are supplementary, not acceptance.
- Verification/evidence: Proposed commands, NOT YET IMPLEMENTED: python cad/generate.py --parameters <registered-parameters.csv> --output <temporary-output>; python -m pytest cad/tests -q. Assert geometry metrics against a reviewed contract with declared tolerances; prove failure on an altered parameter, invalid dimensions, missing inputs and bad STEP. Retain version lock, numeric JSON and STEP outputs.

### PV-CAD-03 — Verify reused specimen/mold geometry and wall bounds

- Owner: Agent; priority: P2; estimate: 3 h; day: conditional.
- Dependencies: PV-CAD-01;PV-CAD-08.
- Proposed output: `NEW cad/pilot/mold/ (editable source, STEP, drawings)`.
- Done when: Version authorized existing mold/specimen geometry and make only the verification representation for wall thickness, chamber volume and fits. No new mold-production campaign; unavailable source means rescope.
- Verification/evidence: Regenerate reviewed wall bounds from parameters.csv, export/reimport STEP and assert positive walls, chamber/solid volume and analytic limits in CI. Invalid walls, missing inputs and units must fail.

### PV-CAD-04 — Model specimen base and pneumatic-routing fixture

- Owner: Agent; priority: P2; estimate: 2 h; day: conditional.
- Dependencies: PV-CAD-01;PV-CAD-08.
- Proposed output: `NEW cad/pilot/specimen-fixture/ (source, STEP, assembly drawing)`.
- Done when: Define repeatable clamping without crushing active chambers, pressure tee locations, strain relief and traceable tubing lengths. Preserve free/contact operating modes selected by the pilot; no fixture contact in the measured motion envelope.
- Verification/evidence: Review assembly mates, full motion clearance and hose routing; retain interference and nominal/dead-volume inventory.

### PV-CAD-05 — Model volumetric-drive mounting and calibration interfaces

- Owner: Agent; priority: P2; estimate: 2 h; day: conditional.
- Dependencies: PV-CAD-01;PV-CAD-08.
- Proposed output: `NEW cad/pilot/volume-drive/ (source, STEP, dimensioned assembly)`.
- Done when: Reference the selected commercial drive or model syringe restraints, plunger alignment, travel stops and pinch-zone shielding for a custom drive. Record stroke-to-displacement calibration interface; syringe displacement must not be labeled direct chamber volume.
- Verification/evidence: Check full travel and connector access; produce an error-source diagram covering compliance and gas/tubing effects; qualified review remains necessary before pressurization.

### PV-CAD-06 — Model independent pose target and camera/calibration fixture

- Owner: Agent; priority: P2; estimate: 2 h; day: conditional.
- Dependencies: PV-CAD-02;PV-CAD-04.
- Proposed output: `NEW cad/pilot/pose-fixture/ (source, STEP, views)`.
- Done when: Define marker/target attachment, sensor coordinate frame, scale reference and camera or mocap clearance. Quantify added target mass from sourced density and note potential perturbation of actuator pose.
- Verification/evidence: Retain field-of-view and full-motion checks plus target mass calculation; physical pose accuracy is deferred to calibration.

### PV-CAD-07 — Release a reproducible pilot CAD and fabrication-review packet

- Owner: Agent; priority: P2; estimate: 2 h; day: conditional.
- Dependencies: PV-CAD-03;PV-CAD-04;PV-CAD-05;PV-CAD-06.
- Proposed output: `NEW cad/pilot/release/ (BOM, drawings, export manifest, inspection checklist)`.
- Done when: Publish editable/version-pinned source, STEP solids, fabrication drawings, dimensions/material/process notes, supplier references, assembly and section visuals. Proposed assets remain labeled CAD/design-only; pressure-test permission and calibration are separate gates.
- Verification/evidence: Second operator reopens exported geometry and checks units, dimensions, part count and assembly fit against source. Retain hashes and review issues; no build approval from this task alone.

## Stop and release rules

Do not equate prepared drawings with fabricated/inspected apparatus. Unknown fit-critical dimensions block manufacture. Owner/facility review, actual metrology and prospective reference freezes remain separate gates. No spending, manufacture, pressurization, rotor operation, flight, publication or new third-party drawing disclosure is authorized here.

If time overruns, cut decorative views and already-parked variants first. Keep reference controls, fit/clearance tests, source provenance, filled measurement budgets and pre-load model freeze. Update estimates explicitly rather than claiming blocked hours as progress. Every future public visual needs a source/version, problem explained and CAD-only label.
