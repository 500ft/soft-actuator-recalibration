"""McKibben successor concepts. No closed-study files are imported or modified."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

import oracle

HERE = Path(__file__).resolve().parent


def box(x, y, z, bottom=0, cx=0, cy=0):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,bottom)).val()


def tube(od, id, length, bottom=0):
    wp=cq.Workplane('XY').circle(od/2)
    if id:wp=wp.circle(id/2)
    return wp.extrude(length).translate((0,0,bottom)).val()


def cut_z(shape, diameter, centres, bottom, depth):
    for x,y in centres:shape=shape.cut(tube(diameter,0,depth,bottom).translate((x,y,0)))
    return shape.clean()


def pin_hole(shape, diameter, z, depth):
    tool=tube(diameter,0,depth).rotate((0,0,0),(1,0,0),90).translate((0,depth/2,z))
    return shape.cut(tool).clean()


def metrics(shape):
    p=GProp_GProps();integration_error=BRepGProp.VolumeProperties_s(shape.wrapped,p,1e-9,True,False)
    I=p.MatrixOfInertia();a=np.array([[I.Value(i+1,j+1) for j in range(3)] for i in range(3)])
    b=shape.BoundingBox()
    center=p.CentreOfMass()
    return {'volume_mm3':p.Mass(),'centroid_mm':[center.X(),center.Y(),center.Z()],
            'bbox_mm':[b.xlen,b.ylen,b.zlen],'principal_volume_moments_mm5':np.linalg.eigvalsh(a).tolist(),
            'solid_count':len(shape.Solids()),'valid':shape.isValid(),'adaptive_integration_error':integration_error}


def make_plug(g, ported):
    v=lambda k:oracle.v(g,'plug',k)
    root,crest=v('root_diameter')/2,v('crest_diameter')/2
    shape=tube(2*root,0,v('grip_length'))
    for index in range(v('barb_count')):
        cone=cq.Solid.makeCone(root,crest,v('barb_pitch'),cq.Vector(0,0,index*v('barb_pitch')),cq.Vector(0,0,1))
        shape=shape.fuse(cone)
    end=v('grip_length')+v('head_length')
    if ported and v('head_length')-v('mechanical_depth')<=max(v('flow_end_from_head_start'),v('radial_port_from_head_start')+v('port_major')/2):
        raise ValueError('Fluid bore intersects the mechanical thread cavity')
    shape=shape.fuse(tube(v('head_diameter'),0,v('head_length'),v('grip_length')))
    shape=shape.cut(tube(v('mechanical_major'),0,v('mechanical_depth'),end-v('mechanical_depth')))
    if ported:
        shape=shape.cut(tube(v('flow_bore'),0,v('grip_length')+v('flow_end_from_head_start')))
        radial=tube(v('port_major'),0,v('head_diameter')/2).rotate((0,0,0),(0,1,0),90)
        shape=shape.cut(radial.translate((0,0,v('grip_length')+v('radial_port_from_head_start'))))
    return shape.clean()


def make_rod_end(g):
    v=lambda k:oracle.v(g,'rod_end',k)
    eye=tube(v('eye_diameter'),v('eye_bore'),v('eye_width')).rotate((0,0,0),(1,0,0),90).translate((0,v('eye_width')/2,0))
    stud=tube(v('stud_diameter'),0,v('centre_to_stud_tip')-v('eye_diameter')/2+v('stud_diameter')/2,-v('centre_to_stud_tip'))
    return eye.fuse(stud).clean()


def make_end_plate(g):
    v=lambda k:oracle.v(g,'frame',k)
    t=v('plate_thickness');shape=box(v('plate_width'),v('plate_depth'),t)
    for sign in [-1,1]:
        y=sign*(v('fork_gap')+v('ear_thickness'))/2
        shape=shape.fuse(box(v('ear_width'),v('ear_thickness'),v('ear_height'),t,cy=y))
    centres=list(itertools.product([-v('rail_spacing')/2,v('rail_spacing')/2],[-v('rail_section')[1]/4,v('rail_section')[1]/4]))
    shape=cut_z(shape,v('end_bolt_clearance'),centres,0,t)
    shape=cut_z(shape,v('adjuster_clearance'),[(0,0)],0,t)
    return pin_hole(shape,v('pin_diameter'),t+v('pin_from_plate'),v('fork_gap')+2*v('ear_thickness'))


def build(g):
    v=lambda group,key:oracle.v(g,group,key)
    f=lambda key:v('frame',key)
    if f('pin_diameter')>v('rod_end','eye_bore')+1e-9 or f('fork_gap')<=v('rod_end','eye_width'):
        raise ValueError('Pin or bearing collar interferes with the rod-end fork')
    shapes={'SAR-0101':make_plug(g,True),'SAR-0102':make_plug(g,False),
            'SAR-0103':tube(v('ferrule','od'),v('ferrule','id'),v('ferrule','length')),
            'SAR-0104':make_end_plate(g),'SAR-0502':make_rod_end(g)}
    # Length-adjustment block: lower fork and an axially threaded upper block.
    bx,by,bz=f('adjust_block_size')
    adjust=box(bx,by,bz,f('ear_height'))
    for sign in [-1,1]:
        adjust=adjust.fuse(box(f('ear_width'),f('ear_thickness'),f('ear_height'),cy=sign*(f('fork_gap')+f('ear_thickness'))/2))
    adjust=cut_z(adjust,f('adjust_thread_major'),[(0,0)],f('ear_height'),bz)
    shapes['SAR-0105']=pin_hole(adjust,f('pin_diameter'),f('pin_from_plate'),by)
    # Pin modeled along Y; retention hole remains outside the fork bearing span.
    pin=tube(f('pin_diameter'),0,f('pin_length')).fuse(tube(f('pin_head_diameter'),0,f('pin_head_length'),-f('pin_head_length')))
    cross=tube(f('pin_cross_hole'),0,f('pin_diameter')).rotate((0,0,0),(0,1,0),90).translate((-f('pin_diameter')/2,0,f('pin_length')-f('pin_head_length')*1.5))
    pin=pin.cut(cross).rotate((0,0,0),(1,0,0),90).translate((0,f('pin_length')/2,0))
    shapes['SAR-0106']=pin.clean()
    c=lambda key:v('chamber',key)
    length=oracle.chamber_length(g)
    if length<=2*c('flange_length') or c('bolt_depth')>=c('flange_length'):
        raise ValueError('Chamber flange/bolt lengths overlap or break through')
    if (c('flange_od')-c('bolt_pcd'))/2 < 1.5*c('bolt_major'):
        raise ValueError('Chamber bolt edge distance below 1.5 nominal diameters')
    bolt_centres=[(c('bolt_pcd')/2*math.cos(2*math.pi*i/c('bolt_count')),c('bolt_pcd')/2*math.sin(2*math.pi*i/c('bolt_count'))) for i in range(c('bolt_count'))]
    body=tube(c('barrel_od'),c('bore_diameter'),length)
    for z in [0,length-c('flange_length')]:body=body.fuse(tube(c('flange_od'),c('bore_diameter'),c('flange_length'),z))
    for z in [0,length-c('bolt_depth')]:body=cut_z(body,c('bolt_major'),bolt_centres,z,c('bolt_depth'))
    shapes['SAR-0107']=body.clean()
    cap=tube(c('flange_od'),v('plug','flow_bore'),c('cap_thickness'))
    shapes['SAR-0108']=cut_z(cap,c('bolt_clearance'),bolt_centres,0,c('cap_thickness'))
    shapes['SAR-0109']=box(f('plate_width'),f('shield_thickness'),f('rail_length'))
    cu=lambda key:v('coupler',key)
    h=cu('pin_spacing')+2*cu('pin_end_distance')
    coupling=box(cu('width'),cu('depth'),h)
    for z in [0,cu('pin_spacing')]:coupling=coupling.cut(box(cu('width'),f('fork_gap'),2*cu('pin_end_distance'),z))
    for z in [cu('pin_end_distance'),h-cu('pin_end_distance')]:coupling=pin_hole(coupling,f('pin_diameter'),z,cu('depth'))
    shapes['SAR-0110']=coupling.clean()
    shapes['SAR-0501']=box(*v('cell','size'))
    sx,sy=f('rail_section');shapes['SAR-0503']=box(sx,sy,f('rail_length'))
    cut_length=v('specimen','active_length')+2*v('plug','grip_length')
    shapes['SAR-0504']=tube(v('specimen','bladder_od'),v('specimen','bladder_id'),cut_length)
    shapes['SAR-0505']=tube(v('specimen','bladder_od')+2*v('specimen','braid_wall'),v('specimen','bladder_od'),cut_length)
    # Generic reference fitting envelope, not a certified SMC model.
    p=lambda key:v('pneumatic',key)
    fitting=tube(v('plug','port_major'),0,p('fitting_stud_length'))
    af=p('fitting_hex_af');circum=af/math.cos(math.pi/6)
    hexagon=cq.Workplane('XY').polygon(6,circum).extrude(p('fitting_stud_length')).translate((0,0,p('fitting_stud_length'))).val()
    fitting=fitting.fuse(hexagon).fuse(tube(af,0,p('fitting_length')-2*p('fitting_stud_length'),2*p('fitting_stud_length')))
    shapes['SAR-0506']=fitting.cut(tube(p('tube_id'),0,p('fitting_length'))).clean()
    # Explicit four-pin load chain, lower ported fitting at the fixed end.
    low_pin=f('plate_thickness')+f('pin_from_plate')
    rod=shapes['SAR-0502']
    low_eye=rod.rotate((0,0,0),(1,0,0),180).translate((0,0,low_pin))
    fixed_face=low_pin+v('rod_end','centre_to_stud_tip')-v('plug','mechanical_depth')
    fixed_tip=fixed_face+v('plug','head_length')+v('plug','grip_length')
    free_end=fixed_tip+v('specimen','active_length')
    ported=shapes['SAR-0101'].rotate((0,0,0),(1,0,0),180).translate((0,0,fixed_tip))
    closed=shapes['SAR-0102'].translate((0,0,free_end))
    high_face=free_end+v('plug','grip_length')+v('plug','head_length')
    muscle_high_pin=high_face-v('plug','mechanical_depth')+v('rod_end','centre_to_stud_tip')
    high_eye=rod.translate((0,0,muscle_high_pin))
    active_latex=tube(v('specimen','bladder_od'),v('specimen','bladder_id'),v('specimen','active_length'),fixed_tip)
    active_braid=tube(v('specimen','bladder_od')+2*v('specimen','braid_wall'),v('specimen','bladder_od'),v('specimen','active_length'),fixed_tip)
    ferrules=[shapes['SAR-0103'].translate((0,0,fixed_face+v('plug','head_length'))),
              shapes['SAR-0103'].translate((0,0,free_end-v('ferrule','length')+v('plug','grip_length')))]
    muscle=[ported,closed,active_latex,active_braid,low_eye,high_eye]+ferrules
    shapes['SAR-0002']=cq.Compound.makeCompound(muscle)
    coupling=shapes['SAR-0110'].translate((0,0,muscle_high_pin-cu('pin_end_distance')))
    cell_low_pin=muscle_high_pin+cu('pin_spacing')
    cell_high_pin=cell_low_pin+v('cell','eye_to_eye')
    cell_bottom=(cell_low_pin+cell_high_pin-v('cell','size')[2])/2
    cell=shapes['SAR-0501'].translate((0,0,cell_bottom))
    cell_low_eye=rod.rotate((0,0,0),(1,0,0),180).translate((0,0,cell_low_pin))
    cell_high_eye=rod.translate((0,0,cell_high_pin))
    adjust_offset=cell_high_pin-f('pin_from_plate')
    adjust_block=shapes['SAR-0105'].translate((0,0,adjust_offset))
    upper_base=f('plate_thickness')+f('rail_length')
    rod_bottom=adjust_offset+f('ear_height')+bz-v('plug','mechanical_depth')
    rod_top=upper_base+f('plate_thickness')+f('locknut_allowance')
    adjuster=tube(f('adjust_thread_major'),0,rod_top-rod_bottom,rod_bottom)
    if rod_top<=rod_bottom:raise ValueError('Load chain exceeds available frame height')
    pins=[shapes['SAR-0106'].translate((0,0,z)) for z in [low_pin,muscle_high_pin,cell_low_pin,cell_high_pin]]
    rails=[shapes['SAR-0503'].translate((sign*f('rail_spacing')/2,0,f('plate_thickness'))) for sign in [-1,1]]
    # Conservative cable keep-out for clearance only; excluded from physical part volume/mass.
    cl=lambda key:v('cell',key)
    if cl('routing_radius')<cl('cable_bend_radius'):raise ValueError('Cable bend below vendor minimum')
    cable_z=cell_bottom+cl('cable_exit_z')
    x0=cl('size')[0]/2+cl('grommet_protrusion');x1=x0+cl('routing_stub');radius=cl('routing_radius')
    path=(cq.Workplane('XY',origin=(0,0,cable_z)).moveTo(x0,0).lineTo(x1,0)
          .threePointArc((x1+radius/math.sqrt(2),-radius+radius/math.sqrt(2)),(x1+radius,-radius))
          .lineTo(x1+radius,cl('routing_end_y')))
    cable=cq.Workplane('YZ',origin=(x0,0,cable_z)).circle(cl('routing_envelope_diameter')/2).sweep(path).val()
    grommet=tube(cl('grommet_diameter'),0,cl('grommet_protrusion')).rotate((0,0,0),(0,1,0),90).translate((cl('size')[0]/2,0,cable_z))
    cable=cable.fuse(grommet).clean()
    cable_clearance=min(cable.distance(rail) for rail in rails)
    if cable_clearance<=0:raise ValueError('Cable keep-out intersects a rail')
    plates=[shapes['SAR-0104'],shapes['SAR-0104'].translate((0,0,upper_base))]
    shield=shapes['SAR-0109'].translate((0,-f('shield_standoff'),f('plate_thickness')))
    port_fitting=shapes['SAR-0506'].rotate((0,0,0),(0,1,0),90).translate((v('plug','head_diameter')/2-p('fitting_stud_length'),0,fixed_tip-v('plug','grip_length')-v('plug','radial_port_from_head_start')))
    shapes['SAR-0001']=cq.Compound.makeCompound(muscle+[coupling,cell,cell_low_eye,cell_high_eye,adjust_block,adjuster,shield,port_fitting]+pins+rails+plates)
    # Pneumatic CAD is a routing layout: unknown components and sensor port are omitted.
    chamber_x=-f('plate_width')
    chamber_z=f('plate_thickness')
    chamber=shapes['SAR-0107'].translate((chamber_x,0,chamber_z))
    caps=[shapes['SAR-0108'].translate((chamber_x,0,z)) for z in [chamber_z-c('cap_thickness'),chamber_z+length]]
    routes=[]
    for i,route_length in enumerate(p('routing_lengths')):
        routes.append(tube(p('tube_od'),p('tube_id'),route_length).rotate((0,0,0),(0,1,0),90).translate((chamber_x,-(i+1)*20,chamber_z)))
    shapes['SAR-0003']=cq.Compound.makeCompound([chamber]+caps+routes+[shapes['SAR-0506'].translate((chamber_x,0,chamber_z+length+c('cap_thickness')-p('fitting_stud_length')))])
    return {'shapes':shapes,'pin_z_mm':[low_pin,muscle_high_pin,cell_low_pin,cell_high_pin],
            'adjuster_length_mm':rod_top-rod_bottom,'cut_latex_braid_length_mm':cut_length,
            'main_cavity_length_mm':length,'caps_port_dead_volume_mm3':2*math.pi/4*v('plug','flow_bore')**2*c('cap_thickness'),
            'load_chain_parts':{'coupler':coupling,'cell':cell,'adjust_block':adjust_block,'adjuster':adjuster},
            'rail_instances':rails,'shield_instance':shield,'cable_keepout':cable,'cable_rail_clearance_mm':cable_clearance}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();g=json.loads((HERE/'geometry.json').read_text())
    result=build(g);shapes=result.pop('shapes')
    rows={r['pn']:r for r in csv.DictReader((HERE/'part_number_register.csv').open(encoding='utf-8-sig'))}
    if set(rows)!=set(shapes):raise ValueError(f'Part register mismatch {set(rows)^set(shapes)}')
    step=args.output/'03_EXPORTS/STEP';step.mkdir(parents=True,exist_ok=True)
    out=args.output/'04_ANALYSIS/successor-concepts';out.mkdir(parents=True,exist_ok=True)
    (out/'geometry.json').write_text(json.dumps(g,indent=2)+'\n')
    expected=oracle.volumes(g,result['adjuster_length_mm']);records={}
    for pn,shape in shapes.items():
        row=rows[pn];stem=f'{pn}_{row["rev"]}_{row["title"].replace(",", "").replace(" ", "-").replace("/", "-")}'
        path=step/(stem+'.STEP');cq.exporters.export(shape,str(path))
        before,after=metrics(shape),metrics(cq.importers.importStep(str(path)).val())
        checks={k:bool(np.allclose(before[k],after[k],rtol=1e-7,atol=1e-6)) for k in ['volume_mm3','centroid_mm','bbox_mm','principal_volume_moments_mm5']}
        volume=expected.get(pn)
        anchor=abs(before['volume_mm3']-volume)<1e-5 if volume is not None else None
        record={'pn':pn,'revision':row['rev'],'status':'CONCEPT / HOLD','accepted':None,
                'cad_route':'CadQuery with independent closed-form oracle where available; native optional per handoff 04',
                'evidence_state':'provisional_design','holds':g['holds'],'metrics':before,
                'step_roundtrip_matches':checks,'independent_volume_mm3':volume,'independent_volume_matches':anchor,
                'omitted_features':g['omitted_features'],'pressure_rating_established':False,'file':str(path)}
        (out/(pn+'_acceptance.json')).write_text(json.dumps(record,indent=2)+'\n')
        if not all(checks.values()) or not before['valid'] or anchor is False:raise RuntimeError(f'Concept geometry check failed {pn}')
        records[pn]=record
        print(pn,'STEP roundtrip OK','oracle',anchor,flush=True)
    screen=oracle.screening(g,result['adjuster_length_mm'])
    # Keep the pressure plan and detailed tests as explicit gates. CAD is not a pressure rating.
    summary={'stage':'CONCEPT','accepted':None,'part_count':len(records),
             'all_original_register_parts_present':True,'added_part':'SAR-0110: double-clevis coupler required for four-pin load chain',
             'pin_z_mm':result['pin_z_mm'],'adjuster_length_mm':result['adjuster_length_mm'],
             'cut_latex_braid_length_mm':result['cut_latex_braid_length_mm'],
             'main_cavity_volume_mm3':oracle.v(g,'chamber','target_main_cavity_volume'),
             'caps_port_dead_volume_mm3':result['caps_port_dead_volume_mm3'],
             'rail_clearances_mm':{name:min(body.distance(rail) for rail in result['rail_instances']) for name,body in result['load_chain_parts'].items()},
             'cable_keepout_to_rail_clearance_mm':result['cable_rail_clearance_mm'],
             'rod_end_to_fork_side_clearance_mm':(oracle.v(g,'frame','fork_gap')-oracle.v(g,'rod_end','eye_width'))/2,
             'ported_plug_minimum_web_mm':oracle.v(g,'plug','head_length')-oracle.v(g,'plug','mechanical_depth')-max(oracle.v(g,'plug','flow_end_from_head_start'),oracle.v(g,'plug','radial_port_from_head_start')+oracle.v(g,'plug','port_major')/2),
             'screening':screen,'omitted_features':g['omitted_features'],
             'seal_zone_note':'Only the free active latex/braid is shown in the muscle assembly; deformed sealing/crimp zones require measured materials and trials. Standalone stock cut-length envelopes include those zones.',
             'pneumatic_note':'Straight tube runs show length allowances, not a connected pressurizable assembly. Regulator, valve and sensor/tee geometry remain omitted.',
             'geometry_sha256':hashlib.sha256((HERE/'geometry.json').read_bytes()).hexdigest()}
    (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
