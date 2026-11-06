"""Freeze the C05-skipped continuation scope and the original CAL35 quote.

Reads the accepted confirm10 manifest, collection, inventory and partial scores.
Does not rewrite those files, reserve a ledger, or start a GPU.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from wcomr.policy_generator_r1.interval_grammar import digest

RUN = 'cara-generator-v1-confirm10-continuation-r1-20261106'
ORIGINAL_RUN = 'cara-generator-v1-confirm10-r1-20261105'
ORIGINAL_MANIFEST = 'plans/cara_next_stage_20261105/confirm10/manifest.json'
REPORT = 'reports/cara_generator_v1_confirm10_r1_20261105'
EXECUTION_ALIASES = ['C06', 'C07', 'C08', 'C09', 'C10']
SCIENTIFIC_ALIASES = ['C01', 'C02', 'C03', 'C04', 'C06', 'C07', 'C08', 'C09', 'C10']
EXCLUDED_ALIAS = 'C05'
EXCLUDED_MEMBER = 'av_snowy_1_0'
ARMS = ['NATIVE35', 'F17_A2_LIGHT_C', 'R18C', 'R16C', 'R21C']
OUTPUT_ROOT = ('/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/'
               'cara_cal66_sm86_workspace/outputs/cara-generator-v1-confirm10-r1-20261105')


def read(name):
    return json.loads((ROOT / name).read_text())


def file_sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def request_quote(prices):
    raw = 5 * sum(prices[name] for name in ARMS)
    center = (1.1 * raw + 1200) / 3600
    bounds = [(0.9 * raw + 1200) / 3600, (1.2 * raw + 1200) / 3600]
    hard = math.ceil(bounds[1] * 10) / 10
    return raw, center, bounds, hard


def build():
    original = read(ORIGINAL_MANIFEST)
    inventory = read(REPORT + '/output_inventory.json')
    collection = read(REPORT + '/collection.json')
    scores = read(REPORT + '/partial_scores.json')
    settlement = read(REPORT + '/central_settlement.json')
    if (original['run_id'] != ORIGINAL_RUN or collection['run_id'] != ORIGINAL_RUN
            or collection['status'] != 'FAILED_NO_RETRY'
            or collection['scope_sha256'] != original['scope_sha256']
            or inventory['collection_sha256'] != file_sha(REPORT + '/collection.json')):
        raise ValueError('Original confirm10 manifest and failed collection differ')
    by_id = {row['slot']['id']: row for row in collection['rows']}
    inherited_rows = []
    for item in inventory['completed_outputs']:
        slot = item['slot']
        source = by_id[slot['id']]
        if source['status'] != 'COMPLETE' or source['slot'] != slot:
            raise ValueError('Inventory row is not the complete collection row')
        artifacts = {}
        for key in ('latent_artifact', 'video_artifact'):
            saved = source['result'][key]
            recorded = item['artifacts'][key]
            if saved['sha256'] != recorded['sha256'] or saved['path'] != recorded['path']:
                raise ValueError('Collection artifact hash differs from the inventory')
            if not recorded['path'].startswith(OUTPUT_ROOT + '/'):
                raise ValueError('Completed artifact is outside the original output root')
            artifacts[key] = dict(path=recorded['path'], sha256=recorded['sha256'], bytes=recorded['bytes'])
        if source['result']['T_DD'] != item['T_DD']:
            raise ValueError('Inventory T_DD differs from the collection')
        inherited_rows.append(dict(slot=copy.deepcopy(slot), status='COMPLETE', **artifacts,
            T_DD=item['T_DD'], T_request=item['T_request']))
    inherited_ids = [row['slot']['id'] for row in inherited_rows]
    if inherited_ids != [f'CONFIRM10_{i:03d}' for i in range(1, 22)]:
        raise ValueError('Inherited ids are not CONFIRM10_001-021')
    formal_rows = [row for row in inherited_rows if row['slot']['section'] != 'warm']
    if len(formal_rows) != 20 or sum(row['slot']['section'] == 'warm' for row in inherited_rows) != 1:
        raise ValueError('Inherited split is not 20 formal plus one warm')
    if {row['slot']['member'] for row in inherited_rows} != {
            original['inputs_by_alias'][alias] for alias in ('C01', 'C02', 'C03', 'C04')}:
        raise ValueError('Inherited outputs are not exactly C01-C04')

    excluded_ids = [f'CONFIRM10_{i:03d}' for i in range(22, 27)]
    for request_id in excluded_ids:
        slot = by_id[request_id]['slot']
        if slot['member'] != EXCLUDED_MEMBER or by_id[request_id]['status'] == 'COMPLETE':
            raise ValueError('C05 row is not the skipped incomplete cohort')
    if by_id['CONFIRM10_022']['status'] != 'RUNNING' or by_id['CONFIRM10_022']['slot']['role'] != 'R21C':
        raise ValueError('Original 022 row identity changed')

    matrix = [copy.deepcopy(slot) for slot in original['matrix']
              if slot['id'] in {f'CONFIRM10_{i:03d}' for i in range(27, 52)}]
    if [slot['id'] for slot in matrix] != [f'CONFIRM10_{i:03d}' for i in range(27, 52)]:
        raise ValueError('Continuation matrix is not CONFIRM10_027-051 in original order')
    if any(slot['section'] != 'c' or slot['seed'] != 0 or slot['member'] == EXCLUDED_MEMBER for slot in matrix):
        raise ValueError('Continuation matrix changes section, seed, or includes C05')
    execution_members = [original['inputs_by_alias'][alias] for alias in EXECUTION_ALIASES]
    if sorted(slot['member'] for slot in matrix) != sorted(execution_members * 5):
        raise ValueError('Continuation is not five arms on C06-C10')
    if {slot['role'] for slot in matrix} != set(ARMS):
        raise ValueError('Continuation arms differ from the original five')

    score_rows = []
    inherited_by_id = {row['slot']['id']: row for row in formal_rows}
    for row in scores['rows']:
        source = inherited_by_id[row['slot']['id']]
        video = row['fidelity']['candidate']['sha256']
        reference = row['fidelity']['reference']['sha256']
        if (row['slot'] != source['slot'] or not row['mask_matches']
                or video != source['video_artifact']['sha256'] or row['T_DD'] != source['T_DD']):
            raise ValueError('Partial score does not match the inherited formal output')
        native = next(item for item in formal_rows
            if item['slot']['member'] == row['slot']['member'] and item['slot']['role'] == 'NATIVE35')
        if reference != native['video_artifact']['sha256']:
            raise ValueError('Partial score reference is not the inherited Native video')
        score_rows.append(dict(slot=copy.deepcopy(row['slot']), Alex=row['Alex'], T_DD=row['T_DD'],
            mask_matches=True, video_sha256=video, reference_sha256=reference))
    if len(score_rows) != 16 or scores['status'] != 'PARTIAL_SCORES_COMPLETE':
        raise ValueError('Inherited scores are not the 16 complete C01-C04 pairs')

    job = settlement['central_after']['jobs'][ORIGINAL_RUN]
    if (job['status'] != 'SETTLED' or job['launch_id'] != settlement['launch_id']
            or job['billing_sha256'] != settlement['billing_sha256']):
        raise ValueError('Original settlement is not the unique settled confirm10 job')
    prices = {name: original['quote']['request_prices_seconds'][name] for name in ARMS}
    raw, center, bounds, hard = request_quote(prices)
    anchors = copy.deepcopy(original['quote']['anchors'])
    quote = dict(anchors=anchors, request_prices_seconds=prices, request_sum_seconds=raw,
        formal_request_seconds=raw, warm_request_seconds=0, forecast_GPUh=center, range_GPUh=bounds,
        hard_GPUh=hard, hard_limit_is_suggestion_only=False, expected_wall_hours=center,
        expected_wall_seconds=center * 3600, model_load_seconds=600, release_margin_seconds=600,
        formal_requests=25, warm_requests=0, total_requests=25, warm_roles=[],
        approval_required_for_any_run=True, user_approved=True, GPU_submissions=0, ledger_reservations=0,
        arithmetic_verification=dict(
            formula='T_request=70.734852+6.772260*nD+0.993956*nA+0.637948*nC; light C cost 0; center=(1.1*sum+1200)/3600; range=(0.9*sum+1200)/3600 to (1.2*sum+1200)/3600; hard=ceil(upper*10)/10',
            one_of_each_seconds=sum(prices.values()), request_sum_seconds=raw,
            supplied_request_sum_seconds_not_used=5465.0538,
            supplied_center_GPUh_not_used=1.919259795,
            supplied_range_GPUh_not_used=[1.586821375, 2.1223512],
            supplied_hard_GPUh_not_used=2.1,
            thirty_request_quote_not_used=dict(request_sum_seconds=6570.1074, forecast_GPUh=2.34086615, hard_GPUh=2.6),
            measured_partial_means_not_used=True,
            reason='The supplied 5465.0538/1.919259795/2.1 triple is not the preregistered formula on the unchanged per-request prices. The 30-request quote still includes C05. Partial measured means stay context, not a new anchor.'))
    scientific_members = [original['inputs_by_alias'][alias] for alias in SCIENTIFIC_ALIASES]
    by_name = {row['name']: row for row in original['inputs']}
    provenance = {row['name']: row for row in original['input_provenance']}
    card = dict(schema='CARA_CONFIRM10_CONTINUATION_PREPARE_R1', run_id=RUN,
        phase='PREREGISTERED_CPU_ACCEPTED_AWAITING_FRESH_ADMISSION', GPU_dispatch_ready=True,
        authority=dict(execution_authorized=True, ledger_reservation_authorized=True,
            sync_launch_authorized=True, this_commit_dispatches=False,
            preparation_was_not_gpu_authority=True, fresh_admission_required=True,
            preparation_authority='确认重试 confirm10 续跑准备：跳过 C05，只做预注册和纯 CPU 验收，不上卡、不碰账本。',
            user_quote='confirm10 跳过 C05 整组，不绕过护栏；精确重报后在空闲卡上续跑，硬限按重报，k18 等它完成后再跑。',
            future_dispatch_quote='confirm10 跳过 C05 整组，不绕过护栏；精确重报后在空闲卡上续跑，硬限按重报，k18 等它完成后再跑。',
            authorization_date='2026-11-06', cumulative_budget_policy='RUNNING_TOTAL_NO_CUMULATIVE_CAP',
            hard_GPUh_follows_requote=True),
        reservation_event='CONFIRM10_CONTINUATION_WHOLE2_2_RESERVE',
        gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        gpu_preference=['GPU-cebf7119-cf03-23b9-e192-cd196332b704',
            'GPU-de9a5370-cd87-0f1c-a48e-288888777dd3'],
        inputs=[copy.deepcopy(by_name[name]) for name in execution_members],
        inputs_by_alias={alias: original['inputs_by_alias'][alias] for alias in SCIENTIFIC_ALIASES},
        input_provenance=[copy.deepcopy(provenance[name]) for name in execution_members],
        profile=original['profile'], schedule=original['schedule'], settings=original['settings'],
        roles={name: copy.deepcopy(original['roles'][name]) for name in ARMS},
        matrix=matrix, mask_summary={name: copy.deepcopy(original['mask_summary'][name]) for name in ARMS},
        seed=0, record_noncomplete_on_row=True,
        counts=dict(a=0, b=0, c=25, warm=0, new_native_references=5, total_requests=25,
            scientific_inputs=9, excluded_inputs=1, LPIPS_pairs=36, new_LPIPS_pairs=20,
            inherited_LPIPS_pairs=16, quality_positions=0),
        generated_A_alpha=original['generated_A_alpha'], F17_A2_gains=original['F17_A2_gains'],
        native_references={},
        native_reference_source='Four inherited formal NATIVE35 outputs by hash plus five new same-run NATIVE35 rows. No other historical Native and no C05.',
        fresh_Native_timing_requests=5, inherited_formal_native_references=4,
        frozen_predictions_vs_F17=original['frozen_predictions_vs_F17'],
        frozen_prediction_scope='Fixed old-four-input mean ratios transferred unchanged to the nine continuation inputs C01-C04 and C06-C10. Not refit. The original ten-input transfer remains the historical confirm10 contract and is not evaluable.',
        bootstrap=original['bootstrap'],
        primary=dict(original['primary'], cohort='C01-C04 and C06-C10; C05 is outside the denominator'),
        contrasts=[dict(candidate=name, reference='F17_A2_LIGHT_C', members=scientific_members)
            for name in ('R18C', 'R16C', 'R21C')],
        excluded_cohort=dict(alias=EXCLUDED_ALIAS, member=EXCLUDED_MEMBER, ids=excluded_ids,
            text_rejected_request='CONFIRM10_022', original_row_status='RUNNING',
            original_collection_status='FAILED_NO_RETRY', in_pairing_denominator=False,
            reason='Skip the whole av_snowy_1_0 group after TEXT_REJECTED on CONFIRM10_022. Keep the prompt, seed, masks and guardrails; do not retry 022 and do not replace the input.'),
        inherited_outputs=dict(source_run_id=ORIGINAL_RUN, source_scope_sha256=original['scope_sha256'],
            source_collection=REPORT + '/collection.json', source_collection_sha256=inventory['collection_sha256'],
            source_collection_status='FAILED_NO_RETRY', output_root=OUTPUT_ROOT,
            count=21, formal=20, warm=1, ids=inherited_ids, excluded_member=EXCLUDED_MEMBER,
            excluded_ids=excluded_ids, rows=inherited_rows,
            settlement=dict(status=job['status'], launch_id=job['launch_id'], actual_GPUh=job['actual_GPUh'],
                billing_sha256=job['billing_sha256'], billed_limit_GPUh=job['billed_limit_GPUh'],
                source_receipt=REPORT + '/central_settlement.json')),
        inherited_score_rows=score_rows,
        inherited_scores_receipt=dict(path=REPORT + '/partial_scores.json', sha256=file_sha(REPORT + '/partial_scores.json'),
            status='PARTIAL_SCORES_COMPLETE', pairs=16),
        untouched_sources={name: file_sha(name) for name in (
            ORIGINAL_MANIFEST, 'plans/cara_next_stage_20261105/confirm10/quote.json',
            REPORT + '/collection.json', REPORT + '/central_settlement.json',
            REPORT + '/output_inventory.json', REPORT + '/partial_scores.json')},
        claims_completion=False, original_ten_input_endpoint='NOT_EVALUABLE',
        deferred_supplements=['NATIVE_K18 waits until this continuation is finished; this card does not run k18 or the P probe'],
        execution_readiness=dict(scope='Same five-role Requests and guardrails. Dispatch is a later fresh-admission step, not this preparation.'),
        runtime_entry='plans/cara_next_stage_20261104/sensitivity/runner.py',
        loaded_request_entry=original['loaded_request_entry'],
        runtime_setup_ref=original['runtime_setup_ref'], runtime_torch_version=original['runtime_torch_version'],
        host='two_card', future_route='relay',
        postrelease_CPU_entry='plans/cara_next_stage_20261105/confirm10_continuation/postprocess.py',
        postrelease_CPU_resources=original['postrelease_CPU_resources'],
        postrelease_inputs=original['postrelease_inputs'],
        storage=copy.deepcopy(original['storage']),
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/' + RUN,
        preregistration_ref='plans/cara_next_stage_20261105/confirm10_continuation/PREREGISTRATION.md',
        quote=quote)
    card['scope_sha256'] = digest(card)
    return card


if __name__ == '__main__':
    card = build()
    quote = dict(card['quote'], mask_summary=card['mask_summary'], blocked=False,
        execution_authorized=True, GPU_dispatch_ready=True)
    for name, value in [('manifest.json', card), ('quote.json', quote)]:
        (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(run_id=card['run_id'], requests=len(card['matrix']),
        request_sum_seconds=card['quote']['request_sum_seconds'], center=card['quote']['forecast_GPUh'],
        range=card['quote']['range_GPUh'], hard=card['quote']['hard_GPUh'],
        scope_sha256=card['scope_sha256'], quote_GPU_dispatch_ready=True)))
