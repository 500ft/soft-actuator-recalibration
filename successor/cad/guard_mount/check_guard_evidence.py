"""Read delivered executed CAD records with Python's standard library only.

Never extracts files, imports archived code, opens historical host paths, starts
CAD/FE, regenerates geometry or changes an acceptance limit. This checks the
recorded evidence and its byte identity, not an independent CAD replay.
"""
from pathlib import Path, PurePosixPath
import argparse
import csv
import hashlib
import io
import json
import math
import zipfile

HERE = Path(__file__).resolve().parent
PREFIX = 'guard_candidate/'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalized(path):
    return str(path).replace('\\', '/').casefold()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(archive_path, manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    require(manifest['schema'] == 'sar-guard-executed-delivery-v1', 'Unknown delivery schema')
    require(digest(archive_path.read_bytes()) == manifest['archive_sha256'], 'Archive hash differs')
    bindings = {normalized(row['original_source']):row['member'] for row in manifest['files']}
    pins = {row['member']:row for row in manifest['files']}
    require(len(pins) == len(manifest['files']), 'Duplicate archive member pin')
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate ZIP member')
        require(set(names) == set(pins), 'ZIP inventory differs from explicit whitelist')
        payload = {}
        for name in names:
            path = PurePosixPath(name)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,
                    'Unsafe archive member')
            data = archive.read(name)
            require(len(data) == pins[name]['bytes'] and digest(data) == pins[name]['sha256'],
                    'Archived bytes differ: ' + name)
            payload[name] = data
    def read(name):
        return json.loads(payload[name].decode('utf-8-sig'))
    def pin(name, expected):
        require(name in payload and digest(payload[name]) == expected, 'Referenced bytes differ: ' + name)
    def all_checks(value):
        rows = value['checks']
        require(bool(rows), 'No recorded checks')
        passed = all(rows.values()) if isinstance(rows, dict) else all(x['passed'] is True for x in rows)
        require(passed, 'A recorded check failed')
        return len(rows)

    mapped = set()
    unshipped = set()
    reference_pairs = [('path','sha256'), ('file','sha256'), ('source_step','source_step_sha256'),
        ('baseline_snapshot','baseline_snapshot_sha256'), ('redrive_spec_path','redrive_spec_sha256'),
        ('proposal_path','proposal_sha256')]
    def reference_hashes(value):
        if isinstance(value, dict):
            for path_key, hash_key in reference_pairs:
                if isinstance(value.get(path_key), str) and isinstance(value.get(hash_key), str):
                    original = normalized(value[path_key])
                    member = bindings.get(original)
                    if member is None:
                        unshipped.add(original)
                    else:
                        pin(member, value[hash_key])
                        mapped.add(original)
            for child in value.values(): reference_hashes(child)
        elif isinstance(value, list):
            for child in value: reference_hashes(child)
    for name in names:
        if name.endswith('.json'):
            reference_hashes(read(name))

    pilot_name = PREFIX+'pilot_20261114/result.json'
    pilot = read(pilot_name)
    require(pilot['status'] == 'ONE_GUARD_CONCEPT_PILOT_CHECKS_PASS', 'Pilot status')
    require(pilot['accepted'] is None and pilot['pilot_checks_passed'], 'Pilot concept scope')
    pilot_count = all_checks(pilot)
    pin(PREFIX+'guard_spec.json', pilot['spec_sha256'])
    for name, value in pilot['candidate_code_sha256'].items(): pin(PREFIX+name, value)
    pin(PREFIX+'pilot_20261114/SAR-0109_02_CONCEPT-GUARD-PILOT.STEP', pilot['step_sha256'])
    dxf = read(PREFIX+'review_dxf_20261114/result.json')
    require(dxf['status'] == 'REVIEW_DXF_EXPORT_AND_READBACK_PASS' and not dxf['fabrication_authorized'], 'DXF status/scope')
    dxf_count = all_checks(dxf)
    pin(PREFIX+'review_dxf_20261114/SAR-0109_02_CONCEPT-GUARD-PILOT.DXF', dxf['DXF_sha256'])

    mount_root = PREFIX+'mount_subsystem_candidate/'
    nominal_root = mount_root+'nominal_20261114/'
    nominal = read(nominal_root+'result.json')
    require(nominal['status'] == 'GUARD_MOUNT_SUBSYSTEM_CHECKS_PASS_EXISTING_ASSEMBLY_INTERFERENCES_UNRESOLVED', 'Nominal status')
    require(nominal['accepted'] is None and nominal['subsystem_checks_passed'], 'Nominal concept scope')
    require(not nominal['assembly_interference_free'] and not nominal['new_positive_interferences'], 'Nominal interference scope')
    require(len(nominal['existing_unresolved_interferences']) == 2, 'Prior engagement-envelope occurrences')
    nominal_count = all_checks(nominal)
    pin(mount_root+'subsystem_spec.json', nominal['subsystem_spec_sha256'])
    for name, value in nominal['candidate_code_sha256'].items(): pin(mount_root+name, value)
    for name, value in nominal['output_files'].items(): pin(nominal_root+name, value)

    redrive_root = PREFIX+'redrive_candidate/'
    batch_root = redrive_root+'finite_30_20261114/'
    batch = read(batch_root+'result.json')
    proposal = read(mount_root+'REDRIVE_PROPOSAL.json')
    require(batch['status'] == 'FINITE_30_GUARD_MOUNT_REDRIVE_CHECKS_PASS', 'Finite batch status')
    expected_count = len(proposal['cases'])
    require(batch['planned_case_count'] == batch['completed_case_count'] == len(batch['cases']) == expected_count,
            'Finite case count differs from executed proposal')
    require(batch['accepted'] is None and batch['all_registered_cases_passed'] and batch['all_original_inputs_unchanged'],
            'Finite concept/original-input scope')
    require(not batch['physical_criteria_changed'] and not batch['numerical_limits_changed'], 'Acceptance criteria changed')
    require(not batch['native_application_started'] and not batch['pressure_parts_rebuilt'] and not batch['overall_fixture_interference_free'],
            'Finite native/pressure/whole-fixture scope')
    pin(redrive_root+'redrive_spec.json', batch['redrive_spec_sha256'])
    pin(mount_root+'REDRIVE_PROPOSAL.json', batch['proposal_sha256'])
    for name, value in batch['code_sha256'].items(): pin(redrive_root+name, value)

    total_case_checks = 0
    total_steps = 0
    total_terms = 0
    zero_terms = {}
    minimum_gap = math.inf
    case_hashes = {}
    fixed = proposal['all_physical_acceptance_frozen']
    for ordinal, item in enumerate(batch['cases'], 1):
        require(item['case_number'] == ordinal and item['passed'], 'Case order/status')
        name = bindings.get(normalized(item['result']))
        require(name == batch_root+f'{ordinal:02d}/result.json', 'Explicit case binding differs')
        case = read(name)
        case_hashes[ordinal] = digest(payload[name])
        require(case['status'] == 'SYNTHETIC_REDRIVE_CASE_CHECKS_PASS' and case['accepted'] is None and case['case_checks_passed'], 'Case status/scope')
        total_case_checks += all_checks(case)
        require(case['parameter'] == proposal['cases'][ordinal-1] == item['parameter'], 'Registered parameter differs')
        require(case['physical_criteria_frozen'] == fixed, 'Physical criteria differ')
        require(case['affected_geometry'] == item['affected_geometry'] and bool(case['affected_geometry']), 'Parameter affected geometry')
        gap = case['physical_guard_cable_gap_mm']
        require(gap >= fixed['minimum_cable_gap_mm']-1e-6, 'Recorded cable gap below unchanged criterion')
        minimum_gap = min(minimum_gap, gap)
        for filename, value in case['output_STEP_sha256'].items():
            pin(str(PurePosixPath(name).parent/filename), value)
            total_steps += 1
        for label, group in case['full_tensor_terms'].items():
            rule = group['rule']
            floor = max(1e-4, 8*math.ulp(rule['largest_expected_diagonal_mm5']))
            require(math.isclose(floor,rule['absolute_component_mm5'],rel_tol=1e-13,abs_tol=1e-14), 'Tensor floor differs')
            require(len(group['terms']) == 9, 'Incomplete full tensor')
            for term in group['terms']:
                limit = floor+1e-7*abs(term['expected_mm5'])
                error = abs(term['measured_mm5']-term['expected_mm5'])
                require(math.isclose(limit,term['limit_mm5'],rel_tol=1e-13,abs_tol=1e-14), 'Tensor limit differs')
                require(math.isclose(error,term['error_mm5'],rel_tol=1e-13,abs_tol=1e-14), 'Tensor error differs')
                require(error <= limit and math.isclose(limit-error,term['margin_mm5'],rel_tol=1e-13,abs_tol=1e-14), 'Tensor margin fails')
                total_terms += 1
                if term['expected_mm5'] == 0:
                    zero_terms[(ordinal,label,term['i'],term['j'])] = term

    review_paths = [(PREFIX+'PILOT_INDEPENDENT_REVIEW.json','INDEPENDENT_GUARD_PILOT_REVIEW_PASS'),
        (mount_root+'NOMINAL_RESULT_INDEPENDENT_REVIEW.json','INDEPENDENT_NOMINAL_MOUNT_RESULT_REVIEW_PASS'),
        (redrive_root+'FINITE30_RESULT_INDEPENDENT_REVIEW.json','INDEPENDENT_FINITE30_RESULT_REVIEW_PASS')]
    for name, expected_status in review_paths:
        review = read(name)
        require(review['status'] == expected_status and review['accepted'] is None, 'Independent review status/scope')
        all_checks(review)
    finite_review = read(review_paths[-1][0])
    require(finite_review['case_count'] == expected_count and finite_review['total_recorded_case_checks'] == total_case_checks,
            'Independent review count differs')
    require(finite_review['total_tensor_terms_reconciled'] == total_terms and finite_review['exact_expected_zero_terms'] == len(zero_terms),
            'Independent tensor/zero count differs')
    for item in finite_review['case_reviews']:
        require(case_hashes[item['case']] == item['case_result_sha256'], 'Independent case result hash differs')
        require(all(item['independent_checks'].values()), 'Independent case review failed')
    csv_name = redrive_root+'FINITE30_EXPECTED_ZERO_TENSOR_TERMS.csv'
    pin(csv_name, finite_review['expected_zero_terms_csv_sha256'])
    csv_rows = list(csv.DictReader(io.StringIO(payload[csv_name].decode('utf-8-sig'))))
    require(len(csv_rows) == len(zero_terms), 'Raw expected-zero CSV count differs')
    seen = set()
    for row in csv_rows:
        key = (int(row['case']),row['label'],int(row['i']),int(row['j']))
        require(key not in seen and key in zero_terms, 'CSV expected-zero key differs')
        seen.add(key)
        for field in ['expected_mm5','measured_mm5','limit_mm5','error_mm5','margin_mm5']:
            require(float(row[field]) == zero_terms[key][field], 'CSV raw term differs')
    return {'status':'PACKAGED_EXECUTED_GUARD_EVIDENCE_CHECKS_PASS',
        'pilot_recorded_checks':pilot_count, 'DXF_recorded_checks':dxf_count,
        'nominal_recorded_checks':nominal_count, 'registered_parameter_cases':expected_count,
        'recorded_parameter_checks':total_case_checks, 'parameter_STEP_hashes_checked':total_steps,
        'recorded_tensor_terms_reconciled':total_terms,'raw_expected_zero_rows_reconciled':len(zero_terms),
        'minimum_recorded_parameter_cable_gap_mm':minimum_gap,
        'archive_members_checked':len(names),'mapped_historical_source_hashes_checked':len(mapped),
        'unshipped_historical_path_references_not_revalidated':len(unshipped),
        'independent_CAD_replay_performed':False,'native_app_or_FE_started':False,
        'pressure_release_or_whole_fixture_acceptance':False,'successor_research_remains_open':True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=HERE/'SAR_Guard_Mount_Executed_Evidence_2026-11-14.zip')
    parser.add_argument('--manifest',type=Path,default=HERE/'evidence_manifest.json')
    args = parser.parse_args()
    print(json.dumps(check(args.archive,args.manifest),indent=2))
