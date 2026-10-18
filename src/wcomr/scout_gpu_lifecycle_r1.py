"""New scout lifecycle, with an explicitly separate accepted execution stage.

The original real-entry stage is read only. Its runner, registration, CPU proof
and execution revision stay together; the supervisor/post code has its own
registered revision and CPU proof. No old scope pass is transferred to a scout.
"""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from .gpu_budget_pool_v2 import BudgetPool
from .scout_sampling_r1 import matrix, plans, TIMING

DEPENDENCIES = {k: 'manifests/scout_'+k.lower()+'_lifecycle_dependency_r1_20261018.json' for k in ('CAL12', 'BANK24')}

def dependency_ref(stage):
    return DEPENDENCIES[read(Path(stage)/'registration.json')['scout_kind']]
CPU_BUNDLE = 'scout-lifecycle-CPU-bundle.json'
CPU_PROOF = 'scout-lifecycle-CPU-proof.json'
CPU_LAUNCH = 'scout-lifecycle-CPU-launch.json'
CPU_ACCEPTED = 'SCOUT_GPU_LIFECYCLE_CPU_ACCEPTED_WITH_UNCHANGED_REAL_ENTRY'
PATTERNS = ('test_scout_gpu_lifecycle_r1.py',)
ENTRY_SOURCE = 'c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9'
RUNS = dict(CAL12='wc-scout-cal4-g01-var26-full12-r1',
            BANK24='wc-scout-dev6-paired-native-full24-r1')
VECTORS = ('p20_c', 'p20_u', 'p21_c', 'p21_u', 'v_actual21', 'v_returned21')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    p = Path(path); raw = p.read_bytes()
    return json.loads(gzip.decompress(raw) if p.suffix == '.gz' else raw)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def counts(kind):
    require(kind in RUNS, 'Explicit CAL12 or BANK24 required')
    n, methods, formal, warm = (4, 2, 8, 4) if kind == 'CAL12' else (6, 3, 18, 6)
    return dict(requests=n, methods=methods, formal_paths=formal, full_warmup_paths=warm,
                total_paths=formal+warm, loads=1, new_teacher_pairs=0,
                new_Native_formal=0 if kind == 'CAL12' else 6,
                ordinary_pairs=(formal+warm)*36, ordinary_CFG_calls=(formal+warm)*72)


def alive(expected, observed):
    return bool(expected and observed and expected['pid'] == observed['pid']
                and expected['start_ticks'] == observed['start_ticks']
                and observed['state'] not in (None, 'Z', 'X'))


def audit_registered_rows(c, rows):
    """Exact denominator, including refusals, failures and not-reached slots."""
    kind = c['kind']; require(c['scope_counts'] == counts(kind), 'Whole scout count changed')
    expected = matrix(kind, [r['name'] for r in c['requests']])
    require(len(rows) == len(expected), 'All registered positions must remain')
    require(len({r['id'] for r in rows}) == len(rows), 'Duplicate scout position')
    for row, plan in zip(rows, expected):
        require(all(row.get(k) == v for k, v in plan.items()), 'Foreign position or observation rule')
        if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED'):
            continue
        native = row['method'] == 'NATIVE35'
        life = row['request_memory_lifecycle']
        require(row['solver_steps'] == row['guided_pairs'] == 36, 'Incomplete actual solver')
        require(life['owners_alive_after'] == 0 and life['observed_owners'] == (0 if native else 1), 'Owner leak')
        require(row['audit'] == (plan['section'] == 'WARMUP') and
                row['in_timing_guided_copies'] == (36 if row['audit'] else 0), 'Wrong guided capture boundary')
        require(row['in_timing_hashes'] == row['research_checkpoints'] == 0 and
                row['write_deferred_after_main_timer'], 'Unregistered audit work')
        require(row['timing_claim'] == TIMING and math.isfinite(row['core_seconds']) and row['core_seconds'] > 0,
                'Actual diagnostic time required')
        require(row['scout_observation']['observer_enabled'] == plan['observer'], 'Observer scope changed')
        if native:
            require(row['actions'] is None and not row.get('source_history') and not plan['observer'], 'Native owner/actions')
            continue
        mask = list(plans(kind)[row['method']]); hist = row['source_history']
        require(row['semantic_plan'] == mask and row['actions'] == ['DD' if a == 'D' else 'CC' for a in mask],
                'Changed actual compute mask')
        require(len(hist) == 36 and [h['action'] for h in hist] == row['actions'], 'Incomplete source history')
        for a, h in zip(mask, hist):
            r = h['A_readout']
            require(not h['teacher_calls'] and not r['teacher_calls'] and not r['extra_deep_blocks'] and
                    not h['P_updates_true_D_or_zero_risk_RA_anchor'], 'Teacher or false source')
            require(r['readout_action'] == a, 'Actual readout differs')
            if a != 'D': require(h['true_D_before'] == h['true_D_after'], 'Approximation wrote a dense anchor')
            if a == 'A': require(r['shared_alpha'] == 1, 'Changed A intensity')
            if a == 'C': require(not r['shared_alpha'] and not r['extra_heads'], 'C computed an extra proposal')
        if plan['observer']:
            o = row['scout_observation']
            require(o['probe_copies'] == 4 and o['velocity_copies'] == 2 and not o['teacher_calls'] and
                    o['copies_and_hashes_in_request_clock'] and not o['online_gate_executed'], 'Observation not paid or changed')


def endpoint_key(row):
    return (row['final_latent_sha256'], row['actions'], row.get('A_history'), row['decoded_video']['RGB_sha256'])


def repeat_and_prefix(c, rows):
    lookup = {r['id']: r for r in rows}; controls = []
    for method in plans(c['kind']):
        a, b = (lookup['warm_'+str(n)+'_'+method] for n in (1, 2))
        if not all(r.get('endpoint_audit') == 'PASS' for r in (a, b)):
            controls.append(dict(method=method, status='UNAVAILABLE_RETAINED')); continue
        require(endpoint_key(a) == endpoint_key(b), 'Observer changed final/actions/A history/RGB')
        require(a['guided_step_sha256'] == b['guided_step_sha256'] and len(a['guided_step_sha256']) == 36,
                'Observer changed a real guided update')
        formal = next(r for r in rows if r['section'] == 'TIMED' and r['scene'] == a['scene'] and r['method'] == method)
        if formal.get('endpoint_audit') == 'PASS': require(endpoint_key(a) == endpoint_key(formal), 'Warm/formal endpoint changed')
        controls.append(dict(method=method, status='PASS_ALL36_AND_ENDPOINT_RGB', formal_status=formal.get('endpoint_audit')))
    methods = ('G01_LATE_A', 'VARIATION26_C') if c['kind'] == 'CAL12' else ('D21', 'A21')
    prefix = []
    for n in (1, 2):
        a, b = (lookup['warm_'+str(n)+'_'+m] for m in methods)
        if not all(r.get('guided_step_sha256') for r in (a, b)):
            prefix.append(dict(round=n, status='UNAVAILABLE_RETAINED')); continue
        require(a['guided_step_sha256'][:20] == b['guided_step_sha256'][:20], 'Different pre-action trajectory')
        prefix.append(dict(round=n, status='PASS_FIRST20_GUIDED', compared_outputs=20))
    state = []
    for scene in [r['name'] for r in c['requests']]:
        a, b = (next(r for r in rows if r['section'] == 'TIMED' and r['scene'] == scene and r['method'] == m) for m in methods)
        if not all(r.get('vector_audit') == 'PASS' for r in (a, b)):
            state.append(dict(scene=scene, status='UNAVAILABLE_RETAINED')); continue
        require(a['scout_observation']['pre_action_input_sha256'] == b['scout_observation']['pre_action_input_sha256'],
                'Different step21 input')
        require(all(a['scout_vector_metadata'][k] == b['scout_vector_metadata'][k] for k in VECTORS[:4]),
                'Different actual p20/p21 probes')
        require(a['scout_observation']['actual_timestep'] == b['scout_observation']['actual_timestep'], 'Different sigma')
        state.append(dict(scene=scene, status='PASS_SAME_INPUT_AND_FOUR_PROBES'))
    return dict(warm_repeat_controls=controls, common_prefix_controls=prefix, same_state_controls=state)


def bound_dependency(project, stage, *, verify_physical=True):
    """Recheck the unchanged accepted entry; do not execute it again on CPU."""
    stage = Path(stage); meta = read(stage/dependency_ref(stage)); kind = meta['kind']
    require(kind in RUNS, 'Unknown scout dependency')
    reg = read(stage/'registration.json'); entry_stage = Path(meta['entry_stage'])
    require(entry_stage.parent == Path(project).resolve()/'.sync' and entry_stage != stage, 'Distinct immutable entry stage required')
    require(sha(entry_stage/'registration.json') == meta['entry_registration_sha256'], 'Original entry registration changed')
    original = read(entry_stage/'registration.json')
    require(meta['entry_source_revision'] == original['source_revision'] == ENTRY_SOURCE and
            reg['CPU_scope'] == 'SCOUT_GPU_LIFECYCLE_OVER_ACCEPTED_ENTRY', 'Wrong source/scope')
    require(reg['scout_kind'] == kind and reg['runtime_source_sha256'] == original['runtime_source_sha256'], 'Runtime or kind changed')
    require(all(reg['payload_sha256'].get(n) == h for n, h in original['payload_sha256'].items()), 'Execution dependency changed')
    for ref in meta['evidence'].values(): require(sha(stage/ref['ref']) == ref['sha256'], 'Entry evidence changed')
    cap = read(stage/meta['evidence']['capture']['ref']); saved = read(stage/meta['evidence']['accepted']['ref'])
    require(saved['capture_sha256'] == meta['evidence']['capture']['sha256'], 'Original capture binding differs')
    require(cap['launch'] == read(stage/meta['evidence']['launch']['ref'])['launch'], 'Original CPU identity differs')
    require(cap['registration_sha256'] == meta['entry_registration_sha256'] and cap['registration'] == original,
            'Original entry source proof differs')
    spec = importlib.util.spec_from_file_location('scout_accepted_real_entry', stage/'scripts/capture_wc_scout_production_entry_cpu_r1.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    accepted = module.accept(cap)
    require(accepted.get('production_entry_CPU_accepted') and all(saved.get(k) == v for k, v in accepted.items()), 'Real entry CPU not independently accepted')
    if verify_physical:
        require(all(sha(stage/n) == h for n, h in reg['payload_sha256'].items()), 'Lifecycle source changed')
        require(all(sha(entry_stage/n) == h for n, h in original['payload_sha256'].items()), 'Execution source changed')
        require(all(sha(Path(project)/'runtime'/n) == h for n, h in reg['runtime_source_sha256'].items()), 'Runtime changed')
        require(sha(entry_stage/'scout-entry-production-CPU-result.json') == accepted['production_entry_CPU_sha256'], 'Real entry CPU proof changed')
    config = cap['files']['config']['data']
    require(config['scope_counts'] == counts(kind) and config['run_id'] == RUNS[kind], 'Full scout scope required')
    return meta, config, reg, cap, accepted


def accept_cpu(v):
    L = v['launch']; require(v['mode'] == 'terminal' and v['observed_unix'] >= L['final_not_before_unix'], 'Not final CPU capture')
    require(not alive(L['identity'], v['process']), 'Original lifecycle CPU still running')
    require(v['registration_sha256'] == L['registration_sha256'] and v['registration']['source_revision'] == L['source_revision'], 'CPU registration differs')
    reg = v['registration']
    require(v['payload_actual_sha256'] == reg['payload_sha256'] and v['runtime_actual_sha256'] == reg['runtime_source_sha256'], 'Full source/runtime not accepted')
    missing = [n for n in ('bundle', 'proof', 'dependency', 'config') if not v['files'].get(n, {}).get('data')]
    if missing:
        return dict(status='SCOUT_LIFECYCLE_CPU_TERMINAL_MISSING_RETAINED', lifecycle_CPU_accepted=False,
                    GPU_dispatch_ready=False, missing=missing, GPU_submissions=0)
    b, proof = v['files']['bundle']['data'], v['files']['proof']['data']
    if b.get('exit_code') != 0:
        return dict(status='SCOUT_LIFECYCLE_CPU_FAILURE_RETAINED', lifecycle_CPU_accepted=False,
                    GPU_dispatch_ready=False, GPU_submissions=0)
    require(b['exit_code'] == 0 and b['status'] == 'SCOUT_LIFECYCLE_CPU_PASS_REUSING_REAL_ENTRY', 'Lifecycle CPU failed')
    command = [L['command'][0], '-m', 'unittest', 'discover', '-s', L['stage']+'/tests', '-p', PATTERNS[0], '-v']
    check = [L['command'][0], L['stage']+'/scripts/check_wc_scout_gpu_lifecycle_r1.py', '--project', L['project'], '--stage', L['stage']]
    require([x['command'] for x in b['commands']] == [command, check] and all(x['exit_code'] == 0 for x in b['commands']), 'Actual lifecycle commands required')
    require(b['proof_sha256'] == v['files']['proof']['sha256'] and b['source_revision'] == L['source_revision'], 'Different CPU proof/source')
    require(proof['registration_sha256'] == L['registration_sha256'] and proof['dependency_sha256'] == reg['payload_sha256'][DEPENDENCIES[L['kind']]], 'Different execution dependency')
    require(proof['kind'] == L['kind'] and proof['scope_counts'] == counts(L['kind']) and proof['entry_CPU_accepted'], 'Wrong scout scope')
    require(proof['entry_source_revision'] == ENTRY_SOURCE and proof['full_registered_request_matrix_checked'], 'Missing real entry reuse')
    require(proof['GPU_submissions'] == b['GPU_submissions'] == 0 and not proof['ledger_written'] and not b['ledger_written'], 'CPU touched GPU/ledger')
    return dict(status=CPU_ACCEPTED, GPU_dispatch_ready=True, lifecycle_CPU_accepted=True,
                kind=L['kind'], source_revision=L['source_revision'], registration_sha256=L['registration_sha256'],
                dependency_sha256=proof['dependency_sha256'], proof_sha256=v['files']['proof']['sha256'],
                scope_counts=counts(L['kind']), original_CPU_identity=L['identity'],
                entry_source_revision=ENTRY_SOURCE, entry_registration_sha256=proof['entry_registration_sha256'],
                entry_CPU_sha256=proof['entry_CPU_sha256'], CPU_commands=2, CPU_wall_seconds=b['CPU_wall_seconds'],
                unchanged_numerical_and_real_entry_reused=True, actual_video_or_quality_result=False,
                GPU_submissions=0, ledger_written=False)


def validate_authority(auth, config, regsha, accepted_sha, proofsha, dependencysha):
    kind = config['kind']
    require(auth['direct_user_authorization'] is True and auth['user_reply_quote'] and
            auth['autonomy_exclusive_upper_GPUh'] == 12, 'Standing direct human authority required')
    require(auth['kind'] == kind and auth['run_id'] == RUNS[kind] and auth['scope_counts'] == counts(kind), 'Wrong whole card')
    require(auth['registration_sha256'] == regsha and auth['independent_CPU_acceptance_sha256'] == accepted_sha and
            auth['production_CPU_sha256'] == proofsha and auth['dependency_sha256'] == dependencysha, 'Authority proof changed')
    require(auth['bound_config_fingerprint'] == hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(), 'Authority config changed')
    require(auth['forecast_GPUh'] == config['forecast_complete_GPUh'] and auth['billed_limit_GPUh'] == config['billed_limit_GPUh'] and
            0 < auth['forecast_GPUh'] <= auth['billed_limit_GPUh'] < 12, 'Strict whole under12 quote required')
    require(auth['cumulative_cap_GPUh'] == 226 and auth['budget_origin_used_GPUh'] == 79.99637737158223, 'Cumulative budget changed')
    require(auth['upstream_originals_verified'] and len(auth['upstream_capture_sha256']) == 64 and auth['launch_id'] and
            auth['gpu_uuid'].startswith('GPU-'), 'Frozen upstream and fresh launch/UUID required')


def finance(v, launch):
    bill = v['billing']; pool = v['pool']; job = pool['jobs'][launch['run_id']]
    require(all(bill[k] == launch[k] for k in ('launch_id', 'run_id', 'source_revision', 'gpu_uuid', 'scope_counts')), 'Bill identity differs')
    require(math.isfinite(bill['wall_seconds']) and bill['wall_seconds'] > 0 and
            math.isclose(bill['wall_seconds']/3600, bill['actual_GPUh'], rel_tol=1e-12), 'Whole wall price differs')
    require(job['status'] == 'SETTLED' and job['actual_GPUh'] == bill['actual_GPUh'] and job['billing_sha256'] == v['billing_sha256'], 'Settlement differs')
    require(v['supervisor']['billing_sha256'] == v['billing_sha256'], 'Supervisor bill differs')
    require(all(job[k] == launch[k] for k in ('launch_id', 'gpu_uuid', 'source_revision', 'production_CPU_sha256', 'config_sha256', 'scope_counts')), 'Charged wrong scope')
    require(all(math.isclose(pool[k], n, abs_tol=1e-12, rel_tol=1e-12) for k, n in BudgetPool.accounting(pool).items()), 'Additive pool differs')
    own = {launch['supervisor_pid'], v['supervisor'].get('child_pid')}
    require(not v.get('GPU_telemetry_error') and v['own_GPU'].split(',')[0].strip() == launch['gpu_uuid'], 'Original UUID telemetry missing')
    require(not any(s.split(',')[0].strip() == launch['gpu_uuid'] and int(s.split(',')[1]) in own
                    for s in v.get('compute_apps', '').splitlines() if s.strip()), 'Own GPU process still running')
    later = any(alive(dict(pid=j['supervisor_pid'], start_ticks=j['supervisor_start_ticks']),
                      v.get('other_reservation_identities', {}).get(k)) for k, j in pool['jobs'].items()
                if k != launch['run_id'] and j['status'] == 'RESERVED_OR_RUNNING' and j['gpu_uuid'] == launch['gpu_uuid'])
    require(v['own_UUID_lock_free'] or later, 'Original lock not released')
    require(pool['cap_gpu_hours'] == 226 and pool['origin_used_gpu_hours'] == 79.99637737158223, 'Budget history changed')
    return dict(finance_accepted=True, actual_GPUh=bill['actual_GPUh'],
                billed_limit_respected=bill['actual_GPUh'] <= bill['billed_limit_GPUh'], own_UUID_released=True)


def accept_terminal(v, launch):
    """Recompute frame means, state/step identity and additive cost offline."""
    require(v['launch'] == launch and v['mode'] == 'terminal', 'Original launch and terminal capture required')
    require(v['observed_unix'] >= launch['next_check_not_before_unix'], 'Before original ETA')
    if any(v['original_live_handles'].values()):
        return dict(status='SCOUT_ORIGINAL_STILL_RUNNING_REESTIMATE_ONCE', full_protocol_accepted=False)
    require(v['registration_sha256'] == launch['registration_sha256'] and
            v['registration']['source_revision'] == launch['source_revision'], 'Original lifecycle registration differs')
    require(v['payload_actual_sha256'] == v['registration']['payload_sha256'] and
            v['runtime_actual_sha256'] == v['registration']['runtime_source_sha256'], 'Missing immutable source/runtime')
    c = v['config']; kind = c['kind']; expected = matrix(kind, [r['name'] for r in c['requests']])
    require(launch['scope_counts'] == counts(kind) and launch['run_id'] == RUNS[kind], 'Foreign card')
    require(v['entry_payload_actual_sha256'] == v['entry_registration']['payload_sha256'] and
            v['entry_registration_sha256'] == launch['entry_registration_sha256'], 'Original execution source differs')
    require(v['runner']['source_revision'] == ENTRY_SOURCE and
            v['runner']['config_sha256'] == v['entry_config_file_sha256'], 'Original runner binding differs')
    fin = finance(v, launch); final = v.get('final'); errors = []
    if final is None or v.get('post_exit', {}).get('exit_code') != 0:
        return dict(status='SCOUT_POST_FAILED_OR_MISSING_RETAINED', full_protocol_accepted=False, finance=fin,
                    registered_paths=len(expected), errors=['Original CPU post did not complete'])
    rows = final['rows']; audit_registered_rows(c, rows)
    require(v['post_exit']['final_result_sha256'] == v['final_sha256'], 'Original CPU final bytes differ')
    actual = {r['id']: r for r in v['runner']['runs']}
    require(len(actual) == len(v['runner']['runs']) and set(actual) <= {r['id'] for r in expected}, 'Foreign runner rows')
    for row in rows:
        original = actual.get(row['id'])
        if original:
            require(all(row[k] == value for k, value in original.items()), 'CPU post altered an original runner value')
        else: require(row['status'] == 'NOT_REACHED_RETAINED', 'A missing path was fabricated')
        for name in ('final_artifact', 'warm_guided_artifact', 'scout_vectors_artifact', 'video_artifact'):
            if name not in row: continue
            item = row[name]; observed = v['original_artifacts'].get(item['path'])
            require(observed == dict(sha256=item['sha256'], bytes=item['bytes']), 'Original physical artifact differs')
        if row['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
            if row.get('raw_model_audit') != 'PASS': errors.append(row['id']+':RAW_AUDIT_FAILURE')
            if row.get('observer') and row.get('vector_audit') != 'PASS': errors.append(row['id']+':VECTOR_AUDIT_FAILURE')
        if row['status'] == 'COMPLETE' and row.get('endpoint_audit') != 'PASS': errors.append(row['id']+':VIDEO_AUDIT_FAILURE')
        if row.get('endpoint_audit') == 'PASS':
            d = row['decoded_video']; require(d['frames'] == 93 and d['probe']['HWC'] == [432, 768, 3], 'Full93 RGB required')
    try:
        controls = repeat_and_prefix(c, rows)
        require(all(final.get(k) == val for k, val in controls.items()), 'Independent repeat/state controls differ')
    except (ValueError, KeyError) as error:
        errors.append('CONTROL:'+str(error)); controls = {}
    if final.get('control_failure'): errors.append('POST_CONTROL_FAILURE')
    references = {r['scene']: r for r in final.get('Native_reference_bindings', [])}
    losses = []; scored = {}
    for row in rows:
        if row['section'] != 'TIMED' or row['method'] == 'NATIVE35' or row.get('endpoint_audit') != 'PASS': continue
        score = row.get('LPIPS'); ref = references.get(row['scene'])
        if score is None:
            losses.append(dict(id=row['id'], scene=row['scene'], method=row['method'], status='REFERENCE_OR_SCORE_UNAVAILABLE_RETAINED'))
            if ref is not None: errors.append(row['id']+':APPLICABLE_LPIPS_NOT_SCORED')
            continue
        require(ref is not None and score['reference_sha256'] == ref['video_artifact']['sha256'] and
                score['candidate_sha256'] == row['video_artifact']['sha256'], 'LPIPS pairing identity differs')
        vals = score['frame_distances']
        require(score['frames'] == len(vals) == len(score['pts']) == 93 and
                all(math.isfinite(x) and x >= 0 for x in vals), 'All93 actual distances required')
        require(math.isclose(sum(vals)/93, score['mean_LPIPS'], rel_tol=1e-12, abs_tol=1e-12), 'LPIPS mean differs')
        scored[(row['scene'], row['method'])] = sum(vals)/93
        losses.append(dict(id=row['id'], scene=row['scene'], method=row['method'], status='SCORED',
                           LPIPS=sum(vals)/93, seconds=row['core_seconds']))
    memory = v['runner'].get('request_memory_records', [])
    require(final['request_memory_records'] == memory and
            [r['id'] for r in memory] == [r['id'] for r in v['runner']['runs'] if 'request_memory_lifecycle' in r] and
            all(r['owners_alive_after'] == 0 for r in memory), 'Every completed request must release its owner')
    outcomes = {s: sum(r['status'] == s for r in rows) for s in sorted({r['status'] for r in rows})}
    full_rows = all(r['status'] in ('COMPLETE', 'TEXT_REJECTED', 'VIDEO_REJECTED') for r in rows)
    if v['supervisor']['child_exit_code'] != 0 or not full_rows: errors.append('GPU_TECHNICAL_FAILURE_OR_NOT_REACHED')
    if kind == 'CAL12':
        controls_old = final.get('old_prefix_controls', [])
        if len(controls_old) != 2 or any(not r['status'].startswith('PASS') for r in controls_old): errors.append('OLD_PREFIX_INCOMPLETE')
        for check in controls_old:
            current = next(r for r in rows if r['id'] == 'warm_1_'+check['method'])
            n = check['compared_outputs']
            require(current.get('guided_step_sha256', [])[:n] == check['old_guided_step_sha256'][:n], 'Old common prefix differs')
        require(len(final.get('old_CAL_bindings', [])) == 12, 'All original N12 formal controls retained')
    protocol = not errors and fin['finance_accepted'] and fin['billed_limit_respected']
    all_videos = all(r['status'] == 'COMPLETE' and r.get('endpoint_audit') == 'PASS' for r in rows)
    target_scores = 8 if kind == 'CAL12' else 12
    return dict(status='SCOUT_COMPLETE_REGISTERED_PROTOCOL_ACCEPTED' if protocol else 'SCOUT_FULL_SCOPE_ISSUES_RETAINED',
                kind=kind, full_protocol_accepted=protocol, all_registered_videos_accepted=all_videos,
                all_applicable_fidelity_scored=len(scored) == target_scores,
                registered_paths=len(expected), formal_denominator=counts(kind)['formal_paths'],
                scored_nonNative_formal=len(scored), actual_GPUh=fin['actual_GPUh'], finance=fin,
                errors=errors, outcomes=outcomes, controls=controls, per_scene_results=losses,
                exploratory_only=True, clean_latency_claim=False, independent_final_test_claim=False,
                GPU_submissions=0, ledger_written=False)


def freeze_cal_gate(v, accepted):
    require(accepted['kind'] == 'CAL12' and accepted['full_protocol_accepted'], 'Accepted entire CAL12 required')
    rows = [r for r in v['final']['rows'] if r['section'] == 'TIMED' and r['method'] == 'G01_LATE_A']
    require(len(rows) == 4 and all(r.get('vector_audit') == 'PASS' for r in rows), 'Four CAL observed states required')
    values = [r['visible_probe_delta']['guided_probe_delta_RMS'] for r in rows]
    require(all(math.isfinite(x) and x >= 0 for x in values), 'Finite actual probe changes required')
    mu = sum(values)/4; z = [x/(mu+1e-12) for x in values]; order = sorted(z)
    return dict(status='FOUR_CAL_GATE_FROZEN_BEFORE_DEV_BANK', mu_RMS=mu, epsilon=1e-12,
                threshold=(order[1]+order[2])/2, direction='LARGER_Z_KEEP_D', equality='Z_GE_THRESHOLD_D',
                definition='z=guided_probe_delta_RMS/(four_CAL_mean_RMS+1e-12)',
                CAL_rows=[dict(scene=r['scene'], delta_RMS=x, z=value) for r, x, value in zip(rows, values, z)],
                DEV_used_for_fit=False, online_gate_executed=False)


def verify_upstream(kind, capture, accepted, gate=None):
    if kind == 'CAL12':
        from .drop1_window24_acceptance_r1 import accept
        calculated = accept(capture, capture['launch'])
        require(calculated['full_protocol_accepted'] and all(accepted.get(k) == val for k, val in calculated.items()),
                'Original complete Window24 must finish before CAL12')
    else:
        calculated = accept_terminal(capture, capture['launch'])
        require(calculated['kind'] == 'CAL12' and calculated['full_protocol_accepted'] and
                all(accepted.get(k) == val for k, val in calculated.items()), 'CAL12 must finish before BANK24')
        require(gate == freeze_cal_gate(capture, calculated), 'Gate must be frozen from four CAL before DEV')
    return True
