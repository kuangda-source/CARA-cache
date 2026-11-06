"""Prepare a fair production binding; no server operations or GPU authority."""
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.cara_fast_binding_r2 import execution_view

OUT = ROOT / 'plans/cara_next_stage_20261028/mainline/r2'
BASE = 'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json'
OLD_QUOTE = 'plans/cara_next_stage_20261028/mainline/WHOLE_QUOTE.json'


def main():
    science = json.loads((ROOT / BASE).read_text())
    fit, check = science['FIT'], science['CHECK']
    grids = science['finite_grids']
    physical = []

    def add(phase, section, purpose, member, role, *, audit=False, timing=True):
        slot = dict(id='FAST_R2_%03d' % (len(physical)+1), phase=phase,
                    section=phase+'_'+section, purpose=purpose, member=member,
                    scene=member, role=role, seed=0, timing_enabled=timing,
                    audit_enabled=audit,
                    eligible_clean_time=purpose in ('formal', 'calibration', 'repeat'))
        physical.append(slot)
        return slot['id']

    for role in ['NATIVE35','F19_C','F19_A1','WC_T006','RA_T1','NATIVE22']:
        add('A','WARM','warm',fit[0],role)
    # Reuse the original complete two-input three-arm OFF/ON numerical gate.
    # These twelve paths are deliberately ineligible for clean latency.
    for member in fit:
        for role in ['NATIVE35','ALLD','WC_T006']:
            for timing in (False, True):
                add('A','DIAGNOSTIC','control',member,role,audit=True,timing=timing)
    anchors = {}
    candidates = {}
    for i, member in enumerate(fit):
        anchors[member] = add('A','ANCHOR','formal',member,'NATIVE35')
        order = [role for values in grids.values() for role in values]
        for role in (order if i == 0 else order[::-1]):
            candidates[member+':'+role] = add('A','CALIBRATION','calibration',member,role)
    for role in ['NATIVE35','SHARED25_C','F19_A1','WC_FAST','RA_FAST','NATIVE_K']:
        add('B','WARM','warm',fit[0],role)
    formal = []
    for i, item in enumerate(science['inputs']):
        member = item['name']
        roles = science['formal_roles'] if i % 2 == 0 else science['formal_roles'][::-1]
        for role in roles:
            if role == 'NATIVE35' and member in fit:
                source = dict(slot_id=anchors[member])
            elif role in ('WC_FAST','RA_FAST','NATIVE_K') and member in fit:
                family = science['roles'][role]['family']
                source = dict(family=family,requires_frozen_selection=True,
                              selected_candidate_slot_ids={c:candidates[member+':'+c] for c in grids[family]})
            else:
                source = dict(slot_id=add('B','QUALITY','formal',member,role))
            formal.append(dict(member=member,role=role,source=source))
    for member in fit:
        add('B','REPEAT','repeat',member,'NATIVE35')
    for i, member in enumerate(check):
        for role in (['F19_C','F19_A1'] if i == 0 else ['F19_A1','F19_C']):
            add('B','REPEAT','repeat',member,role)
    counts = dict(collections.Counter(s['purpose'] for s in physical))
    assert len(physical) == 68 and len(formal) == 32
    assert counts == dict(warm=12,control=12,formal=26,calibration=12,repeat=6)
    spec = dict(schema='CARA_FAST_PRODUCTION_BINDING_R2',state='CPU_PREPARATION_NO_GPU_AUTHORIZATION',
        base_manifest=dict(path=BASE,sha256=hashlib.sha256((ROOT/BASE).read_bytes()).hexdigest()),
        reason='R1 CPU fixture always enabled audit. Production must preserve the full twelve-path numerical gate and separate two clean Native anchors; diagnostic copies may not inflate the timing reference.',
        unchanged_science=['four CAL identities and seed0','F19/F18/A1/Uniform19 masks and phase alpha',
                           'WC/RA/Native-k two-candidate grids','32 logical formal positions','Fidelity-v2 prospective protocol'],
        overrides=dict(state='PRODUCTION_BINDING_PREPARATION_NOT_GPU_READY',
            physical_matrix=physical,formal_matrix=formal,
            counts=dict(physical_paths=68,formal_logical_positions=32,independent_prompts=4,
                        stage_A_paths=32,stage_B_paths=36,**counts),
            previous_preparation_scope_paths=60,prior_proposal_is_not_production_ready=True,
            scope_amendment_required_before_GPU_authorization=True,
            minimum_next_card=dict(name='FAST-CAL-A32',physical_paths=32,
                purpose='Complete numerical bridge, clean Native anchors and finite FIT baseline calibration',
                endpoint_competitive_claim=False,does_not_authorize_stage_B=True),
            diagnostic_gate='Two FIT x {Native35, ALLD, WC_T006 PaperPort} x timingOFF/ON; exact guided36, latent, RGB93 and input/RNG equality as applicable',
            clean_timing_rule='audit_enabled=false; in_timing_guided_copies=in_timing_hashes=research_checkpoints=0; diagnostic/warm paths excluded',
            GPU_authorized=False,GPU_dispatch_ready=False,GPU_submissions=0,new_reserved_GPUh=0))
    card = execution_view(science, spec)
    spec['resolved_scope_sha256'] = card['scope_sha256']
    OUT.mkdir(exist_ok=True)
    (OUT/'RUN_SPEC.json').write_text(json.dumps(spec,indent=2)+'\n')
    old = json.loads((ROOT/OLD_QUOTE).read_text())
    hosts = {}
    for host, previous in old['host_quotes'].items():
        native = previous['reference_native_max_seconds']
        positions = []
        for slot in physical:
            kind = science['roles'][slot['role']]['kind']
            factor = 1.0 if kind == 'native' else 1.25 if kind == 'ra' else 1.30 if (
                kind == 'selection' or slot['role'].endswith('_A1')) else 1.20
            diagnostic_factor = 1.5 if slot['audit_enabled'] else 1.0
            positions.append(dict(slot_id=slot['id'],phase=slot['phase'],purpose=slot['purpose'],
                                  role=slot['role'],role_factor=factor,audit_factor=diagnostic_factor,
                                  request_seconds=native*factor*diagnostic_factor))
        phases = {}
        for phase in ('A','B'):
            rows = [r for r in positions if r['phase'] == phase]
            overhead = previous['phases'][phase]['overhead_seconds']
            base_seconds = sum(r['request_seconds'] for r in rows)+sum(overhead.values())
            forecast = base_seconds*1.2/3600
            phases[phase] = dict(physical_paths=len(rows),
                by_purpose_seconds={p:sum(r['request_seconds'] for r in rows if r['purpose']==p)
                                    for p in ('formal','calibration','warm','repeat','control')},
                overhead_seconds=overhead,base_GPUh=base_seconds/3600,
                failure_reserve_factor=1.2,forecast_GPUh=forecast,
                proposed_hard_GPUh=math.ceil(forecast*2)/2,stop_release_margin_seconds=180)
        hosts[host] = dict(reference_native_max_seconds=native,positions=positions,phases=phases,
            complete_forecast_GPUh=sum(p['forecast_GPUh'] for p in phases.values()),
            proposed_whole_hard_GPUh=sum(p['proposed_hard_GPUh'] for p in phases.values()),
            actual_new_GPUh=0)
    quote = dict(schema='CARA_FAST_COMPLETE_ENGINEERING_QUOTE_R2',scope_sha256=card['scope_sha256'],
        base_quote=dict(path=OLD_QUOTE,sha256=hashlib.sha256((ROOT/OLD_QUOTE).read_bytes()).hexdigest()),
        host_quotes=hosts,CPU_scoring=old['CPU_scoring'],storage=old['storage'],
        uncertainty='Historical same-device full-Native maxima with explicit role/audit factors and all overhead; no new GPU rates or guaranteed runtimes.',
        quote_change='Eight additional diagnostic paths replace the incomplete four-control production proposal; clean Native anchors remain separate.',
        planning_pool_GPUh=11,cap_GPUh=226,old_unknown_reserve_GPUh=16.5,
        pool_is_not_reservation_or_authorization=True,GPU_authorized=False,new_reserved_GPUh=0)
    assert all(h['proposed_whole_hard_GPUh'] <= 11 for h in hosts.values())
    (OUT/'WHOLE_QUOTE.json').write_text(json.dumps(quote,indent=2)+'\n')
    print(json.dumps(dict(scope_sha256=card['scope_sha256'],paths=68,stage_A=32,stage_B=36,
        quotes={h:dict(forecast=v['complete_forecast_GPUh'],hard=v['proposed_whole_hard_GPUh'],
                       A_forecast=v['phases']['A']['forecast_GPUh'],A_hard=v['phases']['A']['proposed_hard_GPUh'])
                for h,v in hosts.items()})))


if __name__ == '__main__':
    main()
