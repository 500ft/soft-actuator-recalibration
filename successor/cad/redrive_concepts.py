"""Re-drive each concept geometry input and retain independent volume checks.

This checks the CadQuery parameter path only. It does not close owner inputs,
validate material properties, or qualify a pressure-containing part.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

import build_concepts as cad
import oracle

HERE=Path(__file__).resolve().parent
ANALYSIS_ONLY={('specimen','angle_cases'),('specimen','working_pressure'),('specimen','proof_pressure'),
               ('frame','rail_area'),('frame','adjust_thread_pitch'),('cell','rated_force'),('cell','displacement_cases')}
CONSTRAINT_ONLY={('cell','cable_bend_radius')}


def check_models(g, data):
    expectations=oracle.volumes(g,data['adjuster_length_mm'])
    records={}
    for pn,shape in data['shapes'].items():
        m=cad.metrics(shape)
        if not m['valid']:raise RuntimeError(f'Invalid shape: {pn}')
        error=m['volume_mm3']-expectations[pn]
        if abs(error)>1e-5:raise RuntimeError(f'Independent volume mismatch {pn}: {error}')
        records[pn]=m
    records['cable_keepout']=cad.metrics(data['cable_keepout'])
    return records


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    g=json.loads((HERE/'geometry.json').read_text());baseline=check_models(g,cad.build(g))
    result={'accepted':False,'scope':'CadQuery concept geometry re-drive; no pressure or native release',
            'source_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['geometry.json','build_concepts.py','oracle.py','redrive_concepts.py']},
            'analysis_only_inputs':[list(k) for k in sorted(ANALYSIS_ONLY)],'cases':[]}
    for group,items in g.items():
        if not isinstance(items,dict) or group in ['material','omitted_features']:continue
        for key,entry in items.items():
            if not isinstance(entry,dict) or 'value' not in entry or (group,key) in ANALYSIS_ONLY:continue
            original=entry['value'];indices=range(len(original)) if isinstance(original,list) else [None]
            for index in indices:
                old=original[index] if index is not None else original
                if not isinstance(old,(int,float)):continue
                new=old+1 if isinstance(old,int) else old*0.99
                if (group,key)==('rod_end','eye_bore'):new=old*1.01
                if (group,key)==('cell','eye_to_eye'):new=old+0.5
                changed=copy.deepcopy(g)
                if index is None:changed[group][key]['value']=new
                else:changed[group][key]['value'][index]=new
                label=f'{group}.{key}'+(f'[{index}]' if index is not None else '')
                try:
                    data=cad.build(changed);metrics=check_models(changed,data)
                    affected=[pn for pn in baseline if any(not np.allclose(baseline[pn][field],metrics[pn][field],rtol=1e-10,atol=1e-7)
                              for field in ['volume_mm3','centroid_mm','bbox_mm','principal_volume_moments_mm5'])]
                    if not affected and (group,key) not in CONSTRAINT_ONLY:raise RuntimeError('Parameter produced no geometric change')
                    record={'parameter':label,'from':old,'to':new,'passed':True,'affected_geometry':affected,
                            'cable_rail_clearance_mm':data['cable_rail_clearance_mm']}
                except Exception as exc:
                    record={'parameter':label,'from':old,'to':new,'passed':False,'error':repr(exc)}
                result['cases'].append(record)
                args.output.write_text(json.dumps(result,indent=2)+'\n')
                print(label,record['passed'],flush=True)
                if not record['passed']:raise RuntimeError(f'Re-drive stopped at {label}: {record["error"]}')
    result['accepted']=all(c['passed'] for c in result['cases'])
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'accepted':result['accepted'],'case_count':len(result['cases'])}),flush=True)


if __name__=='__main__':main()
