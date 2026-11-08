# Successor hardware requirements and interfaces

The measurand is blocked force at fixed muscle length and regulated pressure.
`cad/geometry.json` owns the provisional specimen, fitting, frame, cell and
chamber inputs. `cad/oracle.py` computes force, required series stiffness and
the solved reference-cavity length. Results and explicit omissions live in the
executed concept evidence under `cad/runs/concept_20261108/`.

| Requirement | Interface and verification |
| --- | --- |
| Axial load path | Ported fitting at the fixed end; cell at the closed end; four pin joints and the added double-clevis coupler keep the path axial. Final eye/pin fits, thread engagement and joint compliance remain detail inputs. |
| Series stiffness | Required stiffness is 99 times the muscle force/length slope, to limit the length-change force bias to one percent. The current screen omits joints/clevis contact. SAR-SIM-02 and a known-load dial-gauge test are the paired checks. |
| Alignment and length | Angle below one degree; lateral offset no greater than 0.5 percent of active length; set and lock pin-to-pin length within +/-0.1 mm. Inspect the assembled fixture after real interfaces are supplied. |
| Hose/cable force | Fixed-end hose loop clamped to the frame so its tension bypasses the cell. The modeled cell cable keep-out meets the vendor bend basis; actual slack, strain relief and force remain inspection inputs. |
| Reference volume | Main cavity length is solved from volume and bore. Cap-port volume is separate. The closed study's printed chamber is unchanged and has no rating for the successor pressure. |
| Pressure qualification | The separate [P1-P7 plan](pressure_qualification_plan.md) holds pressure-part detail/release. The current operating cell/frame cannot qualify the higher pull-out load. A separate rated test method remains owner-held. |

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
