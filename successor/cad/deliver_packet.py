"""Deliver the concept metadata, drawings checklist and pressure-plan review."""
import argparse
import csv
import json
from pathlib import Path
import shutil

import cadquery as cq

import oracle

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--desktop',type=Path,required=True);args=parser.parse_args()
    root=args.desktop;analysis=root/'04_ANALYSIS/successor-concepts';g=json.loads((HERE/'geometry.json').read_text())
    rows=list(csv.DictReader((HERE/'part_number_register.csv').open()));revision=[]
    for row in rows:
        pn=row['pn'];path=analysis/(pn+'_acceptance.json');record=json.loads(path.read_text());step=Path(record['file'])
        props={'PartNo':pn,'Revision':row['rev'],'Description':row['title'],'Material':row['material'] or 'Reference envelope; see source',
               'Finish':'Deburr / see checklist','Process':row['process'] or 'Concept assembly','Project':root.name,'Status':'HOLD',
               'SourceKey':'successor/cad/geometry.json','Evidence':'provisional_design; source identified for every input',
               'ToleranceStd':'ISO 2768-mK; explicit tolerances take precedence','SimIDs':'SAR-SIM-01..03 after owner/detail gates; SAR-SIM-04 optional',
               'DrawnBy':'Codex','Date':'2026-11-08'}
        (root/'01_CAD'/(step.stem+'_PROPERTIES.json')).write_text(json.dumps(props,indent=2)+'\n');record['properties']=props
        if row['type'].startswith('MFG'):
            lines=['CONCEPT / HOLD - NOT FOR FABRICATION',pn+' REV '+row['rev']+' '+row['title'],
                   'Third-angle projection; mm; ASME Y14.5 dimensioning; ISO 2768-mK general tolerances.',
                   'Dimensions/evidence: ../01_CAD/Parametric_Source/cad/geometry.json.',
                   'Datum axis: axial load / chamber bore. State end-face and pin-centre datums explicitly on a manual drawing.',
                   'Dimension all bores, shoulders, barb crests/roots, pin centres, bolt PCD and engagement from source as applicable.',
                   'Pin/eye clearance, thread class, retention, crimp interference and supplier fits remain detailed-design inputs.',
                   'The chamber main cavity length is solved from target volume and bore, not chosen independently.',
                   'Standard seal grooves are omitted until P3 selection. Pressure-part threads are envelope geometry, not released taps.',
                   'Frame pin-to-pin set length must be measured and locked; alignment and series-compliance checks remain required.',
                   'The native pilot drawing attempt produced views without dimensions. This checklist supports manual drafting.',
                   'Review pressure qualification plan P1-P7. Current operating frame/cell do not qualify for the separate pull-out load.',
                   *g['holds']]
            (root/'02_DRAWINGS'/(step.stem+'_DRAWING-CHECKLIST.txt')).write_text('\n'.join(lines)+'\n')
        path.write_text(json.dumps(record,indent=2)+'\n');revision.append({'pn':pn,'revision':row['rev'],'change':'Concept review packet only; no fabrication release'})
    # The flat frame shield is a cut sheet. Its local development is width x height.
    width=oracle.v(g,'frame','plate_width');height=oracle.v(g,'frame','rail_length');thickness=oracle.v(g,'frame','shield_thickness')
    shape=cq.Workplane('XY').rect(width,height).extrude(thickness);record=json.loads((analysis/'SAR-0109_acceptance.json').read_text());stem=Path(record['file']).stem
    dxf=root/'03_EXPORTS/DXF'/(stem+'.DXF');cq.exporters.export(shape.faces('>Z').wires(),str(dxf))
    wires=cq.importers.importDXF(str(dxf)).wires().vals();area=cq.Face.makeFromWires(wires[0]).Area()
    packet={'accepted':len(wires)==1 and abs(area-width*height)<1e-6,'scope':'Concept metadata, checklist and shield DXF only',
            'shield_dxf':{'file':str(dxf),'area_mm2':area,'expected_mm2':width*height},'physical_work_authorized':False,'pressure_rating_established':False}
    (analysis/'packet_result.json').write_text(json.dumps(packet,indent=2)+'\n')
    with (root/'00_ADMIN/CONCEPT_REVISION_LOG.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(revision[0]));writer.writeheader();writer.writerows(revision)
    current=[]
    for row in rows:
        entry=dict(row);entry['status']='CONCEPT / HOLD';entry['hold_on']='; '.join(g['holds']);current.append(entry)
    with (root/'00_ADMIN/part_number_register.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(current[0]));writer.writeheader();writer.writerows(current)
    (root/'00_ADMIN/STATUS.json').write_text(json.dumps({'parts':current,'accepted':None,'physical_work_authorized':False,'pressure_plan':'../01_CAD/Parametric_Source/docs/pressure_qualification_plan.md'},indent=2)+'\n')
    (root/'00_ADMIN/README.txt').write_text('All original 18 SAR entries plus SAR-0110 have concept models and executed STEP/independent-volume checks.\n'
        '86 geometry re-drive cases and four mechanics tests passed. Inputs O12/O13/O14b/O15 remain open.\n'
        'Editable source: 01_CAD/Parametric_Source/cad/. Drawings are checklists only.\n'
        'Draft P1-P7 plan: 01_CAD/Parametric_Source/docs/pressure_qualification_plan.md. It does not close the detail gate.\n'
        'P6 needs a separately qualified pull-out load train: its load exceeds the proposed 1 kN cell and 857 N frame basis.\n'
        'Standard seal grooves and pressure-sensor/tee ports remain omitted. No test result or pressure rating is claimed.\n'
        'No purchases, physical work, pressurization, or fabrication release are authorized. Closed-study files remain unchanged.\n')
    source=root/'01_CAD/Parametric_Source';(source/'cad').mkdir(parents=True,exist_ok=True);(source/'docs').mkdir(exist_ok=True)
    for file in HERE.iterdir():
        if file.is_file():shutil.copy2(file,source/'cad'/file.name)
    for file in (HERE.parent/'docs').glob('*.md'):shutil.copy2(file,source/'docs'/file.name)
    (root/'06_INSPECTION/README.txt').write_text('CONCEPT / HOLD. No hardware has been inspected.\n'
        'Use 02_DRAWINGS checklists for source dimensions and applicable datums. Physical inspection must identify part/revision, instrument and uncertainty.\n'
        'P1-P7 records, seal/fit selection, material traceability and reviewer approval are required before the corresponding qualification/release.\n'
        'The draft plan and pressure_plan_review.json identify the separate pull-out load-train hold.\n')
    print(json.dumps(packet,indent=2));return 0 if packet['accepted'] else 3


if __name__=='__main__':raise SystemExit(main())
