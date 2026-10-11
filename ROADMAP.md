# Roadmap

## Closed-study finish line

Done: preserve the reproducible simulation study and its audit. At matched
recalibration cost, the cycle-count clock ties the P-V trigger; see the
[audit output](data/sim/phaseD/matched_clock_audit.json) and [result index](docs/results.md).
v1.4 remains withdrawn. The [history index](docs/history/README.md) retains the
manuscripts, corrections, executed results, original figures and preregistrations.

| Closed item | Prerequisite | Completion evidence |
|---|---|---|
| Correct the headline comparison | Reproduce the matched-cost policies | Audit output and withdrawal record in the result index |
| Correct the Libby measurement attribution | Inspect the actual full text | [Literature check](docs/A01_A04_Literature_Review.md#libby-full-text-check) and corrected manuscript sources |
| Remove obsolete active work | Trace imports, commands and evidence consumers | Unrun C2 implementation and redundant proposals removed; retained sources and pre-cleanup snapshot listed in the history index |
| Preserve reproducibility | Keep executed-result generators and corrections | Existing tests, numeric checks, figure lineage and archive-integrity checks remain active |

This repository is finished. No manuscript release, C2 run or new simulation
campaign is pending here. The reference chamber is retained as CAD; physical
manufacture and calibration are unverified.

## Separate successor question

Does qualified pressure retention predict independently measured functional
loss within the next N cycles, beyond cycle count and load history, on unseen
manufacturing batches?

Done: source-supported local metrology calculations, independent equation tests
and a theoretical figure. The [successor record](docs/decisions/0002-successor-software-preparation.md)
pins that result and locates the separate local repository. Its `ROADMAP.md`
is the full dependency plan for the successor; it does not reopen this study.
The owner adopted the dependency plan and this cleanup, without approving
physical work, a public name or publication. The owner then chose the
successor's specimen and endpoint, in-house McKibben muscles and blocked force
at fixed length; see [decision 0003](docs/decisions/0003-successor-specimen-and-endpoint.md).

## Dependencies and remaining evidence

| Stage | State and prerequisite | Evidence required to complete |
|---|---|---|
| Setup, endpoint and parts | Current; specimen and endpoint chosen, remaining owner decisions pending | Confirmed access/inventory, bladder/sleeve/fitting definition with a batch rule, a registered loss criterion and compatible parts for 500 kPa |
| Single-channel apparatus | Future; setup and physical authorization | Documented control/acquisition, calibrated units and independent functional measurement |
| Blank, known-leak, thermal and compliance qualification | Future; usable apparatus | Resolvable retention change with uncertainty above nuisance effects |
| Development pilot | Future; qualified probe and approved endpoint | Unit/batch variation, probe effects and precursor ordering relative to functional loss |
| Acquisition and study design | Future; pilot supports a useful precursor | Qualified channels if expansion is needed, justified sample size and frozen whole-batch holdouts |
| Confirmatory evaluation | Future; frozen design and owner authorization | Loss-within-N-cycles predictions compared to registered baselines, with lead time and false alarms |
| Write-up | Future; confirmation or a documented earlier stop | Reproducible results and a clear distinction between a null result, measurement limits and resource limits |

Multichannel expansion is conditional. A fixed blocked-force drop is a proposed
endpoint pending owner selection and specimen/application feasibility. Horizon N,
false-alarm unit and lead-time definition must be registered before evaluation.
Naming approval is independent of physical readiness; no public successor exists.

Owner action: confirm physical start, location, budget, available equipment,
the loss criterion for the blocked-force endpoint, purchases for the 500 kPa
supply and sensors, and the public successor name.
