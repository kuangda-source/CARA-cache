"""Identity-only selection and complete cost calculation; never reserves or launches."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from wcomr.frozen_input_exposure_r1 import Identities
from wcomr.cara_fast_spec_r1 import digest
from audit_cara_new_pool_r1 import unpack
from cara_f19_speed190_transport_r1 import rpc

HERE = Path(__file__).resolve().parent
SALT = 'CARA_SENSITIVITY_20261104_SEED0'
RUN = 'cara-native-sensitivity8-confirm4-r1-20261104'


def read(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select_inputs():
    catalog = read('reports/dataset_source_group_audit_20260930.json')
    prior = read('reports/cara_new_input_pool48_exposure_r1_20261025.json')
    pool = read('plans/cara_policy_generator_20261020/NEW_INPUT_POOL48_R1_20261025.json')
    records = catalog['records']
    index = Identities(records)
    excluded = set(prior['excluded_names']) | set(catalog['engineering_excluded_groups'])
    # All 48 are excluded: DEV16 has been used; final16 and backup16 stay protected.
    excluded.update(n for r in pool['members'] for n in r['group_members'])
    known = {r['ref']: r['sha256'] for r in prior['local_documents']}
    metadata = {
        'reports/dataset_source_group_audit_20260930.json',
        'reports/wc_paper_N07_all1044_original_input_bytes_CPU_inventory_20261016.json',
    }
    delta = []
    for folder in ('reports', 'plans', 'manifests', 'cards'):
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file() or not str(path).endswith(('.json', '.json.gz')) or '.private.' in path.name:
                continue
            ref = str(path.relative_to(ROOT))
            if ref in metadata:
                continue
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if known.get(ref) == digest:
                continue
            data = json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
            hits, _ = index.document(unpack(data))
            excluded.update(h['name'] for h in hits)
            delta.append(dict(path=ref, sha256=digest))
    module = (ROOT/'src/wcomr/frozen_input_exposure_r1.py').read_text()
    operator = '''
import json,pathlib,time
p=packet['arguments'];ns={};exec(compile(p['module'],'sensitivity-identities','exec'),ns)
rows=[ns['collect_outputs'](root,p['records']) for root in p['roots']]
print(json.dumps(dict(observed_unix=time.time(),roots=rows)))
'''
    remote = rpc(operator, dict(module=module, records=records, roots=[
        '/data20t/gaokuangda/worldcache_workspace', '/home/gaokuangda/data/gkd/worldcache_omr']),
        route='ipv4', timeout=180)
    if 'roots' not in remote:
        raise ValueError('Identity inventory unavailable: '+str(remote))
    for result in remote['roots']:
        if result['read_errors']:
            raise ValueError('Incomplete identity inventory: '+str(result['read_errors'][:3]))
        excluded.update(result['identity_hits'])
    for record in records:
        if excluded.intersection(record['group_members']):
            excluded.update(record['group_members'])
    eligible = [r for r in records if not excluded.intersection(r['group_members'])]
    categories = ['av', 'human', 'misc', 'physics']
    selected = [min((r for r in eligible if r['category'] == category),
                    key=lambda r: hashlib.sha256((SALT+'|'+r['name']).encode()).hexdigest())
                for category in categories]
    sources = []
    for record in selected:
        path = ROOT/'vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only'/(record['name']+'.json')
        sources.append(dict(record, source_ref=str(path.relative_to(ROOT)), source_sha256=sha(path)))
    return sources, dict(rule='one per av/human/misc/physics, minimum SHA256(salt|name), exclude whole source groups',
        selection_salt=SALT, selection_seed=0, generation_seed=0,
        catalog_ref='reports/dataset_source_group_audit_20260930.json',
        prior_audit_ref='reports/cara_new_input_pool48_exposure_r1_20261025.json',
        protected_pool_ref='plans/cara_policy_generator_20261020/NEW_INPUT_POOL48_R1_20261025.json',
        all48_excluded=True, eligible_groups=len(eligible), excluded_names=sorted(excluded),
        local_delta_files=delta, remote_observed_unix=remote['observed_unix'],
        remote_inventory=[dict(documents=len(r['documents']), identity_groups=len(r['identity_hits']),
                               read_errors=r['read_errors']) for r in remote['roots']],
        coverage='Prior four-card inventory + current local registered JSON/gzip + two-card current and historical outputs; unknown external runs are outside scope',
        dispatch_incremental_identity_check_required=True, outcome_values_exported=False)


def build(sources, selection):
    selection = dict(selection)
    delta = selection.pop('local_delta_files')
    selection.update(local_delta_files_count=len(delta),local_delta_inventory_sha256=digest(delta),
        full_local_inventory_path='/tmp/cara_sens_selection.json')
    base_ref = 'plans/cara_next_stage_20261103/f19_speed190_cal/CAL35_MANIFEST_R1.json'
    base = read(base_ref)
    inputs = list(base['inputs'])
    template = {k: v for k, v in inputs[0].items() if k not in ('name', 'prompt', 'partition')}
    for source in sources:
        request = read(source['source_ref'])
        if isinstance(request, list):
            if len(request) != 1:
                raise ValueError('Expected one benchmark source request')
            request = request[0]
        prompt = request['prompt']
        if hashlib.sha256(prompt.encode()).hexdigest() != source['prompt_sha256']:
            raise ValueError('Source prompt changed')
        inputs.append(dict(template, name=source['name'], prompt=prompt, partition='NEW_CONFIRM'))
    analysis = read('reports/cara_f19_speed190_complete_r1_20261103/complete_analysis.json')
    prices = {r['role']: r['T_request'] for r in analysis['rows']}
    native = next(r for r in analysis['rows'] if r['role']=='NATIVE35')
    # Charge every remaining update at the measured full-D pair price, including C.
    d = analysis['diagnostic_components_by_action']['D']['pair_D']
    pair_seconds = d['inclusive_CUDA_ms']/d['calls']/1000
    decode_seconds = 6.3783
    overhead = native['T_request']-native['T_DD']+decode_seconds
    suffix_seconds = sum((37-t)*pair_seconds+overhead for t in range(8,35,2))
    matrix = []
    def add(section, member, role, target=None):
        matrix.append(dict(id=f'SENS_{len(matrix)+1:03d}', section=section, member=member, role=role,
                           target_update=target, seed=0, audit=False, eligible_clean_time=section == 'c'))
    for role in ('NATIVE35', 'F19_A1'):
        add('warm', inputs[0]['name'], role)
    for row in inputs:
        add('a', row['name'], 'NATIVE_RECORD')
    add('control', inputs[0]['name'], 'NATIVE35')
    for target in (8,34):
        add('control', inputs[0]['name'], 'RESUME_D', target)
    for target in range(8, 35, 2):
        for row in inputs:
            add('b', row['name'], 'SINGLE_C', target)
    for target in (8,34):
        add('control', inputs[0]['name'], 'FULL_SINGLE_C', target)
    for i, row in enumerate(inputs[4:]):
        roles = ('NATIVE35', 'F17_A2_LIGHT_C', 'F19_A1', 'WC_T006')
        for role in roles[i:]+roles[:i]:
            add('c', row['name'], role)
    # Original D-pair CUDA profile plus full measured Native non-loop overhead per suffix.
    seconds = {
        'a': 8*prices['NATIVE35'],
        'b_old': 4*suffix_seconds,
        'b_new': 4*suffix_seconds,
        'c': 4*sum(prices[r] for r in ('NATIVE35','F17_A2_LIGHT_C','F19_A1','WC_T006')),
        'warm_and_controls': 6*prices['NATIVE35']+prices['F19_A1'],
    }
    raw = sum(seconds.values())
    quote = dict(basis='CAL35 measured D-pair CUDA time * remaining updates + complete Native non-loop overhead; C charged as D; CPU scoring after release',
        pair_D_seconds=pair_seconds, suffix_overhead_seconds=overhead,
        measured_request_seconds=prices, components_GPUh={k:v/3600 for k,v in seconds.items()},
        variation_10pct_GPUh=raw*.10/3600, model_load_cleanup_GPUh=600/3600,
        checkpoint_IO_allowance_GPUh=1200/3600, release_margin_GPUh=600/3600,
        forecast_GPUh=(raw*1.1+2400)/3600, hard_GPUh=9.5)
    card = dict(schema='CARA_SENSITIVITY8_CONFIRM4_R1', run_id=RUN,
        stage_name='cara-native-sensitivity8-confirm4-r1-20261104',
        phase='PHASE1_PREPARATION_ONLY', GPU_dispatch_ready=False,
        authority=dict(user_quote='批准新旧输入都做，约 8.9 GPUh，硬限 9.5 GPUh',
            hard_GPUh=9.5, Phase1_ledger_reservation_allowed=False, Phase1_GPU_allowed=False,
            cap_increase_allowed=False, automatic_monitoring_allowed=False),
        CAL35_manifest_ref=base_ref, CAL35_manifest_sha256=sha(ROOT/base_ref),
        inputs=inputs, new_sources=sources, selection=selection,
        FIT=base['FIT'], old_CHECK=base['CHECK'], new_confirm=[r['name'] for r in inputs[4:]],
        profile=base['profile'], schedule=base['schedule'], settings=base['settings'],
        roles={r:base['roles'][r] for r in ('NATIVE35','F17_A2_LIGHT_C','F19_A1','WC_T006')},
        sensitivity_steps=list(range(8,35,2)), C_semantics='Original full C, alpha0, flow/settings identical CAL35; only step t becomes C, all others D',
        matrix=matrix, counts=dict(a=8,b=112,c=16,warm=2,controls=5,total_requests=len(matrix),
            suffix_paired_calls=8*sum(37-t for t in range(8,35,2)), LPIPS_pairs=124,quality_positions=48),
        quote=quote, storage=dict(private_output_GiB=256, journal_MiB=48,
            RAM_GiB=40, swap_GiB=0, snapshot_logical_GiB=24, snapshot_CPU_GiB=16,
            note='Native latent before every update; full owner/cache/UniPC/RNG/conditions only at 14 sensitivity steps; one image materialized at a time'),
        quality=base['success'], prior_g=dict(reference='plans/scouts_20261018/SCOUT_READONLY_CPU_PLAN.json',
            measured_points=3, semantics='coarse transferred prior; interpolated gains are not 36 empirical sensitivities'),
        precheck=json.loads(Path('/tmp/cara_sens_phase1_precheck.json').read_text()),
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/'+RUN,
        stage_root='/data20t/gaokuangda/worldcache_workspace/.sync/'+RUN,
        ledger_reserved=False, GPU_submissions=0)
    card['scope_sha256']=digest(card)
    return card


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():
        raise ValueError('Preserve the selected manifest')
    sources, selection = select_inputs()
    Path('/tmp/cara_sens_selection.json').write_text(json.dumps(dict(sources=sources,selection=selection)))
    card = build(sources, selection)
    args.output.write_text(json.dumps(card,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(new_inputs=card['new_confirm'],quote=card['quote'],counts=card['counts'])))
