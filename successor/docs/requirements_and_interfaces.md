# Successor hardware requirements and interfaces

The measurand is blocked axial force at fixed muscle length and regulated gauge
test pressure. [geometry.json](../cad/geometry.json) owns the provisional specimen,
fitting, frame, cell and chamber inputs. [oracle.py](../cad/oracle.py) computes
force, required series stiffness and the solved reference-cavity length. The
[current concept result](../cad/runs/cell_exit_20261108_rev02/result.json) holds
the force/compliance screen, corrected cell/cable source readback and omissions.
In the Desktop packet, that result is at
`04_ANALYSIS/successor-cell-exit-rev02/result.json` relative to the project folder.

| Requirement | Interface and verification |
| --- | --- |
| Force range and design load | Use `screening.force_cases` in the current result: the operating range starts at zero and extends to the maximum `blocked_force_N`; the maximum `proof_pressure_force_N` supplies the higher design-load case. The pressure and braid-angle cases come from geometry.json. Actual cell range, load-train rating and specimen choice remain O12/O13 inputs. |
| Axial load path | Ported fitting at the fixed end; cell at the closed end; four pin joints and the added double-clevis coupler keep the path axial. Final eye/pin fits, thread engagement and joint compliance remain detail inputs. |
| Series stiffness | Required stiffness is 99 times the muscle force/length slope, to limit the length-change force bias to one percent. The current screen omits joints/clevis contact. SAR-SIM-02 and a known-load dial-gauge test are the paired checks. |
| Alignment and length | Angle below one degree; lateral offset no greater than 0.5 percent of active length; set and lock pin-to-pin length within +/-0.1 mm. Inspect the assembled fixture after real interfaces are supplied. |
| Hose/cable force | Fixed-end hose loop clamped to the frame so its tension bypasses the cell. The modeled cell cable keep-out meets the vendor bend basis; actual slack, strain relief and force remain inspection inputs. |
| Reference volume | Main cavity length is solved from volume and bore. Cap-port volume is separate. The closed study's printed chamber is unchanged and has no rating for the successor pressure. |
| Pressure qualification | The separate [P1-P7 plan](pressure_qualification_plan.md) holds pressure-part detail/release. The current operating cell/frame cannot qualify the higher pull-out load. A separate rated test method remains owner-held. |

## Force-measurement error budget

Keep each contributor below as a separate line item. Numerical allocations and
combined measurement uncertainty remain pending; the geometry and compliance
screen provide predictions, not a calibrated force-measurement result.

| Contributor | Current basis and status | Later qualification method |
| --- | --- | --- |
| Cell and readout accuracy | PENDING: O13 must identify the actual cell revision and measurement chain. Manufacturer accuracy, calibration uncertainty, nonlinearity, hysteresis, repeatability and readout resolution have no allocated force-error contribution yet. | Review the selected cell/readout specifications and calibration evidence. Under an approved procedure, apply known axial loads over the intended range in loading and unloading, repeat readings and check the zero and sensitivity after remounting. |
| Frame compliance | SCREENED / PENDING QUALIFICATION: `screening.frame_stiffness_cases` in the current result carries the series stiffness and predicted force-bias fraction for each cell-displacement case. The calculation in oracle.py omits joint, clevis and contact compliance. | Pair SAR-SIM-02 with a known-load dial-gauge measurement of the complete load train. Use measured deflection and the model's force/length sensitivity to bound the resulting force bias. |
| Misalignment cosine and bending | PENDING: the angle, lateral-offset and pin-to-pin length requirements above are inspection targets. Their cosine-force contribution and bending/moment cross-talk have no allocated uncertainty yet. | Inspect the assembled load-axis angle and offset. Obtain the selected cell's off-axis/moment sensitivity and check axial calibration under the permitted alignment conditions before assigning a contribution. |
| Hose and cable forces | PENDING: the fixed-end hose rule and corrected cell-cable keep-out establish routing intent. The current result checks cable bend geometry and rail clearance; it supplies no measured parasitic force. | With the actual connections and strain relief fitted, tare the complete setup and measure the reading change when the slack loops move through their intended positions. Include any remaining preload, friction or routing-dependent force in this line item. |
| Load-cell temperature | PENDING: the actual cell's zero and sensitivity temperature coefficients, operating temperature range and thermal settling are unqualified. | Review the selected cell revision's temperature specifications. Log cell temperature with force, and establish zero/span changes over the intended temperature conditions before assigning a temperature contribution. |
| Pressure regulation times force/pressure sensitivity | PENDING: oracle.py's current blocked-force expression is linear in gauge pressure at fixed length and braid geometry. Obtain `dF/dP` from its force divided by the gauge working pressure in geometry.json, then multiply by measured pressure deviation in matching units. Actual pressure sensing and regulation remain O13/O14b inputs. | After sensor and regulator selection, qualify pressure calibration and stability over the force-reading interval. Propagate pressure offset and variation through `dF/dP`, retaining pressure-measurement uncertainty separately in the pressure-deviation basis. |

Record the operating conditions and evidence for each contribution before
combining them, including correlated bias terms where applicable. No contributor
is closed by the compliance screen alone.

The frame and machined parts are provisional 6061-T6 concepts; pins and bought
envelopes retain the material/source fields in the register. Standard O-ring
glands, actual crimp and tap details, pressure sensor/tee, regulator and valve
geometry remain omitted. O12/O13/O14b/O15 and the plan's unresolved selections
remain holds. Drawing checklists use third-angle mm, ASME Y14.5 and ISO 2768-mK;
explicit thread, pin and seal fits have to be established during detail.

Native SOLIDWORKS is optional under handoff 04; the editable model is CadQuery
with an independent algebra/quadrature oracle. No physical work, purchase,
fabrication or pressurization is authorized. Decision 0004 permits public CAD
and calculations, while research-result publication remains a separate decision.
