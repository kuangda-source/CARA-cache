"""Read-only P0 acceptance: source/receipt integrity and full scope accounting."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];d=root/'plans/cara_wc_time_protocol_p0_20261027'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=read(d/'CONTROL_IDENTITY_MATRIX.yaml');m=c['physical_matrix'];r=read(d/'REFERENCE_SHA_INVENTORY.json');t=read(d/'TIME_BOUNDARY_TESTS.json')
assert len(m)==73 and len({v['id'] for v in m})==73
assert sum(v['section'].startswith('A_') for v in m)==26
assert sum(v['section'].startswith('B_') for v in m)==47
assert len({(v['scene'],v['role']) for v in m if v['section']=='B_QUALITY'})==28
assert all(not v['eligible_clean_time'] for v in m if 'WARM' in v['section'] or 'DIAGNOSTIC' in v['section'])
assert c['selection']['candidates']==[.04,.06] and c['selection']['final16_tuning'] is False
assert c['roles']['WC_TUNED_U36']['selected_tau'] is None and not c['GPU_authorized'] and not c['GPU_dispatch_ready']
assert c['old_T_DD'] is None
assert all(sha(root/p)==h for p,h in r['references'].items())
assert all(sha(root/p)==h for p,h in t['source_and_receipt_SHA'].items())
assert not t['real_GPU_equivalence_passed'] and not t['seven_role_production_combination_passed']
e=read(d/'COST_AND_RESOURCE_ENVELOPE.json');assert e['scope']==c['scope'] and e['current_turn_actual']['GPUh']==0
assert e['CPU_scoring_plan']['total_allocated_vCPUh_cap']==28
print('P0_INCREMENT_INTEGRITY_PASS; GPU_DISPATCH_BLOCKED; 73 paths; 28 formal; original references unchanged')
