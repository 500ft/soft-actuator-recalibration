# Revision Plan — frozen preprint v1.3 and v2 (RoboSoft package)

> **2026-08-03 update:** `preprint-v1.3` and its Zenodo payload remain frozen.
> The original Wave-B sequence below is retained as history, but the canonical v2
> claim boundary and execution scope now live in:
>
> - `docs/reviews/novelty-evidence-audit-2026-08-03.md`
> - `docs/specs/robosoft-v2/claim-spine.md`
> - `docs/specs/robosoft-v2/scope.md`
> - `docs/specs/robosoft-v2/manuscript-outline.md`
>
> The new ordering fixes actuator-cluster inference and causal specificity before
> densifying the life grid. More traces from the same generator are not treated as
> stronger independent evidence.

_Written 2026-07-02, after the internal review that added the clock baseline,
the contact-F1 fix, and the §5 falsifiability bullet. This plan sequences the
remaining improvements into two waves with explicit gates. Wave A blocks the
arXiv upload; Wave B is the RoboSoft-deadline package and does NOT block it._

## Ground rules (apply to every item)

- Every number that appears in the manuscript is re-verified against the
  study JSONs after any dataset or study change (`data/sim/phaseD/*.json`).
- `python -m pytest` green before any commit; new analysis gets new tests.
- PDF re-rendered after any text edit through the safe route only, with an explicit
  source and an output outside the archive:
  `python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/day4/preprint_v1_4_candidate.pdf`.
  Rendering prepares a review copy; it does not update `docs/preprint_v1.pdf` (refused as an
  output, hash-verified before and after) and confers no approval. Route and its tests:
  [renderer evidence](../evidence/task-2026-09-12/README.md).
- The 5-stage dataset and its committed results stay untouched until Wave B
  deliberately supersedes them — Wave A adds analysis, it does not regenerate.
- **Execute from updated `main`.** The owner's local checkout sits on
  `codex/phase-c-health-indicators` at `b45d162`, 5 commits behind origin/main
  (which carries the merged preprint, SUBMISSION.md, and this plan). Fix
  before touching anything locally:
  `git checkout main && git pull` (the codex branch is fully merged; safe to
  delete or leave).

---

## Wave A.2 — post-audit corrections (~half a session; blocks the upload)

_Added 2026-07-03 after the independent audit of commit `6c538d4`; **FINALIZED
2026-07-03 after owner review** — this section is now the implementation spec.
The Wave A execution was verified correct (code, tests, CI, spine left frozen,
downgrade propagated). The audit found the negative-lead story is told too
bleakly and one uniformity in the results is reported without being decoded._

### FINAL implementation spec (supersedes the item prose below where they differ)

**Hard rules (owner-confirmed):**
- The title stays "health indicator". The frontier proves temporal lead is
  threshold-dependent — that is not a title-level "leading indicator" claim.
- Deployed policy frozen: `TAU_GRID`, `tau_selected = 0.05`, the §4.5 policy
  table, recal counts, T\*, and all budget claims stay byte-identical.
  `check_manuscript_numbers.py` (already asserting them) is the guard.
- `result_spine.md` stays frozen.

**Step 1 — `lead_frontier_heldout` (descriptive sweep, `run_study3.py`).**
`FRONTIER_TAUS = (0.005, 0.01, 0.02, 0.03, 0.04, 0.05)`. Per τ, on held-out
actuators only (no training involvement, no selection):
```
{tau, trigger_life_median,
 lead_life: {median, min, max}, lead_cycles: {min, max},
 recal_per_actuator, mean_pose_rmse_mm,
 budget_met,            # EXPLICITLY the §4.5 metric: mean held-out
                        # realized pose RMSE <= accuracy_budget_mm
 n_positive_lead, n_nonpositive_lead, status_counts}
```
`n_positive/nonpositive` per τ is mandatory so the frontier cannot hide
per-actuator failures (read-only check indicates τ=0.02 has 1/6 nonpositive).

**Step 2 — free correctness invariants (assert in
`check_manuscript_numbers.py`, they cost nothing and catch implementation
bugs):**
- The τ=0.05 frontier row must equal the deployed §4.5 triggered row exactly
  (same code path ⇒ same numbers).
- The τ=0.005 row must equal the always-on row exactly (per-stage health
  growth ≈0.0077 > 0.005 ⇒ fires every stage ⇒ identical schedule).
Also assert every frontier number quoted in §4.4 against the JSON.

**Step 3 — uniformity test + wording.** Test: normalized `health_trajectory`
for two *different* actuator parameter draws agrees within a measured
tolerance (implementer measures the true max deviation and asserts the
tightest defensible bound, e.g. `atol=1e-9`; do **not** use `array_equal`
unless it actually holds). Manuscript prose says "identical to numerical
precision" / "effectively identical" — never "bitwise". The conceptual point
to land: normalized health is a generator-level life-fraction signal, not
independent per-actuator evidence.

**Step 4 — manuscript §4.4 rewrite (three beats).** (a) Negative lead at the
deployed fewest-recal threshold — existing numbers unchanged. (b) The
frontier: lead is purchasable but not free. Expected values from the owner's
read-only check — **quote final numbers only from the committed JSON after
Step 1, not from this plan**:
- τ=0.005: trigger ≈0.23, median lead ≈+0.476, 5 recals (= always-on cost), ≈0.019 mm
- τ=0.01: trigger ≈0.36, median lead ≈+0.346 [≈+0.199, +0.354], 3 recals, ≈0.029 mm
- τ=0.02: trigger ≈0.62, median lead ≈+0.085 but 1/6 nonpositive, 3 recals, ≈0.037 mm
- τ=0.05 (deployed): trigger 0.83, median lead −0.123, 2 recals, 0.058 mm
(c) Why the deployed point fires late: τ\*=0.05 is ~77% of the signal's 6.5%
full-scale life-growth. Fig. 3 caption gains the frontier clause. §4.4's
per-actuator-r sentence rewritten per Step 3's conceptual point; §4.5 gains
the normalized-life-sensor clause; §5 falsifiability bullet gains the
health-signal-has-no-scatter clause.

**Step 5 — abstract + §1.** "three findings, including a negative one" →
"four findings, including two negative/audit results" (or cleaner equivalent
counting: cross-talk null · drift dominance · health indicator + frontier ·
recalibration trade-off). §1 gains the pre-specification sentence: the
temporal-lead expectation was pre-specified, audited, and downgraded under
the paper's own rules.

**Step 6 — wrap as v1.2.** Re-render PDF (status block → Draft v1.2);
`python -m scripts.check_manuscript_numbers` + pytest + CI green; push; then
sync Progress repo README/PLAN and session memory so no external text still
says unconditional "leading indicator"; then the owner uploads per
`docs/SUBMISSION.md`.

_Original item prose (A2.1–A2.4) retained below for rationale:_

**Executed 2026-07-03.** The descriptive frontier is stored in
`lead_frontier_heldout`; τ\*=0.05 remains the deployed policy, τ=0.005 is
identical to always-on, and §4.4 now reports that lead is purchasable but not
free. Draft v1.2 keeps the health-indicator title, decodes normalized-health
uniformity as a generator property, and leaves `docs/result_spine.md` frozen.

### A2.1 The lead-vs-recalibration frontier (core item)

**Why.** The health signal's full dynamic range over life is only **6.5%
growth** (hn: 1.0 → 1.065), and `TAU_GRID` steps by 0.05 — so the sweep
evaluated nothing between "recalibrate every stage" (τ=0) and "fire at life
0.83" (τ\*=0.05, i.e. 77% of the signal's full scale). Verified from the
committed data: **τ=0.01 triggers at life 0.36 — positive lead of +0.20 to
+0.35 against every held-out budget crossing — at ~3 recals/actuator (still
40% fewer than always-on).** The fair statement is a *frontier* (lead is
purchasable with sensitivity), not "no positive lead."

**How — without touching any deployed number.**
1. Do **NOT** refine the selection grid. τ\* = 0.05 and every §4.5 number
   stay exactly as committed (a finer selection grid would shift τ\* to ~0.06
   with byte-identical policy behavior — pure number churn). The frontier is
   a **separate, descriptive sweep**.
2. New frontier computation in `run_study3.py`: for τ ∈ {0.005, 0.01, 0.02,
   0.03, 0.04, 0.05}, on held-out actuators report: interpolated
   trigger_life, lead stats (reusing `lead_time`), discrete-policy recal
   count, realized error, budget met (yes/no). Store as
   `lead_frontier_heldout` in `study3_results.json`. No selection, no
   training involvement — it is a characterization of the deployed signal,
   like study 4 was for cross-talk.
3. Manuscript §4.4, second paragraph reframed: (a) negative lead at the
   deployed fewest-recal threshold, with the existing numbers; (b) the
   frontier — sensitivity buys lead, quantified at 2–3 τ points; (c) why the
   deployed point sits late: τ\* is 77% of the signal's 6.5% full-scale
   range. Fig. 3 caption gains the frontier clause. **Title and headline stay
   "health indicator"** — lead being configuration-dependent is exactly why
   the unconditional "leading" claim stays retired.
4. Tests: frontier monotonicity (smaller τ → earlier trigger, ≥ recals);
   `check_manuscript_numbers.py` asserts the frontier numbers quoted in §4.4.
5. Honesty guard: if any frontier point that leads also **violates** the
   budget on held-out, report it as-is — no cherry-picking the τ list.

### A2.2 Decode the per-actuator uniformity

**Why.** `trigger_life` = 0.829 for all six actuators and per-actuator r in
[0.9570, 0.9574] are not coincidence: **hn is bitwise-identical across
actuators** (verified — the young-normalization cancels every per-actuator
parameter; the fatigue state depends only on life fraction). The manuscript
currently reports the 4-decimal-tight range as if it were evidence; a
reviewer will decode it and read naivety.

**How.**
1. Test asserting the property (two different actuator parameter sets →
   identical hn), documenting it as a known generator property.
2. §4.4: rewrite the per-actuator sentence — the near-uniform per-actuator r
   *follows from* the generator producing a single normalized degradation
   trajectory, adds no independent evidence, and counts toward the
   single-generator caveat.
3. §4.5 gains one clause: within this generator the P-V trigger is
   effectively a normalized-life sensor — which is precisely why it beats
   the absolute-cycle clock.
4. §5 falsifiability bullet: per-actuator scatter did not materialize in the
   health signal (deterministic in life fraction); scatter lives in the error
   trajectories' scale.

### A2.3 Abstract / §1 consistency

- "three findings, including a negative one" → count honestly: two negative
  results (cross-talk second-order; no positive lead at the deployed
  threshold) alongside the drift-dominance and health-indicator findings.
- §1: one clause claiming the credit that is due — the temporal-lead
  expectation was pre-specified in the spine, audited, and downgraded when
  the audit failed it. Pre-specification working as intended.

### A2.4 Wrap

- Re-render PDF as Draft v1.2; `check_manuscript_numbers` + pytest + CI
  green; push.
- Update Progress repo (README/PLAN still say "leading indicator") and the
  session memory in the same round.
- Explicit non-goals: do NOT retitle back toward "leading indicator"; do NOT
  touch `result_spine.md`; do NOT refine the *selection* grid.
- Then the owner uploads per `docs/SUBMISSION.md`.

---

## Wave A — before the arXiv upload (~half a day, all from existing data)

**Executed 2026-07-03.** A1/A2 were added from the existing 5-stage data; the
lead-time audit found no positive temporal lead under the deployed τ\*=0.05
threshold (6/6 held-out actuators nonpositive), so the manuscript wording was
downgraded from "leading indicator" to "health indicator" where temporal lead
was implied. A3/A4/A5 were completed with the v1.1 manuscript/PDF, number-check
script, and CI workflow.

### A1. Quantify the lead time (closes the "leading vs correlated" gap) — HIGHEST VALUE

**Why.** §2 promises a "cycle-resolved leading indicator with *quantified lead
behavior*"; §4.4 delivers a pooled same-stage correlation, which is symmetric
in time and demonstrates no lead. This is the strongest remaining referee
attack and it is answerable from existing data.

**Crossing definitions (fixed here so the code has no latitude):**
- *Trigger crossing* = the first life fraction where the fractional loop-area
  growth **from the young calibration** exceeds the policy's actual
  train-selected τ\* — i.e., exactly when the triggered policy takes its first
  recalibration. Not a re-derived threshold; the deployed one.
- *Budget crossing* = the first life fraction where the **young/fixed-
  calibration** pose error (`err[i][0]`) exceeds `accuracy_budget_mm`. This is
  the clean "indicator leads degradation" comparison: both trajectories start
  from the same young state and neither is contaminated by recalibration.

**How.**
1. New function in `pipeline/coupling.py`:
   `lead_time(health_norm, errors_fixed_cal, tau, budget_mm, life_fractions)`
   with crossings linearly interpolated between the 5 stages (state the
   interpolation honestly; the stage grid bounds resolution at ±0.1 life).
2. In `scripts/run_study3.py`: compute for the 6 held-out actuators; store
   **raw per-actuator records, not just summaries** —
   `lead_time_heldout: {per_actuator: [{actuator_id, rupture_cycles,
   trigger_life, budget_violation_life, lead_life, lead_cycles, status}],
   median_lead_life, min, max, n_excluded}` where `status` ∈
   {`ok`, `never_triggers`, `never_violates`, `nonpositive_lead`} and
   `lead_cycles = lead_life × rupture_cycles` (per-actuator, not median-life
   converted). Excluded statuses are counted, never silently dropped.
3. Manuscript §4.4: one added sentence + inline numbers — "the trigger fires at
   life X.XX [range] while the budget is violated at X.XX [range]; median lead
   ≈ X.X of normalized life (≈N–M cycles across the held-out rupture lives)".
   If any actuator shows `nonpositive_lead`, report it — that IS the result.
4. Tests: synthetic monotone health/error arrays with a known crossing gap;
   each degenerate status; interpolation correctness at an exact stage hit.

**Gate:** the word "leading" in the abstract/§2/§4.4 is backed by a reported
lead statistic, or the wording is downgraded. Either outcome closes the item.

### A2. Per-actuator correlations beside the pooled r

**Why.** Pooled r = 0.885 mixes within-actuator life trends with
across-actuator scatter (ecological-correlation objection).

**How.** In `run_study3.py`, compute Pearson r per held-out actuator (5 points
each) on (loop-area growth, fixed-cal error); store
`per_actuator_r: {values, median, min, max}`. Manuscript §4.4: one sentence,
**deliberately modest** — 5 points per actuator shows the within-actuator
*structure* is consistent with the pooled result; it cannot support strong
per-actuator inference and the sentence must not imply it. No per-actuator CIs
(they would be meaningless at n=5); just the six values' median and range.
Test: per-actuator r of a constructed dataset with one deviant actuator.

**Gate:** §4.4 reports both pooled and per-actuator statistics with the small-n
caveat inline.

### A3. "Pre-registered" → "pre-specified" (2 occurrences: lines ~81, ~339)

**Why.** The spine was frozen in-repo (self-specification), not externally
registered; the term invites a pointless fight.

**How.** Replace both with "pre-specified (frozen in `docs/result_spine.md`,
commit `d856455`, before result write-up)". **Precision note:** `d856455` adds
both the spine and the dataset generator/artifacts, so git alone cannot prove
"before dataset generation" — do not claim it. "Before result write-up" is
what the history does prove (the spine predates the study results and the
preprint commits) and is the part that matters for the pre-specification
claim. Keep the claim's substance; drop the loaded term and the unprovable
ordering.

**Gate:** `grep -c "pre-registered" docs/preprint_v1.md` returns 0, and the
replacement claims only git-provable ordering.

### A4. Kill the test-count drift (and the drift class)

**Why.** Three documents currently state three different test counts —
manuscript §7 says 125, `SUBMISSION.md` says 129, the suite is at 131. Nobody
lied; the counts were each true when written. Hardcoded volatile numbers in
prose are the bug.

**How.**
1. Remove exact test counts from *prose*: manuscript §7 → "the full unit-test
   suite gates the pipeline (count and status in CI)"; `SUBMISSION.md`
   pre-upload check → "`python -m pytest` fully green" with no number.
   Exact counts stay in commit messages, where they are timestamped claims.
2. New `scripts/check_manuscript_numbers.py`: asserts every load-bearing
   manuscript number against the study JSONs — r + CI bounds, the four-policy
   table values, τ\*, T\*, budget, and (after A1/A2) the lead and per-actuator
   figures. Exits nonzero on any mismatch. This automates the SUBMISSION.md
   verification step instead of trusting a human to re-grep.
3. Minimal CI (`.github/workflows/ci.yml`): pytest + the number-check script
   on push/PR. The repo currently has **no CI at all** — every "N tests pass"
   claim so far has been a local, unrepeated assertion. MechAudit's workflow
   is the in-portfolio template.

**Gate:** `check_manuscript_numbers.py` passes; CI green on main; no volatile
count remains in prose.

### A5. Wave-A wrap

- Re-render PDF; bump the status block to "Draft v1.1 (2026-07-0X)".
- Run `scripts/check_manuscript_numbers.py` as the verification step (A4).
- Commit, push, confirm CI green, then the owner uploads per
  `docs/SUBMISSION.md` — from **updated main**, not the stale codex branch.

---

## Wave B — the RoboSoft package (2–4 sessions; does not block arXiv)

Do these only when the RoboSoft deadline is real. Order matters: B1 first (it
changes no committed numbers), then B2 (which changes ALL of them), then B3–B4.

### B1. Study 5 — probe-robustness sweep (highest-value new experiment)

**Why.** §5 now *argues* that probe noise/quantization could have degraded r;
the natural referee follow-up is "so where does it die?" A sweep converts the
qualitative defense into an operating envelope — the same move study 4 made
for the cross-talk null.

**How.** New `scripts/run_study5.py`: hold the dataset fixed; recompute the
*observable* health trajectory under swept probe conditions — sensor-noise
multiplier ×{0.5, 1, 2, 4, 8}, quantization step ×{1, 2, 4}, drive amplitude
`amplitude_frac` ∈ {0.05, 0.1, 0.2} (`pv_loop_area` already parameterizes
amplitude; noise/quantization enter via the sensor model applied to the probe
signal — small extension to `pipeline/coupling.py`, seeded). For each
condition: pooled held-out r + CI, and whether the τ\*-triggered policy still
meets the budget. One figure (r vs condition, budget-pass shading) → Fig. 6;
one results JSON; tests for the probe-corruption path.

**Gate:** the manuscript can state "the indicator survives probe noise up to
×N and dies at ×M" with a figure behind it.

### B2. Densify life stages: 5 → 9 (regenerates the dataset — all numbers move)

**Entry condition (hard):** a real, dated RoboSoft deadline exists and the
decision to submit has been taken. 9 stages is scientifically better, but
after arXiv v1 is public every regeneration creates version-management
overhead (two citable number sets, an errata-shaped diff to explain). Without
an active venue deadline the cost is not worth paying — B1, B3 and even B4
are all doable against the 5-stage build.

**Why.** Five stages integer-quantizes recal counts, the clock comparison, and
the A1 lead statistic (±0.1 life). Nine stages ({0.1..0.9} step 0.1) roughly
halves the quantization at pure compute cost (2,000 → 3,600 traces).

**How.** `LIFE_FRACTIONS` in `scripts/phaseD_dataset.py` and `LIFE` in
`run_study2/3.py`; regenerate (deterministic, new manifest `npz_sha256`);
rerun studies 2, 3, 5; re-verify EVERY manuscript number (abstract r, CI,
policy table, τ\*, T\*, lead times, per-actuator r); regenerate Figs 1–4 and 6.
**Risk:** headline drift — if r or the policy ordering shifts materially,
report the new numbers and note the stage-count sensitivity; do not cherry-pick
the grid that looks better. Keep the 5-stage v1.1 numbers quotable via the
arXiv v1 record.

**Gate:** full re-verification checklist in `SUBMISSION.md` passes on the
9-stage build; a manuscript footnote states the stage-grid change from v1.

### B3. Orientation error metric

**Why.** Evaluation is tip-position only; PCC yields full SE(3); soft-robotics
reviewers ask by default.

**How.** `pcc_transform` already returns the rotation; add geodesic
orientation error (angle of R_predᵀR_true) to `pose_rmse`-style evaluation in
studies 2–3; report alongside position in Fig. 2 and the §4.5 table (or a
compact appendix table if it clutters). Tests: known curvature pairs → known
angle.

**Gate:** every place position RMSE is reported, orientation RMSE is available
(inline or appendix), and the §2 conventions sentence is updated to match —
no repeat of the F1 inconsistency.

### B4. IEEE two-column reflow (owner + Overleaf)

**Why.** RoboSoft requires ieeeconf LaTeX; the reportlab render is
arXiv-adequate only.

**How.** Owner creates an Overleaf ieeeconf project; port section-by-section
from `preprint_v1.md` (it is already IEEE-shaped: abstract/intro/related/
methods/results/discussion/conclusion/refs); figures drop in as the committed
vector PDFs (`data/sim/phaseD/*.pdf`); references have DOIs ready for BibTeX.
Expect a length pass — RoboSoft is 6+references; §3 phase summaries and §5
bullets are the compression targets. No local toolchain exists for this; it
cannot be automated here.

**Gate:** compiled ieeeconf PDF within page budget, numbers identical to the
9-stage build.

### Explicitly NOT in scope (decided, recorded)

Contact-state estimator (new scope; honestly descoped in §2) · additional
corrector architectures (Phase E settled it) · hardware anchor (separate
campaign, trigger-gated on lab access — see `ROADMAP.md`) · figure styling
beyond a budget line on Fig. 4.

---

## Sequence summary

| Wave | Items | Effort | Blocks |
|---|---|---|---|
| A | A1 lead time · A2 per-actuator r · A3 wording · A4 number/CI hygiene · A5 wrap | ~½ day | arXiv upload |
| B | B1 probe sweep → B2 9-stage regen (**only under an active RoboSoft deadline**) → B3 orientation → B4 IEEE reflow | 2–4 sessions + owner Overleaf | RoboSoft submission |

_Revised 2026-07-03 after owner review: A1 raw per-actuator schema + explicit
crossing definitions; A2 modesty constraint; A3 git-provable wording only;
A4 added (test-count drift + number-check script + CI — the repo had none);
B2 hard-gated on an active deadline; execute-from-main note added._

---

## Wave A.3 — presentation hygiene before professor outreach / arXiv (owner review 2026-07-07)

_The manuscript's novelty framing is already correct (sim-only up front,
"health indicator" title, no first-P-V-for-fatigue claim, negative lead
admitted, cross-talk null retained). The remaining work is presentation
hygiene: the outward-facing artifact must not read like an internal note, and
the older working docs must not overclaim relative to the downgraded v1.2._

### Governing principle (do not violate)

**Banners, not rewrites, for historical docs.** The proposal, report, and
early drafts were written *before* the v1.2 downgrade and genuinely predicted a
"leading indicator" with "positive lead time." That prediction, made and then
honestly downgraded under the project's own pre-registration, is the core of
the paper's credibility. Rewriting those bodies to say "health indicator" would
be revisionist and would erase the audit trail. **`docs/result_spine.md` stays
FROZEN** (it says "Edit only with a dated note"; its "leading indicator"
language is the pre-specified target that was downgraded — it MUST remain as
the record). Historical docs get a one-line SUPERSEDED banner pointing at the
preprint; their bodies are left intact.

### A3.1 — Remove the internal status block from the manuscript (the only PDF edit)

- **Keep** the `**Status:** ... simulation-only modeling study ...` paragraph —
  that is honest framing arXiv wants.
- **Delete** the entire `**Venue & status (GO decision taken 2026-07-02).**`
  paragraph — "delegated portfolio review", "an unshipped finished preprint
  loses value", "remaining action is the mechanical upload by the owner" are
  internal project-management notes that make the paper look like a memo. All of
  that already lives in `docs/SUBMISSION.md`.
- Re-render PDF; `check_pdf_arxiv` + `check_manuscript_numbers` + pytest + CI
  green; this supersedes the `preprint-v1.2` tag → cut `preprint-v1.3` on the
  new CI-green commit (arXiv v1 will carry v1.3; update §7 pin + SUBMISSION.md).

### A3.2 — Canonical one-sentence novelty claim (single source, quoted everywhere)

- Add a short `docs/NOVELTY.md` with exactly one sentence, owner-approved:
  > "This paper studies, in simulation, whether observable pressure-volume
  > loop-area drift can serve as a health signal for recalibrating pressure-only
  > proprioception in fatiguing shared-manifold soft pneumatic grippers."
- Point the README "Current Positioning" and the SUBMISSION metadata pack at it
  so there is one wording, not five. (Do NOT restate it inside the PDF — the
  abstract already carries the framing.)

### A3.3 — SUPERSEDED banners on the overclaiming working docs

One-line banner at the very top of each, body untouched:
> `> SUPERSEDED (2026-07-07): forward-looking working doc predating preprint`
> `> v1.3. Its "leading indicator"/"positive lead time" framing was a`
> `> pre-specified hypothesis; the simulation study found no positive lead at`
> `> the deployed threshold and reframed the contribution as a health`
> `> indicator. Authoritative current version: docs/preprint_v1.md.`

Apply to: `Proposal_A01_A04_Combined.md`, `report.md`, `paper_drafts.md`,
`Experimental_Protocol.md`. NOT to `result_spine.md` (frozen pre-registration),
NOT to the literature/gate docs (their "leading indicator" usages are
descriptions of prior art / viability, not claims about this study's result —
verify each before deciding, but default is leave).

### A3.4 — README front-door pass

- README already reframed to "health indicator" — good. Add the SUPERSEDED
  status to the `Proposal_A01_A04_Combined.md` bullet in the Repository Contents
  list so a browser lands correctly. Add a one-line "Start here: docs/preprint_v1.md
  (arXiv-ready v1.3)" pointer near the top.

### A3.5 — Professor-outreach framing note (not a claim about results)

- Add a short `docs/OUTREACH.md`: how to introduce the work to faculty — lead
  with "simulation preprint, reproducible pipeline, looking for a hardware
  validation collaboration", NOT "finished robotics result". Include the
  endorsement ask (per SUBMISSION.md Phase 0) since the natural endorser and a
  natural hardware-collaboration contact may be the same robotics professor.
  Reuse the canonical NOVELTY sentence.

### A3.6 — Wrap

- Re-render, all gates + CI green, tag `preprint-v1.3`, push tags.
- Sync Progress repo README/PLAN if any external text still cites v1.2.

### Non-goals (explicit)

- Do NOT rewrite the body of any historical doc to hide the original prediction.
- Do NOT edit `result_spine.md`.
- Do NOT add venue/submission prose back into the PDF.
- Do NOT change any result number (this wave is presentation only).
