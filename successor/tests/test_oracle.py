"""Independent mechanics identities for the executed successor screening calculation."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

CAD=Path(__file__).resolve().parents[1]/'cad'
sys.path.insert(0,str(CAD))
import oracle


class ScreeningIdentities(unittest.TestCase):
    def setUp(self):self.g=json.loads((CAD/'geometry.json').read_text())

    def test_force_from_pressure_volume_virtual_work(self):
        g=self.g;L=oracle.v(g,'specimen','active_length')
        diameter=oracle.v(g,'specimen','bladder_od')+oracle.v(g,'specimen','braid_wall')
        P=oracle.v(g,'specimen','working_pressure')/1000
        rows=oracle.screening(g,89)['force_cases']
        for row in rows:
            theta=math.radians(row['angle_deg']);strand=L/math.cos(theta)
            turns=L*math.tan(theta)/(math.pi*diameter)
            def volume(length):return (strand*strand-length*length)*length/(4*math.pi*turns*turns)
            step=1e-3
            force=-P*(volume(L+step)-volume(L-step))/(2*step)
            self.assertAlmostEqual(force,row['blocked_force_N'],places=6)

    def test_pressure_scaling_and_neutral_braid_angle(self):
        g=copy.deepcopy(self.g);baseline=oracle.screening(g,89)['force_cases'][0]
        g['specimen']['working_pressure']['value']/=2
        half=oracle.screening(g,89)['force_cases'][0]
        self.assertAlmostEqual(half['blocked_force_N']*2,baseline['blocked_force_N'])
        g['specimen']['angle_cases']['value']=[math.degrees(math.acos(1/math.sqrt(3)))]
        self.assertLess(abs(oracle.screening(g,89)['force_cases'][0]['blocked_force_N']),1e-10)

    def test_reference_volume_is_solved_for_different_bores(self):
        for diameter in [14.0,16.0,18.0]:
            g=copy.deepcopy(self.g);g['chamber']['bore_diameter']['value']=diameter
            cavity=math.pi*(diameter/2)**2*oracle.chamber_length(g)
            self.assertAlmostEqual(cavity,g['chamber']['target_main_cavity_volume']['value'],places=9)

    def test_cell_compliance_is_in_series_and_reduces_force(self):
        result=oracle.screening(self.g,89)
        low,high=result['frame_stiffness_cases']
        self.assertLess(high['series_stiffness_N_per_mm'],low['series_stiffness_N_per_mm'])
        muscle=result['force_cases'][0]['muscle_stiffness_N_per_mm']
        for row in [low,high]:
            k=row['series_stiffness_N_per_mm']
            retained_force_fraction=1/(1+muscle/k)
            self.assertAlmostEqual(1-retained_force_fraction,row['predicted_force_bias_fraction'])


if __name__=='__main__':unittest.main()
