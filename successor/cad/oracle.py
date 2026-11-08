"""Independent algebra and quadrature for the successor concept models. No CAD imports."""
import math

from scipy.integrate import quad


def v(g, group, key):
    return g[group][key]['value']


def chamber_length(g):
    return v(g, 'chamber', 'target_main_cavity_volume')/(math.pi*(v(g, 'chamber', 'bore_diameter')/2)**2)


def plug_volume(g, ported):
    q = lambda k: v(g, 'plug', k)
    root, crest, head = q('root_diameter')/2, q('crest_diameter')/2, q('head_diameter')/2
    pitch = q('barb_pitch')
    volume = math.pi*(root**2*q('grip_length')+head**2*q('head_length'))
    volume += q('barb_count')*math.pi*pitch*((root**2+root*crest+crest**2)/3-root**2)
    volume -= math.pi*(q('mechanical_major')/2)**2*q('mechanical_depth')
    if ported:
        r, p = q('flow_bore')/2, q('port_major')/2
        length = q('grip_length')+q('flow_end_from_head_start')
        zport = q('grip_length')+q('radial_port_from_head_start')
        # Volume of the radial bore inside the circular head, accounting for the curved outer wall.
        radial, _ = quad(lambda y: 2*math.sqrt(max(0, p*p-y*y))*math.sqrt(head*head-y*y), -p, p, epsabs=1e-9)
        def overlap_section(z):
            band = math.sqrt(max(0, p*p-(z-zport)**2))
            if band >= r:
                return math.pi*r*r/2
            return band*math.sqrt(max(0, r*r-band*band))+r*r*math.asin(band/r)
        low, high = max(0, zport-p), min(length, zport+p)
        overlap, _ = quad(overlap_section, low, high, epsabs=1e-9,
                          points=[zport-math.sqrt(p*p-r*r)] if p>r and low<zport-math.sqrt(p*p-r*r)<high else None)
        volume -= math.pi*r*r*length+radial-overlap
    return volume


def volumes(g, adjuster_length=None):
    a = lambda group, key: v(g, group, key)
    annulus = lambda od, id, length: math.pi/4*(od*od-id*id)*length
    c, f = 'chamber', 'frame'
    length = chamber_length(g)
    results = {
        'SAR-0101': plug_volume(g, True), 'SAR-0102': plug_volume(g, False),
        'SAR-0103': annulus(a('ferrule','od'), a('ferrule','id'), a('ferrule','length')),
        'SAR-0107': annulus(a(c,'barrel_od'),a(c,'bore_diameter'),length)
                    +2*annulus(a(c,'flange_od'),a(c,'barrel_od'),a(c,'flange_length'))
                    -2*a(c,'bolt_count')*math.pi/4*a(c,'bolt_major')**2*a(c,'bolt_depth'),
        'SAR-0108': (math.pi/4*(a(c,'flange_od')**2-a('plug','flow_bore')**2)
                     -a(c,'bolt_count')*math.pi/4*a(c,'bolt_clearance')**2)*a(c,'cap_thickness'),
        'SAR-0503': math.prod(a(f,'rail_section'))*a(f,'rail_length'),
        'SAR-0504': annulus(a('specimen','bladder_od'),a('specimen','bladder_id'),a('specimen','active_length')+2*a('plug','grip_length')),
        'SAR-0505': annulus(a('specimen','bladder_od')+2*a('specimen','braid_wall'),a('specimen','bladder_od'),a('specimen','active_length')+2*a('plug','grip_length')),
        'SAR-0501': math.prod(a('cell','size'))
    }
    hole_area=math.pi/4*a(f,'pin_diameter')**2
    results['SAR-0104']=(a(f,'plate_width')*a(f,'plate_depth')-math.pi/4*(4*a(f,'end_bolt_clearance')**2+a(f,'adjuster_clearance')**2))*a(f,'plate_thickness')+2*a(f,'ear_width')*a(f,'ear_thickness')*a(f,'ear_height')-2*a(f,'ear_thickness')*hole_area
    bx,by,bz=a(f,'adjust_block_size')
    results['SAR-0105']=bx*by*bz+2*a(f,'ear_width')*a(f,'ear_thickness')*a(f,'ear_height')-math.pi/4*a(f,'adjust_thread_major')**2*bz-2*a(f,'ear_thickness')*hole_area
    rp,rh=a(f,'pin_diameter')/2,a(f,'pin_cross_hole')/2
    removed,_=quad(lambda x:4*math.sqrt(max(0,rh*rh-x*x))*math.sqrt(rp*rp-x*x),-rh,rh,epsabs=1e-9)
    results['SAR-0106']=math.pi*rp*rp*a(f,'pin_length')+math.pi/4*a(f,'pin_head_diameter')**2*a(f,'pin_head_length')-removed
    results['SAR-0109']=a(f,'plate_width')*a(f,'shield_thickness')*a(f,'rail_length')
    cu=lambda key:a('coupler',key)
    h=cu('pin_spacing')+2*cu('pin_end_distance')
    results['SAR-0110']=cu('width')*cu('depth')*h-4*cu('width')*a(f,'fork_gap')*cu('pin_end_distance')-2*hole_area*(cu('depth')-a(f,'fork_gap'))
    eye_r,stud_r=a('rod_end','eye_diameter')/2,a('rod_end','stud_diameter')/2
    join=-eye_r+stud_r
    def overlap_at_z(z):
        band=min(stud_r,math.sqrt(max(0,eye_r*eye_r-z*z)))
        return 2*(band*math.sqrt(max(0,stud_r*stud_r-band*band))+stud_r*stud_r*math.asin(band/stud_r))
    overlap,_=quad(overlap_at_z,-eye_r,join,epsabs=1e-9,points=[-math.sqrt(eye_r*eye_r-stud_r*stud_r)])
    results['SAR-0502']=annulus(a('rod_end','eye_diameter'),a('rod_end','eye_bore'),a('rod_end','eye_width'))+math.pi*stud_r**2*(a('rod_end','centre_to_stud_tip')+join)-overlap
    p=lambda key:a('pneumatic',key)
    results['SAR-0506']=math.pi/4*a('plug','port_major')**2*p('fitting_stud_length')+math.sqrt(3)/2*p('fitting_hex_af')**2*p('fitting_stud_length')+math.pi/4*p('fitting_hex_af')**2*(p('fitting_length')-2*p('fitting_stud_length'))-math.pi/4*p('tube_id')**2*p('fitting_length')
    if adjuster_length is not None:
        free_fraction=a('specimen','active_length')/(a('specimen','active_length')+2*a('plug','grip_length'))
        results['SAR-0002']=results['SAR-0101']+results['SAR-0102']+2*results['SAR-0103']+2*results['SAR-0502']+free_fraction*(results['SAR-0504']+results['SAR-0505'])
        results['SAR-0001']=results['SAR-0002']+results['SAR-0110']+results['SAR-0501']+2*results['SAR-0502']+results['SAR-0105']+math.pi/4*a(f,'adjust_thread_major')**2*adjuster_length+results['SAR-0109']+4*results['SAR-0106']+2*results['SAR-0503']+2*results['SAR-0104']+results['SAR-0506']
        results['SAR-0003']=results['SAR-0107']+2*results['SAR-0108']+results['SAR-0506']+math.pi/4*(p('tube_od')**2-p('tube_id')**2)*sum(p('routing_lengths'))
    return results


def screening(g, adjuster_length):
    a = lambda group, key: v(g, group, key)
    diameter, active = a('specimen','bladder_od')+a('specimen','braid_wall'), a('specimen','active_length')
    pressure = a('specimen','working_pressure')/1000  # MPa = N/mm2
    cases = []
    for degrees in a('specimen','angle_cases'):
        theta = math.radians(degrees)
        D90 = diameter/math.sin(theta)
        force = pressure*math.pi*D90**2/4*(3*math.cos(theta)**2-1)
        slope = pressure*math.pi*D90**2*3*math.cos(theta)**2/(2*active)
        cases.append({'angle_deg': degrees, 'blocked_force_N': force,
                      'proof_pressure_force_N': force*a('specimen','proof_pressure')/a('specimen','working_pressure'),
                      'muscle_stiffness_N_per_mm': slope, 'required_series_stiffness_N_per_mm': 99*slope})
    E = a('material','aluminum_E')
    rail_k = 2*E*a('frame','rail_area')/a('frame','rail_length')
    # Simply-supported end-plate strip, central force. Joint and clevis compliance omitted.
    inertia = a('frame','plate_depth')*a('frame','plate_thickness')**3/12
    plate_k = 48*E*inertia/a('frame','rail_spacing')**3
    pitch = a('frame','adjust_thread_pitch')
    rod_core = a('frame','adjust_thread_major')-1.226869*pitch
    rod_k = a('material','steel_E')*math.pi*rod_core**2/4/adjuster_length
    stiffness = []
    for displacement in a('cell','displacement_cases'):
        cell_k = a('cell','rated_force')/displacement
        combined = 1/(1/rail_k+2/plate_k+1/cell_k+1/rod_k)
        slope = max(c['muscle_stiffness_N_per_mm'] for c in cases)
        stiffness.append({'cell_rated_displacement_mm': displacement, 'series_stiffness_N_per_mm': combined,
                          'predicted_force_bias_fraction': slope/(combined+slope),
                          'passes_1pct_screen': combined>=99*slope})
    ri, ro = a('chamber','bore_diameter')/2, a('chamber','barrel_od')/2
    p = a('specimen','proof_pressure')/1000
    return {'result_kind':'screening_prediction', 'force_cases':cases,
            'frame_components_N_per_mm':{'two_rails':rail_k,'one_plate_strip':plate_k,'adjuster_rod':rod_k},
            'frame_stiffness_cases':stiffness,
            'frame_limitations':'Clevis, thread, plate-joint, support and contact compliance omitted. Not a frame qualification; SAR-SIM-02 and a dial-gauge load test remain required.',
            'reference_main_cavity_length_mm':chamber_length(g),
            'reference_barrel_inner_hoop_MPa':p*(ro*ro+ri*ri)/(ro*ro-ri*ri),
            'reference_cap_simple_plate_stress_MPa':3*p*ri*ri/(4*a('chamber','cap_thickness')**2),
            'pressure_rating_established':False,'physical_tests_performed':False}
