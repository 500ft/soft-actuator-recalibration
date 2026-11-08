"""Render the actual concept solids and a symbolic pneumatic routing diagram."""
import argparse
import json
import math
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

import numpy as np
import pyvista as pv

import build_concepts as cad

HERE=Path(__file__).resolve().parent


def mesh(shape):
    points,triangles=shape.tessellate(0.15,0.1)
    return pv.PolyData(np.asarray([p.toTuple() for p in points]),np.asarray([[3,*t] for t in triangles],dtype=np.int64).ravel()).clean()


def schematic(g,path):
    root=Element('svg',xmlns='http://www.w3.org/2000/svg',width='1200',height='360',viewBox='0 0 1200 360')
    SubElement(root,'rect',width='1200',height='360',fill='#f5f7fa')
    def text(x,y,value,size=17,color='#223344'):
        item=SubElement(root,'text',x=str(x),y=str(y),fill=color,attrib={'font-family':'Arial','font-size':str(size)})
        item.text=value
    text(30,35,'SAR-0003 — single-channel functional routing',25)
    text(30,63,'CONCEPT / HOLD — symbolic diagram; component ports and actual tubing routes are not released',16,'#8b2839')
    nodes=[(30,'Regulated supply','Part pending'),(260,'Isolation valve','Part pending'),(490,'Pressure sensor + tee','O14b: geometry omitted'),(720,'Reference chamber','SAR-0107 / SAR-0108'),(950,'Muscle, fixed end','SAR-0002')]
    for x,title,subtitle in nodes:
        SubElement(root,'rect',x=str(x),y='110',width='200',height='80',rx='8',fill='white',stroke='#5b7088',attrib={'stroke-dasharray':'6 4' if x in [30,260,490] else 'none'})
        text(x+12,141,title,16);text(x+12,168,subtitle,13)
        if x<950:
            SubElement(root,'path',d=f'M {x+200} 150 L {x+225} 150 l -6 -4 m 6 4 l -6 4',fill='none',stroke='#223344',attrib={'stroke-width':'2'})
    lengths=g['pneumatic']['routing_lengths']['value']
    text(42,227,f'Initial tube allowances: supply→valve {lengths[0]:g} mm; valve→reference {lengths[1]:g} mm (includes unresolved tee); reference→muscle {lengths[2]:g} mm.',15)
    text(42,257,'The ported muscle fitting is on the fixed end. Clamp the hose slack loop to the frame; keep its force out of the load cell.',15)
    text(42,287,'The load cell is on the closed end. Relief sizing, seals, leak limit and P1–P7 remain qualification inputs.',15)
    text(42,328,'No purchase, fabrication, testing or pressurization is authorized.',17,'#8b2839')
    ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    g=json.loads((HERE/'geometry.json').read_text());data=cad.build(g)
    v=lambda group,key:g[group][key]['value']
    plotter=pv.Plotter(off_screen=True,shape=(1,2),window_size=(1600,1100))
    bodies=[]
    for solid in data['shapes']['SAR-0001'].Solids():
        b=solid.BoundingBox();opacity=1.0;color='#b5c4ce'
        if abs(b.ylen-v('frame','shield_thickness'))<1e-5 and b.zlen>500:color='#74a8bd';opacity=0.12
        elif abs(b.zlen-v('specimen','active_length'))<1e-5:color='#6d91b0';opacity=0.45
        elif b.zlen<100 and b.xlen<35 and b.ylen<35:color='#ce9768'
        elif abs(b.xlen-v('cell','size')[0])<1e-5:color='#61798d'
        surface=mesh(solid)
        edges=surface.extract_feature_edges(feature_angle=35,boundary_edges=True,non_manifold_edges=False,manifold_edges=False)
        bodies.append((surface,edges,color,opacity))
    for column,focal,scale in [(0,[0,0,320],370),(1,[0,0,430],135)]:
        plotter.subplot(0,column);plotter.set_background('#f5f7fa')
        for surface,edges,color,opacity in bodies:
            plotter.add_mesh(surface,color=color,opacity=opacity,smooth_shading=True,split_sharp_edges=True,ambient=0.35,specular=0.2)
            if opacity==1:plotter.add_mesh(edges,color='#40515d',line_width=0.7)
        if column==1:
            plotter.add_mesh(mesh(data['cable_keepout']),color='#b35070',opacity=0.45)
        plotter.camera_position=[(np.asarray(focal)+np.array([750,-1200,330])).tolist(),focal,[0,0,1]]
        plotter.camera.parallel_projection=True;plotter.camera.parallel_scale=scale
        plotter.add_text('SAR-0001 | Rig concept' if column==0 else 'Load chain and cable keep-out',position='upper_left',font_size=14,color='#223344')
        plotter.add_text('CONCEPT / HOLD — NO PHYSICAL WORK',position='lower_left',font_size=11,color='#8b2839')
        plotter.add_axes()
    plotter.screenshot(str(args.output/'SAR-0001_01_review.png'));plotter.close()
    schematic(g,args.output/'SAR-0003_01_routing.svg')
    print(args.output/'SAR-0001_01_review.png')


if __name__=='__main__':main()
