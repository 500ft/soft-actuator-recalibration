# McKibben successor hardware

Keep new successor CAD, drawings, calculations, analysis inputs, results and
their evidence in this folder. The closed study elsewhere in this repository
remains unchanged. [Decision 0004](../docs/decisions/0004-successor-hardware-in-this-repo.md)
records the scope and publication approval. The successor's public name is pending.

Part numbers use the `SAR` prefix. The [part register](cad/part_number_register.csv)
holds the assigned numbers, titles, parent assemblies and input holds. Initial
entries come from the owner's handoff v6 and remain at their recorded stages.

The Windows output folder is `<Desktop>/soft-actuator-recalibration/`, with
`00_ADMIN`, `01_CAD`, `02_DRAWINGS`, `03_EXPORTS`, `04_ANALYSIS`, `05_VENDOR_REF`
and `06_INSPECTION` beneath it. Resolve Desktop through the Windows known-folder
API so redirected Desktops work. Source files and evidence belong here; generated
native CAD and review exports also go to that Desktop folder.

Scripts and code use the repository's [MIT License](../LICENSE). CAD, drawings
and documents use [CC BY 4.0](../LICENSE-docs), as approved in decision 0004.

No physical work, purchase, fabrication, hardware testing or pressurization is
authorized. Pressure-part release requires the committed P1-P7 qualification
plan and the applicable owner approvals. The pressure-sensor part and port
remain pending until the owner supplies the Mac sensor audit under O14b.
