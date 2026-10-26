# Soft Actuator Recalibration

**When should a soft robot recalibrate?** This simulation study tests whether
changes in a pressure–volume (P-V) loop can guide recalibration as an actuator
ages. A P-V loop records pressure against volume during a probe cycle. The
simulator models 20 actuators; it contains no physical measurements. At the
same recalibration count, a cycle-count schedule matches the P-V trigger's
pose error exactly.

> **The v1.4 paper candidate is withdrawn.** The archived v1.3 manuscript overstated the
> method; see its [correction](docs/corrections/v1.3-methods-2026-09-05.md).
> The v1.4 candidate was withdrawn after the matched-cost comparison removed
> its main claim ([withdrawal note](docs/corrections/v1.4-withdrawn-2026-10-02.md)).
> The code and original results remain available. Maintenance theory also
> predicts the tie for units that share one degradation curve
> ([why the tie was expected](docs/corrections/v1.4-withdrawn-2026-10-02.md#why-the-tie-was-expected-2026-10-09)).

[![CI](https://github.com/500ft/soft-actuator-recalibration/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/500ft/soft-actuator-recalibration/actions/workflows/ci.yml)
[![Evidence: simulation only](https://img.shields.io/badge/evidence-simulation_only-475569)](docs/results.md)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](.github/workflows/ci.yml)

[Results](#results) · [Roadmap](ROADMAP.md) · [Quick start](#quick-start) ·
[Review record](docs/REVIEW_READY.md)

## About

Frequent recalibration reduces pose error but requires more calibration
events. The study simulates 20 actuators through five life stages (2,000
traces) and holds out entire actuators for testing. It compares an initial
calibration only, cycle-count schedules, a P-V threshold trigger and
recalibration at every stage.

The repository holds the pneumatic simulator, the fatigue and sensing models,
the pose estimators, the study scripts, and the results and figures they
produced.

## Results

![Saved simulation policy comparison: the matched-cost clock and P-V trigger have equal pose error and calibration count](data/sim/summary/policy_comparison.png)

Saved simulation point summaries for 6 held-out actuators; no uncertainty bars.
Panel (a) shows mean pose RMSE [mm] and panel (b) calibrations per actuator for
five policies, marked by shape: initial calibration only (circle), the
train-selected clock at 2,700 cycles (triangle), the matched-cost clock at
2,400 cycles (square), the P-V trigger at τ = 0.05 (diamond), calibration at every
stage (cross). Left is better in both panels. The dashed line in (a) is the
train-derived error budget, 0.159 mm. A filled marker means the policy is within
the budget; a hollow marker means it exceeds it: initial calibration only and
the train-selected clock at 2,700 cycles. At matched cost the clock ties the P-V
trigger: both reach 0.058 mm with 2.0 calibrations per actuator. Counts include
the initial calibration; error averages life stages, then actuators. Values: the
policy table and policy_comparison.csv. Sources: matched_clock_audit.json and
study3_results.json; no physical measurements.

[Caption file](data/sim/summary/policy_comparison.caption.md) · [audit](data/sim/phaseD/matched_clock_audit.json) ·
[Study 3](data/sim/phaseD/study3_results.json) · [download values](data/sim/summary/policy_comparison.csv).

<!-- policy-summary:start -->
| Policy | Mean pose error, RMSE (mm) | Calibrations per actuator |
|:---|---:|---:|
| Initial calibration only | 0.401 | 1.0 |
| Clock: 2,700 cycles (train-selected) | 0.208 | 1.5 |
| Clock: 2,400 cycles (matched cost) | 0.058 | 2.0 |
| P-V trigger: τ = 0.05 | 0.058 | 2.0 |
| Calibration at every stage | 0.019 | 5.0 |
<!-- policy-summary:end -->

| Question | Recorded interpretation | Evidence |
|:---|:---|:---|
| Does the P-V trigger beat counting cycles? | The matched-cost clock ties it exactly. | [Audit](data/sim/phaseD/matched_clock_audit.json) |
| Does the deployed trigger warn before the error budget is crossed? | It fires late on every held-out actuator. | [Timing figure](docs/results.md#study-3-recalibration-policy) |
| Does the P-V loop track drift? | The association is constructed by the shared fatigue law. | [Audit](data/sim/phaseD/matched_clock_audit.json) |
| How does shared-manifold cross-talk vary? | It increases with supply resistance within the saved model sweep. | [Sensitivity figure](docs/results.md#study-4-shared-manifold-sensitivity) |
| Does pressure-only fatigue estimation transfer across actuators? | Study C fails its transfer rule; Study B's post-onset precision remains unestablished. | [Observability record](docs/specs/observability-program/program.md) |

## Quick start

Python 3.11, the CI version. These commands run the tests and check the saved
results and manuscripts; they don't rerun the studies.

```bash
git clone https://github.com/500ft/soft-actuator-recalibration.git
cd soft-actuator-recalibration
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pytest reportlab pypdf
python -m pytest -q
python -m scripts.check_manuscript_numbers
python -m scripts.check_pdf_arxiv
python -m scripts.check_publication_fallback
```

The number check covers the v1.3 and v1.4 manuscripts. The PDF check covers the
archived v1.3 PDF only. The last command checks the archive. With
`--for-publication`, it exits with code 2 (BLOCKED) because the v1.4 release
was withdrawn.
To reproduce the matched-cost audit, regenerate the dataset with
`python -m scripts.phaseD_dataset`, then run `python -m scripts.audit_matched_clock`.

To rerun the studies, see the
[reviewer guide](docs/START_HERE.md#reviewer-reproduce-the-checks). The study
scripts write under `data/`, so use a separate checkout.

## Separate successor preparation

A separate local project asks whether pressure retention can predict
functional loss within the next N cycles, beyond cycle count and load history
on unseen manufacturing batches. Its pressure-retention method must first be
tested against fixture leaks, temperature changes and actuator deformation.
The chosen specimen is an in-house McKibben muscle. Functional loss will be
defined using blocked force measured at fixed length and test pressure on a
separate force sensor; the force-drop threshold remains undecided. Screening
assembly defects and predicting later loss are separate questions.

Local work so far consists of sensor-resolution and ideal-gas pressure-decay
calculations and a theoretical metrology figure. The [successor record](docs/decisions/0002-successor-software-preparation.md)
locates the separate repository, and the [specimen decision](docs/decisions/0003-successor-specimen-and-endpoint.md)
records the selected endpoint. Physical start, equipment, location, budget,
exact build and public repository name remain open. The [roadmap](ROADMAP.md)
lists the required evidence. The [history index](docs/history/README.md)
links this study's original results, figures and manuscript records. Its
[reference-chamber CAD](cad/reference-volume/DESIGN_NOTES.md) has verified
model geometry; manufacture, assembled-volume calibration and pressure
suitability have not been verified.

## Limits

- All 20 actuators come from one simulated fatigue model. Held-out actuators
  test robustness to that model, not to real device-to-device variation, and no
  physical actuator was tested.
- Study 3's probe is idealized: noise-free, with no rest period, and generated
  by the same fatigue model as the drift it predicts. Probe noise and varying
  rest periods are untested.
- Five life stages can't show how the trigger behaves between them.
- The error budget is an average over life stages, not a worst case. Probe time
  and recalibration downtime were not measured.
- Absolute errors stay under a millimetre throughout, so triggered
  recalibration matters most where accuracy requirements are tight.

## Documentation

| Document | What it covers |
| --- | --- |
| [Reading guide](docs/START_HERE.md) | Short paths for readers, reviewers and contributors |
| [Results and limits](docs/results.md) | Every study's findings in full |
| [Data and figures](docs/data-and-figures.md) · [manifest](docs/figure-manifest.json) | Inputs and scripts behind each figure |
| [Review record](docs/REVIEW_READY.md) · [v1.4 withdrawal](docs/corrections/v1.4-withdrawn-2026-10-02.md) · [v1.3 correction](docs/corrections/v1.3-methods-2026-09-05.md) | Why v1.4 was withdrawn and what v1.3 overstated |
| [Study history](docs/history/README.md) · [Observability studies](docs/specs/observability-program/program.md) | Closed simulation questions, original figures and reference-chamber CAD |
| [Literature](literature/README.md) · [claim ledger](literature/claim-ledger.md) | Sources for and against each claim |

```text
sim/        pneumatic, fatigue, sensing and kinematic models
pipeline/   feature extraction, health signals and estimators
scripts/    study runners, plot generation and checks
tests/      model, policy, figure and publication tests
data/       committed synthetic results; the large dataset is regenerated
docs/       methods, results, manuscripts and review records
evidence/   recorded checks
```

## Contributing, citation and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing code or results. When
reporting a problem, include the command, the source revision, and what you
expected and saw.

[CITATION.cff](CITATION.cff) still describes the v1.3 manuscript. If you cite
it, name the version and mention the [correction](docs/corrections/v1.3-methods-2026-09-05.md).
The repository was renamed; the paper title was not
([identity note](docs/REPOSITORY_IDENTITY.md)).

Code is [MIT](LICENSE). Manuscript text, documentation and figures are
[CC BY 4.0](LICENSE-docs). Superseded publication instructions are preserved in
[submission notes](docs/SUBMISSION.md) and [Zenodo notes](docs/ZENODO_FALLBACK.md).
