"""HBK broad-face exit regression and actual conservative route checks."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import numpy as np

if importlib.util.find_spec('cadquery') is None:
    raise unittest.SkipTest('Host CAD checks require CadQuery; executed Windows results are committed under successor/cad/runs/.')

CAD=Path(__file__).resolve().parents[1]/'cad'
sys.path.insert(0,str(CAD))
import build_concepts as cad
import oracle


class CellCableSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads((CAD/'geometry.json').read_text())
        cls.data=cad.build(cls.g)

    def test_broad_face_exit_matches_drawing_and_actual_cylinder(self):
        result=cad.cell_cable_checks(self.g,self.data)
        self.assertTrue(result['accepted'],result['checks'])
        face=result['cylindrical_faces'][0]
        np.testing.assert_allclose(face['origin_mm'],[31,-12.7,21],rtol=0,atol=1e-6)
        np.testing.assert_allclose(face['y_extents_mm'],[-13.7,-12.7],rtol=0,atol=1e-6)
        self.assertAlmostEqual(face['diameter_mm'],11)
        self.assertEqual(len(self.data['shapes']['SAR-0501'].Solids()),1)

    def test_previous_end_face_exit_is_rejected(self):
        wrong=copy.copy(self.data);wrong['shapes']=dict(self.data['shapes'])
        old_grommet=cad.tube(11,0,1).rotate((0,0,0),(0,1,0),90).translate((40,0,21))
        wrong['shapes']['SAR-0501']=cad.box(80,25.4,60).fuse(old_grommet).clean()
        result=cad.cell_cable_checks(self.g,wrong)
        self.assertFalse(result['accepted'])
        self.assertFalse(result['checks']['grommet_axis_diameter_position'])

    def test_actual_route_starts_outward_and_keeps_vendor_radius(self):
        edges=self.data['cable_path'].Edges()
        np.testing.assert_allclose(edges[0].startPoint().toTuple(),[31,-13.7,self.data['cell_bottom_mm']+21])
        np.testing.assert_allclose(edges[0].tangentAt(0).toTuple(),[0,-1,0])
        arcs=[edge for edge in edges if edge.geomType()=='CIRCLE']
        self.assertEqual(len(arcs),2)
        self.assertTrue(all(edge.radius()>=10 for edge in arcs))
        # The initial section overlaps the rail's Y/Z spans. The right rail's
        # inner X=65 face is closest to the section's X=31+5.5 extreme.
        self.assertAlmostEqual(self.data['cable_rail_clearance_mm'],65-(31+5.5),places=6)

    def test_source_position_and_bend_redrives_keep_independent_checks(self):
        for key in ['cable_exit_x','cable_exit_z','grommet_protrusion','routing_radius']:
            g=copy.deepcopy(self.g);g['cell'][key]['value']*=.99
            data=cad.build(g);result=cad.cell_cable_checks(g,data)
            self.assertTrue(result['accepted'],(key,result['checks']))

    def test_below_minimum_bend_is_rejected(self):
        g=copy.deepcopy(self.g);g['cell']['routing_radius']['value']=9.9
        with self.assertRaisesRegex(ValueError,'Cable bend'):
            cad.make_cable_keepout(g,self.data['cell_bottom_mm'])


if __name__=='__main__':unittest.main()
