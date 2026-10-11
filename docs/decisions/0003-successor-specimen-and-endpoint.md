# Decision: successor specimen and endpoint

## Status
Accepted 2026-10-10. Owner instruction 2026-10-10 (chat): adopt McKibben
pneumatic artificial muscles as the successor specimen and blocked force at
fixed length and fixed test pressure as its functional endpoint, and update the
successor accordingly.

## What was decided
- Specimen: in-house McKibben muscles (bladder, braided sleeve, end fittings)
  in place of the PneuNet mold route. Batches are a bladder tube lot, a sleeve
  lot or a build day.
- Endpoint: blocked force at fixed length and fixed test pressure, measured
  with its own force sensor in a separate step from the retention hold. The
  force-drop threshold that defines functional loss is still the owner's to
  register before outcomes are observed.
- Operating envelope: declared as roughly 200 to 500 kPa gauge, to be fixed by
  the chosen design. The sensor audit was redone for 0 to 500 kPa: the 25 psi
  absolute digital candidate is out of range; the 100 psi bridge variant fits
  at ADC gain 32 or 64; no digital candidate for this range has been audited.
- Pilot before expansion: about five or six muscles run to failure on one
  channel, retention measured every few hundred cycles, failure location
  recorded per unit. Rupture with no prior retention change ends the study as a
  quick negative.

## What was not decided
Purchases, physical start, work location, budget, equipment and the public name
remain pending. This decision authorizes no physical work and no publication.
The closed study in this repository is unchanged and v1.4 stays withdrawn.

## Where the record lives
Local successor repository (no remote), branch `specimen/mckibben-20261010`,
commit `d6fd0913a229f28654c177bee0b5183b0bd9dab8`:

```text
/Users/redhose/Projects/critical-audit-20261002/implementation/pivot-v2-20261006/workspaces/soft-actuator-lifetime
```

Files: `SPECIMEN.md` (rationale, failure modes, sources), `references.bib`
(six verified entries plus a Festo datasheet note), `SENSOR_OPTIONS.md` and
`results/sensor_compatibility.json` (redone audit), `ROADMAP.md` M0.2, M0.3,
M1.2, M3.1 and M3.3, the fixed-length note in `METHODS.md`, and
`tests/test_sensor_compatibility.py`.

## Sources checked for this decision
Klute and Hannaford 1998 (full text), Woods et al. 2012 (abstract), Miron and
Plante 2016 (metadata only), Durante et al. 2021 (abstract), Zylka 2026
(abstract), Kortman et al. 2026 (open-access partial text), Festo DMSP-10
datasheet (distributor copy: 0 to 8 bar operating pressure, no service-life
statement). The claim that commercial muscles last far longer than homemade
ones could not be verified from the datasheet and is not recorded as a fact.
