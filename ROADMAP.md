# Roadmap

## Closed-study finish line

The simulation study is closed. At the same recalibration count, a cycle-count
schedule ties the pressure–volume (P-V) trigger on pose error; see the
[audit output](data/sim/phaseD/matched_clock_audit.json) and [results](docs/results.md).
The v1.4 manuscript remains withdrawn. The [history index](docs/history/README.md)
links the manuscripts, corrections, executed results, original figures and
preregistrations.

| Closed item | Prerequisite | Completion evidence |
|---|---|---|
| Correct the headline comparison | Reproduce the matched-cost policies | Audit output and withdrawal record in the result index |
| Correct the Libby measurement attribution | Inspect the actual full text | [Literature check](docs/A01_A04_Literature_Review.md#libby-full-text-check) and corrected manuscript sources |
| Remove obsolete active work | Trace imports, commands and uses of the results | Unrun C2 implementation and redundant proposals removed; remaining sources and pre-cleanup snapshot listed in the history index |
| Preserve reproducibility | Keep executed-result generators and corrections | Tests, numeric checks, figure lineage and archive-integrity checks remain active |

No manuscript release, C2 run or new simulation campaign is pending here. The
reference chamber exists as a CAD model with checked nominal geometry. Its
physical manufacture, assembled-volume calibration and pressure suitability
have not been verified.

## Separate successor question

Does pressure retention predict independently measured functional loss within
the next N cycles, beyond cycle count and load history, on unseen manufacturing
batches? Before testing that claim, the probe must be checked with a rigid
blank, a characterized leak and a compliant specimen under changing
temperature. Those tests set the uncertainty in an observed pressure change.

Local metrology calculations, independent equation tests and a theoretical
figure are complete. The [successor record](docs/decisions/0002-successor-software-preparation.md)
locates that work in a separate local repository, whose `ROADMAP.md` gives its
full dependency plan. The selected specimen is an in-house McKibben muscle,
and the independent functional endpoint is blocked force at fixed length and
test pressure; see [decision 0003](docs/decisions/0003-successor-specimen-and-endpoint.md).
Physical work, a public name and publication have not been approved.

## Dependencies and remaining evidence

| Stage | State and prerequisite | Evidence required to complete |
|---|---|---|
| Setup, endpoint and parts | Current; specimen type and endpoint chosen, exact build and resources pending | Confirmed access and equipment inventory, bladder/sleeve/fitting definition with a batch rule, a force-loss criterion set before outcomes, and compatible parts for 500 kPa |
| Single-channel apparatus | Future; setup and physical authorization | Documented control/acquisition, calibrated units and independent functional measurement |
| Blank, known-leak, thermal and compliance tests | Future; usable apparatus | Smallest detectable retention change and its uncertainty under fixture leaks, temperature and deformation |
| Development pilot | Future; probe passes those tests and endpoint procedure is set | Unit/batch variation, probe effects and whether retention changes precede functional loss |
| Acquisition and study design | Future; pilot supports a useful precursor | Additional channels tested if needed, justified sample size and whole-batch test cases reserved before evaluation |
| Confirmatory evaluation | Future; study design fixed and owner authorization | Loss-within-N-cycles predictions compared with specified baselines, including lead time and false alarms |
| Write-up | Future; confirmation or a documented earlier stop | Reproducible results and a clear distinction between a null result, measurement limits and resource limits |

Additional channels depend on pilot throughput needs. The blocked-force drop
threshold that defines functional loss, horizon N, false-alarm unit and lead-time
definition must be fixed before evaluation. Naming approval is separate from
physical readiness; no public successor repository exists.

Next decision: confirm physical start, location, budget, available equipment,
the blocked-force loss criterion, any purchases for the 500 kPa supply and
sensors, and the public successor name.
