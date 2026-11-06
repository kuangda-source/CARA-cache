"""Build the mainline-only prospective manifest, action audit and complete quote."""
import collections
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_fast_spec_r1 import (audit_actions, digest, policy_from_mask,
                                    profile_from, uniform_mask)
OUT = ROOT/'plans/cara_next_stage_20261028/mainline'


def read(path):
    return json.loads((ROOT/path).read_text())


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main():
    OUT.mkdir(exist_ok=True)
    old = read('plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml')
    dev = read('manifests/cara_DEV128_scope_r1_20261026.json')
    design = read('plans/cara_next_stage_20261028/experiment_registry.json')
    schedules = read('reports/cara_PG_Native18to35_committed_scheduler_CPU_20261023.json')['rows']
    profile = profile_from(dev['profile'])
    uniform, coordinates = uniform_mask(old['schedule'], profile, 19)
    roles = {}
    for name, mask, corrections in [
        ('SHARED25_C', design['masks']['Shared25_C'], []),
        ('F19_C', design['masks']['F19'], []),
        ('F19_A1', design['masks']['F19'], design['masks']['F19_A1']),
        ('UNIFORM19_C', uniform, []),
        ('F18_C', design['masks']['F18'], []),
        ('F18_A1', design['masks']['F18'], design['masks']['F18_A1'])]:
        policy = policy_from_mask(profile, mask, corrections)
        roles[name] = dict(kind='policy', requested_steps=35, policy=policy)
    assert roles['SHARED25_C']['policy']['fingerprint'] == dev['roles']['SHARED25_C']['policy']['fingerprint']
    roles['NATIVE35'] = dict(kind='native', requested_steps=35)
    for k in (22, 24):
        roles['NATIVE'+str(k)] = dict(kind='native', requested_steps=k)
    for name, tau in [('WC_T006', .06), ('WC_T008', .08)]:
        roles[name] = dict(kind='wc', requested_steps=35,
                          settings={**old['roles']['WC_PAPER_PORT_U36']['settings'],
                                    'worldcache_rel_l1_thresh': tau}, paper_exact=False)
    base = old['roles']['RA_LOCAL_U36']
    for name, factor in [('RA_T1', 1.), ('RA_T15', 1.5)]:
        spec = copy.deepcopy(base['RA_spec']); spec['threshold'] *= factor
        roles[name] = dict(kind='ra', requested_steps=35, RA_spec=spec,
                          calibration_fingerprint=base['calibration_fingerprint'], paper_exact=False)
    roles['ALLD'] = dict(kind='allD', requested_steps=35,
                        settings=copy.deepcopy(old['roles']['WC_WRAPPER_ALLD_U36']['settings']))
    roles['WC_FAST'] = dict(kind='selection', family='WC')
    roles['RA_FAST'] = dict(kind='selection', family='RA')
    roles['NATIVE_K'] = dict(kind='selection', family='NATIVE_K')
    inputs = [{**r, 'partition': 'FIT' if i < 2 else 'CHECK'} for i, r in enumerate(old['requests'])]
    fit = [r['name'] for r in inputs[:2]]; check = [r['name'] for r in inputs[2:]]
    grids = dict(WC=['WC_T006', 'WC_T008'], RA=['RA_T1', 'RA_T15'],
                 NATIVE_K=['NATIVE22', 'NATIVE24'])
    formal_roles = ['NATIVE35', 'SHARED25_C', 'F19_C', 'F19_A1', 'UNIFORM19_C',
                    'WC_FAST', 'RA_FAST', 'NATIVE_K']
    slots = []
    def add(phase, purpose, member, role, timing=True):
        slots.append(dict(id='FAST_R1_%03d' % (len(slots)+1), phase=phase, purpose=purpose,
                          member=member, role=role, seed=0, timing_enabled=timing,
                          eligible_clean_time=purpose in ('formal', 'calibration', 'repeat')))
        return slots[-1]['id']
    for role in ['NATIVE35', 'F19_C', 'F19_A1', 'WC_T006', 'RA_T1', 'NATIVE22']:
        add('A', 'warm', fit[0], role)
    # Balanced candidate order between FIT inputs; every rejected candidate counts.
    references = {}; candidates = {}
    for i, member in enumerate(fit):
        references[member] = add('A', 'formal', member, 'NATIVE35')
        add('A', 'control', member, 'NATIVE35', False)
        add('A', 'control', member, 'ALLD')
        order = [r for values in grids.values() for r in values]
        for role in (order if i == 0 else order[::-1]):
            candidates[member+':'+role] = add('A', 'calibration', member, role)
    for role in ['NATIVE35', 'SHARED25_C', 'F19_A1', 'WC_FAST', 'RA_FAST', 'NATIVE_K']:
        add('B', 'warm', fit[0], role)
    formal = []
    for i, item in enumerate(inputs):
        member = item['name']; order = formal_roles if i % 2 == 0 else formal_roles[::-1]
        for role in order:
            if role == 'NATIVE35' and member in fit:
                source = dict(slot_id=references[member])
            elif role in ('WC_FAST', 'RA_FAST', 'NATIVE_K') and member in fit:
                family = roles[role]['family']
                source = dict(selected_candidate_slot_ids={c: candidates[member+':'+c] for c in grids[family]},
                              family=family, requires_frozen_selection=True)
            else:
                source = dict(slot_id=add('B', 'formal', member, role))
            formal.append(dict(member=member, role=role, source=source))
    # Fresh FIT Native after the reload checks phase drift; two CHECK pairs repeat Fast.
    for member in fit:
        add('B', 'repeat', member, 'NATIVE35')
    for i, member in enumerate(check):
        for role in (['F19_C', 'F19_A1'] if i == 0 else ['F19_A1', 'F19_C']):
            add('B', 'repeat', member, role)
    counts = dict(collections.Counter(s['purpose'] for s in slots))
    assert len(slots) == 60 and len(formal) == 32 and counts == dict(warm=12, formal=26, control=4, calibration=12, repeat=6)
    # Full execution identity, never mask alone. Physical repeats are retained.
    for role in roles.values():
        role['execution_identity_sha256'] = digest(role)
    protocol = dict(name='Fidelity-v2-fast-r1', state='PROSPECTIVE_SPEC_BEFORE_NEW_OUTPUT_ACCESS',
        primary='original lpips 0.1.4 Alex v0.1; RGB/127.5-1; all93 mean; prompt equal',
        PSNR='10*log10(1 / mean_video_RGB_squared_error); zero MSE => string +inf',
        SSIM=dict(implementation='piq 0.8.0 ssim', kernel_size=11, kernel_sigma=1.5,
                  data_range=1., k1=.01, k2=.03, downsample=False, reduction='none',
                  channels='RGB arithmetic mean', aggregation='all93 frame arithmetic mean'),
        temporal='mean abs((I[f+1]-N[f+1])-(I[f]-N[f])); all92 pairs; one video statistic',
        detail='forward x/y pixel differences; mean absolute gradient residual, mean squared gradient energy ratio',
        zero_reference_gradient='ratio null with explicit ZERO_REFERENCE_ENERGY status',
        frame_curves='all93 Alex; higher q95 and first worst frame index',
        geometry=[93,432,768,3], fps=16, color='decoded RGB24 uint8 /255; no resize/trim/alignment',
        blind_review='diagnostic pending; no human agreement claim or retrospective automatic veto',
        old_metrics_alpha_and_request_gates_unchanged=True, supplemental_veto_thresholds=None)
    write('FIDELITY_PROTOCOL.json', protocol)
    card = dict(schema='CARA_FAST_PREPARATION_R1', state='CPU_PREPARATION_NOT_GPU_READY',
        source_parent_commit='814ce3d89ae88e5bcb37bf52d17f3f1d52d278b9',
        profile=dev['profile'], schedule=old['schedule'],
        schedules=[s for s in schedules if s['requested_steps'] in (22,24,35)],
        inputs=inputs, roles=roles, finite_grids=grids, FIT=fit, CHECK=check,
        formal_roles=formal_roles, formal_matrix=formal, physical_matrix=slots,
        counts=dict(physical_paths=60, formal_logical_positions=32, independent_prompts=4,
                    stage_A_paths=24, stage_B_paths=36, **counts),
        original_planning_max=56, revised_scope_proposal_delta=4,
        scope_amendment_required_before_GPU_authorization=True,
        minimum_next_card=dict(name='FAST-CAL-A24', physical_paths=24, purpose='two-FIT P0 and finite baseline calibration',
                               endpoint_competitive_claim=False, does_not_authorize_stage_B=True),
        role_alias_policy='Formal FIT selected calibration aliases reuse complete same-identity video/time; no added sample',
        warm_policy='Six full engine warm slots per load. Scalar threshold and same-shape policy changes share kernels; actual GPU warm adequacy remains unvalidated.',
        selection='Complete 2FIT x 3families x 2candidates; Native T_DD/1.5; <=5% worst-prompt eligibility then Alex; otherwise nearest labelled UNMATCHED',
        phase_boundary='Release A, settle and score FIT only, freeze complete selection, admit B on SAME physical GPU; other device requires new scope',
        timing_analysis='Prompt means of formal plus registered clean repeats, then equal prompt weighting; report both clocks and phase-A-only sensitivity for FIT baselines.',
        stop_rules=['Identity/nonfinite/control failure stops at fixed denominator', 'A release precedes CPU selection',
                    '90C unchanged; interrupted clocks excluded from clean means with failure retained',
                    'No success-based dropping of CHECK; no automatic retry/resume/alternative host'],
        GPU_authorized=False, GPU_dispatch_ready=False, GPU_submissions=0, new_reserved_GPUh=0,
        fidelity_protocol_ref='plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json',
        fidelity_protocol_sha256=digest(protocol), final_and_reserve_inputs_accessed=False,
        historical_artifacts_reused_as_new_clean_time=False)
    card['scope_sha256'] = digest(card)
    write('RUN_MANIFEST.json', card)
    write('MASK_ACTION_AUDIT.json', dict(schedule_sha256=digest(old['schedule']),
        normalization='x_i=(sigma_1-sigma_i)/(sigma_1-terminal_sigma); terminal has no update',
        uniform_rule='Start protected {1..7,36}, add maximum nearest-distance point; exact rational tie -> smaller update index',
        normalized_sigma=coordinates, Uniform19=uniform,
        protection='Inherited engineering constraints, not physical necessity',
        counts={k:v['policy']['counts'] for k,v in roles.items() if v['kind']=='policy'},
        actions={k:audit_actions(v['policy']) for k,v in roles.items() if v['kind']=='policy'},
        actual_updates=36, branches_per_D_pair=2, terminal_model_calls=0,
        F18_step9=dict(action='C',source=7,age=2),
        A_alpha_rule='Unchanged alpha_at(BETA1_ONE_PHASE,t): 1 before25, .5 from25; A1 positions here all1'))
    quote(card)
    print(json.dumps(dict(paths=len(slots),stage_A=24,stage_B=36,Uniform19=uniform,scope_sha256=card['scope_sha256'])))


def quote(card):
    source='plans/cara_wc_time_protocol_r1_20261027/WHOLE_QUOTE.json'
    old = read(source)
    latest = read('reports/cara_fast_readonly_preparation_20261028.json')['four_card']
    hosts = {}
    for host, oldhost in old['hosts'].items():
        n = oldhost['reference_native_max']
        # Actual role timings where available; all new Fast/threshold paths use
        # full-Native ceilings with separate explicit overhead, never D-count speed.
        positions=[]
        for s in card['physical_matrix']:
            role=card['roles'][s['role']]; kind=role['kind']
            if kind == 'native': factor=1.0
            elif kind in ('wc','allD'): factor=1.20
            elif kind == 'ra': factor=1.25
            elif kind == 'policy': factor=1.30 if 'A1' in s['role'] else 1.20
            else: factor=1.30
            multiplier=1.5 if s['purpose']=='control' else 1.0
            positions.append(dict(slot_id=s['id'],phase=s['phase'],role=s['role'],purpose=s['purpose'],
                                  request_seconds=n*factor*multiplier,
                                  base='historical same-host full-Native max',role_factor=factor,
                                  control_save_factor=multiplier,measured_new_rate=None))
        phases={}
        for phase in ('A','B'):
            selected=[v for v in positions if v['phase']==phase]
            overhead=dict(model_load=oldhost['phases'][phase]['overhead_seconds']['model_load'],
                          checks_and_compile=180,save_hash_and_IO=300,held_thermal_wait=300,
                          release_and_settlement=180)
            subtotal=sum(s['request_seconds'] for s in selected)+sum(overhead.values())
            phases[phase]=dict(physical_paths=len(selected),by_purpose_seconds={p:sum(s['request_seconds'] for s in selected if s['purpose']==p) for p in ('formal','calibration','warm','repeat','control')},
                               overhead_seconds=overhead,base_GPUh=subtotal/3600,
                               failure_reserve_factor=1.20,forecast_GPUh=subtotal*1.20/3600,
                               proposed_hard_GPUh=math.ceil(subtotal*1.20/3600*2)/2,
                               stop_release_margin_seconds=180)
        hosts[host]=dict(reference_native_max_seconds=n,positions=positions,phases=phases,
                         complete_forecast_GPUh=sum(v['forecast_GPUh'] for v in phases.values()),
                         proposed_whole_hard_GPUh=sum(v['proposed_hard_GPUh'] for v in phases.values()),
                         actual_new_GPUh=0,quote_type='HISTORICAL_ANCHORED_ENGINEERING_NOT_NEW_MEASURED_SPEED')
    quote=dict(scope_sha256=card['scope_sha256'],host_quotes=hosts,
        source_sha256={source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()},
        current_ledger_readonly=dict(observed_unix=latest['observed_unix'],sha256=latest['ledger_sha256'],**latest['ledger_fields']),
        stale_two_card_ledger_ignored=True,
        rate_uncertainty='No clean F19/WC-fast/RA-fast/Native22/24 T_DD rate. Native ceiling plus role-specific factors are explicit allowances, not speed estimates.',
        CPU_scoring=dict(stage_A=dict(pairs_max=12,cores=2,memory_GiB=8,wall_cap_hours=2),
                         stage_B=dict(pairs_max=32,cores=2,memory_GiB=8,wall_cap_hours=4),
                         allocated_vCPUh_cap=12,allocation_GiBh_cap=48,
                         includes='decode+SHA+Alex+SSIM+PSNR+temporal+detail+frame curves+failed slots; only after GPU release',
                         estimated_wall_hours=None,
                         uncertainty='New all93 supplemental scorer lacks full-resolution CPU throughput probe; cap is resource boundary, not measured completion guarantee',
                         large_historical_batch_authorized=False),
        storage=dict(new_output_bound_GiB=12,same_disk_repeated_archive_read=False,
                     raw_branch_asset_collection=False,logs_on_separate_filesystem=True,
                     prior_WC73_loop_HDD_not_default_output=True),
        billing='One central envelope, A+B only once; minimum A24 is a prefix not an additional independent card; no calibration reuse counted as new sample.',
        GPU_authorized=False,new_reserved_GPUh=0,old_unknown_reserve_GPUh=16.5,cap_GPUh=226)
    probes={}
    for host,ref in [('four_card','reports/cara_fast_four_card_CPU_terminal_r1_20261028.json'),
                     ('two_card','reports/cara_fast_two_card_CPU_capture4_r1_20261028.json')]:
        if (ROOT/ref).exists():
            capture=read(ref);proof=capture.get('CPU_proof')
            if proof and proof.get('fidelity',{}).get('status')=='SYNTHETIC_FIDELITY_AND_REAL_ALEX_CPU_CONTROLS_PASS':
                probes[host]=dict(reference=ref,sha256=hashlib.sha256((ROOT/ref).read_bytes()).hexdigest(),
                    seconds_per_full_resolution_synthetic_frame=proof['fidelity']['full_resolution_frame_wall_seconds'],
                    original_container_exit_code=capture['container_state']['ExitCode'],
                    scope='Completed scoring component only, not whole-batch CPU or lifecycle acceptance')
    if len(probes)==2:
        slow=max(v['seconds_per_full_resolution_synthetic_frame'] for v in probes.values())
        quote['CPU_scoring']['synthetic_frame_probes']=probes
        for phase,pairs in [('stage_A',12),('stage_B',32)]:
            quote['CPU_scoring'][phase].update(engineering_forecast_wall_hours=(pairs*93*slow*1.5+600)/3600,
                frame_cost_factor=1.5,import_model_load_SHA_decode_IO_failure_allowance_seconds=600,
                assumed_thread_speedup=1.)
        quote['CPU_scoring']['estimated_wall_hours']=sum(quote['CPU_scoring'][s]['engineering_forecast_wall_hours'] for s in ('stage_A','stage_B'))
        quote['CPU_scoring']['uncertainty']='One synthetic full-resolution frame per host, with 50% frame-cost margin and 600s fixed overhead per phase. Real all93 decode/hash/I/O throughput remains unmeasured; hard CPU bounds remain 2h+4h, never auto-extended.'
    write('WHOLE_QUOTE.json', quote)


if __name__ == '__main__':
    main()
