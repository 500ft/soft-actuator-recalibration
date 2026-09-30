# Soft Actuator Recalibration

**When should a soft robot recalibrate?** This simulation study tests whether
pressure-volume probes can help answer that question while pose estimates use
pressure alone.

As a simulated pneumatic actuator ages, its pressure-to-pose calibration can
drift. The study compares ways to decide when to recalibrate and shows how each
choice affects pose error and the number of recalibrations. There are no
physical actuator measurements in this repository.

> **Publication hold:** The archived v1.3 manuscript overstates part of the
> method. Read the [correction notice](docs/corrections/v1.3-methods-2026-09-05.md)
> alongside the [revised manuscript](docs/preprint_v1_4_candidate.md). The
> revision still needs author review. There is no corrected PDF yet, and the
> revision has no arXiv ID or DOI. A technical check of the old PDF does not
> mean the revision is ready to publish.

[![CI](https://github.com/500ft/soft-actuator-recalibration/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/500ft/soft-actuator-recalibration/actions/workflows/ci.yml)
[![Evidence: simulation only](https://img.shields.io/badge/evidence-simulation_only-475569)](docs/results.md)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](.github/workflows/ci.yml)

[Read the results](docs/results.md) · [Reproduce the checks](#quick-start) ·
[Author review](docs/AUTHOR_REVIEW_DAY3.md)

![Simulation results comparing four recalibration policies by pose error and number of recalibrations](data/sim/phaseD/study3_fig4_recal_tradeoff.png)

*This plot comes from Study 3's simulation of actuators held out from training.
The counts include the first calibration. The error is averaged across study
stages, so the plot does not show the worst error at every moment. The study did
not measure probe time or downtime. See the [full results](docs/results.md#study-3-recalibration-policy)
and [how the plot was made](docs/data-and-figures.md#study-3-recalibration-policy).*

## About

A soft pneumatic actuator's response can change as its material wears. More
frequent recalibration means more calibration events, but waiting too long can
increase pose error. This
project tests whether an occasional pressure-volume (P-V) probe can help choose
when to recalibrate. Normal pose estimates still use pressure alone.

The repository contains the simulator, fatigue and sensing models, pose
estimators, scripts to run the studies, and the resulting data and figures. The
main result is the **comparison of recalibration policies**, along with a clear
account of what the simulation cannot tell us.

| Question | What the study found |
| --- | --- |
| Can a condition-based trigger reduce recalibrations without too much pose error? | The comparison uses synthetic actuators from one degradation model. [Study 3 results](docs/results.md#study-3-recalibration-policy) |
| Is a shared air supply the main source of pose error? | Its effect was smaller within the tested simulation, but grew as the simulated supply became softer. [Results](docs/results.md#study-4-shared-manifold-sensitivity) |
| Does the trigger warn us before pose error crosses the limit? | The tested trigger at `tau = 0.05` did not provide advance warning. [Results](docs/results.md#study-3-recalibration-policy) |
| Does this work on real actuators? | This repository has no physical tests. |
| Can pressure alone reveal fatigue across different actuators? | Only under some conditions. The [observability studies](docs/specs/observability-program/program.md) document where the approach works and where it fails. |

## Evidence snapshot

These are **simulation results**, not measurements from a physical device. The
[results summary](docs/results.md) explains the limits of each finding.

| Finding | Where to look |
| --- | --- |
| Test data | Actuators were separated by identity for training and evaluation. [Dataset manifest](data/sim/phaseD/manifest.json) |
| P-V probes and pose drift | They move together in this simulation, but the uncertainty is wide because few actuator identities were held out. [Cluster results](data/sim/phaseD/study3_cluster_ci_results.json) |
| Recalibration trade-off | The triggered policy recalibrates less often than the always-on policy while meeting the study's average error limit. [Study 3 results](data/sim/phaseD/study3_results.json) |
| Advance warning | The tested trigger gives no advance warning. Triggering earlier means more recalibrations. [Explanation](docs/results.md#study-3-recalibration-policy) |

## Quick start

CI uses Python 3.11. These commands run the tests and check the saved study and
manuscript files. They do not rerun the studies or change the saved results.

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

The number check covers both the old and revised Markdown manuscripts. The PDF
check applies **only to the old v1.3 PDF**. A passing archive check means the old
files are intact; it does not mean the revised manuscript is ready to publish.
Until the author approves the correction,
`python -m scripts.check_publication_fallback --for-publication` reports
**BLOCKED** and exits with code **2**.

For instructions on rerunning the studies and a local pytest workaround, see the
[reviewer guide](docs/START_HERE.md#reviewer-reproduce-the-checks). Study scripts
write under `data/`, so run them in a separate checkout after recording the
source revision. Rerunning a study does not clear the publication hold.

## Documentation

| Read | For |
| --- | --- |
| [Reading guide](docs/START_HERE.md) | Short paths for new readers, reviewers, and contributors |
| [Results and limitations](docs/results.md) | Findings and the limits of the simulation |
| [Data and figures](docs/data-and-figures.md) · [Figure manifest](docs/figure-manifest.json) | Inputs and scripts behind the figures |
| [Author review](docs/AUTHOR_REVIEW_DAY3.md) | Decisions needed before publication |
| [Correction](docs/corrections/v1.3-methods-2026-09-05.md) · [Revised manuscript](docs/preprint_v1_4_candidate.md) | The correction and the version awaiting review |
| [Proposed follow-up tests](docs/specs/robosoft-v2/claim-spine.md) | Stronger tests that have not been completed |
| [Observability studies](docs/specs/observability-program/program.md) · [novelty check](docs/reviews/novelty-check-2026-09-16.md) | Results on estimating fatigue from pressure across different actuators |
| [Literature review](docs/A01_A04_Literature_Review.md) | Related research |
| [Literature folder](literature/README.md) · [claim ledger](literature/claim-ledger.md) · [gaps](literature/gaps.md) | Sources for and against the study's claims |
| [Review index](docs/REVIEW_READY.md) | Checks, source records, and open decisions |

```text
sim/        pneumatic, fatigue, sensing, and kinematic models
pipeline/   feature extraction, health signals, and estimators
scripts/    study runners, plot generation, and artifact checks
tests/      model, policy, figure, and publication regression tests
data/       committed synthetic artifacts; large dataset regenerated separately
docs/       methods, results, manuscripts, and review records
evidence/   recorded checks and reproducible counterexamples
```

## What remains

The author must review the corrected manuscript before a new PDF can be prepared
for publication. The archived v1.3 version will stay as it is. The
[review packet](docs/AUTHOR_REVIEW_DAY3.md) recommends keeping the uncertainty
across actuators and the original `tau = 0.05` result. Any new trigger rule needs
a fresh test on data that did not influence its design.

The relationship between the P-V probe and pose error may look stronger because
both depend on the same simulated fatigue state. Study 3 uses an idealized probe
without a rest period. It does not test probe noise or changing rest periods.
Measurements at a few life stages cannot show how well the trigger warns at
every moment. Results on held-out simulated actuators do not show that the
method transfers to different physical materials or mechanisms.

## Contributing, citation, and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing code or generated
results. When reporting a problem, include the command, source revision, and
expected and actual behavior. Describe proposed tests as proposals until they
have been run.

[CITATION.cff](CITATION.cff) refers to the **old v1.3 manuscript**. When citing
it, name the version and include the [correction](docs/corrections/v1.3-methods-2026-09-05.md)
if you discuss its findings. The repository's new name is not a new paper title.
See [repository identity](docs/REPOSITORY_IDENTITY.md).

Code is licensed under [MIT](LICENSE). Manuscript text, documentation, and
figures are licensed under [CC BY 4.0](LICENSE-docs). See
[submission notes](docs/SUBMISSION.md) and [Zenodo notes](docs/ZENODO_FALLBACK.md)
for publication steps. The publication hold still applies.
