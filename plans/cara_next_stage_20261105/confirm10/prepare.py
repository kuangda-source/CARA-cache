"""Freeze the ten-input scope and CAL35 quote. No remote calls or execution."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from plans.cara_next_stage_20261105.g17_minitest.prepare import policy
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.policy_generator_r1.interval_grammar import digest

FREEZE = 'plans/cara_next_stage_20261105/generator_v1_frozen'
CATALOG = 'reports/dataset_source_group_audit_20260930.json'
CAL = 'plans/cara_next_stage_20261103/f19_speed190_cal/CAL35_MANIFEST_R1.json'
GRID = 'reports/cara_PG_Native18to35_committed_scheduler_CPU_20261023.json'
MEMBERS = [
    'av_5da7e548-93f4-4a9f-b59d-418051e7c859',
    'av_ba7d9ba6-04e5-4d30-a882-e51abe37aa84',
    'av_2cdc6699-574f-40b7-9b5b-15905c540274',
    'av_dc14df7f-b671-4d66-a98b-b751d8112e6c',
    'av_snowy_1_0',
    'av_0b82886b-be71-49f9-83a3-346bc0134c4b',
    'common_sense_f66000f7-6b6d-4bab-a889-cca8beb5b827',
    'human_222',
    'misc_3105317-hd_1920_1080_24fps',
    'physics_050',
]
EXCLUSION_EVIDENCE = json.loads(r'''{
    "prior_audit_ref": "reports/cara_new_input_pool48_exposure_r1_20261025.json",
    "prior_audit_sha256": "aaf39203ac6466dbf2a641c86fe8c2df9105bb8ad3548d7b9f0dfec8212a80dd",
    "catalog_ref": "reports/dataset_source_group_audit_20260930.json",
    "catalog_sha256": "6f8de690f5cb4f33c3d72aacb23ae6d723f9dd37213845f0472e8b3cb77543f0",
    "selection_rule": "6 av + one each common_sense/human/misc/physics; sort eligible source groups by SHA256(salt+name), no outcomes",
    "selection_salt": "CARA_CONFIRM10_V1_20261105:",
    "local_documents": 7184,
    "unchanged_prior_documents_reused": 4032,
    "local_inventory_sha256": "198fd3e13b3b5d79ca4cc826a1aaa6753df75bf8f97a13e5648ce3b49b898bcd",
    "local_excluded_names": [
        "av_002b815b-7595-4d54-a9f4-4c62c83d3009",
        "av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632",
        "av_395527b9-a6c7-429e-b5b8-d73b5f61f0e8",
        "av_3964e5dd-6704-4e3b-896f-dd8059731b27",
        "av_3f748a97-5a86-4311-a099-c2d1bd1e5fb1",
        "av_46fe9718-b496-4c30-b1b6-8b02028dd336",
        "av_4db72212-26c5-4265-a620-fdbe7b6dc3f7",
        "av_51b45829-502e-4143-9c32-c026bd6ab191",
        "av_5f567f79-4dd0-413d-a81a-2607684decf2",
        "av_7ffad222-afe2-4032-8341-9dec6181bb55",
        "av_94caa98b-1999-42f0-bafd-a5729c2fea25",
        "av_9a39abb2-7289-4b00-8707-887be4f46c04",
        "av_9f986144-dec3-490d-8c44-aed3a2727413",
        "av_a6beffc6-0c10-45d4-9ac1-06e482f25ebf",
        "av_animal_dear_1_0",
        "av_cbf12e70-0268-42c2-bd91-c76d42a86102",
        "av_cc90f226-5312-4e0f-959a-39cd4eb4d90d",
        "av_d9dab3fb-9b1e-4627-83c3-533fca9dcc92",
        "av_da2cfe87-9674-4463-a913-7623f68e16fa",
        "av_debris_2_0",
        "av_eae6d513-6148-4b3a-a5e1-cecd02451671",
        "av_f7247d16-f2db-4807-9e49-b5141861f6cf",
        "common_sense_049c9292-db5f-490b-a72b-546775e8156c",
        "common_sense_534f1783-3578-4d99-b5c9-1afe9c44e8c5",
        "common_sense_6487f37f-ef57-49ca-afdc-d898922b5191",
        "common_sense_67574e57-ed33-422c-b833-e0700e3d14ba",
        "common_sense_73c951a6-d5e3-4664-bd84-0598584e4a41",
        "common_sense_7bfad0d4-3135-464a-875e-8c0a17c81b37",
        "common_sense_7e5de0b8-ad22-4901-9fd8-361f5ea0220a",
        "common_sense_7fc96768-1540-447f-9802-0bd3762d981e",
        "common_sense_8df9180b-b182-49ad-92e5-2d000320f9f3",
        "common_sense_b2507f85-47b2-4fca-9a49-d555130fdd2b",
        "common_sense_bd3c4211-c1b0-4287-b3ba-78391f00c88a",
        "common_sense_ef9755f6-81de-4385-a6bd-1e478d7a4600",
        "human_034",
        "human_041",
        "human_045",
        "human_051",
        "human_068",
        "human_124",
        "human_125",
        "human_131",
        "human_136",
        "human_150",
        "human_173",
        "human_178",
        "human_186",
        "human_199",
        "human_212",
        "human_225",
        "human_233",
        "human_241",
        "human_251",
        "human_254",
        "human_272",
        "human_293",
        "industry_006",
        "industry_009",
        "industry_024",
        "industry_037",
        "industry_052",
        "industry_057",
        "industry_064",
        "industry_084",
        "industry_085",
        "industry_095",
        "misc_1200903-hd_1920_1080_30fps",
        "misc_12908442_1920_1080_25fps",
        "misc_13206250_3840_2160_60fps",
        "misc_13362641_3840_2160_25fps",
        "misc_13398218_3840_2160_60fps",
        "misc_13403670_3840_2160_30fps",
        "misc_18820560-uhd_3840_2160_25fps",
        "misc_2436088-uhd_3840_2160_25fps",
        "misc_2711212-uhd_3840_2160_24fps",
        "misc_2818567-uhd_3840_2160_24fps",
        "misc_3196505-sd_960_540_30fps",
        "misc_4258999-uhd_3840_2160_25fps",
        "misc_4707906-uhd_3840_2160_30fps",
        "misc_4761738-uhd_4096_2160_25fps",
        "misc_5629687-hd_1920_1080_25fps",
        "misc_856132-hd_1920_1080_30fps",
        "misc_9699390-uhd_3840_2160_30fps",
        "physics_001",
        "physics_006",
        "physics_017",
        "physics_018",
        "physics_040",
        "physics_043",
        "physics_045",
        "physics_066",
        "physics_143",
        "physics_145",
        "physics_174",
        "physics_181",
        "physics_189",
        "robot_000",
        "robot_001",
        "robot_005",
        "robot_016",
        "robot_022",
        "robot_033",
        "robot_043",
        "robot_047",
        "robot_054",
        "robot_060",
        "robot_095",
        "robot_097",
        "robot_106",
        "robot_110",
        "robot_135",
        "robot_145",
        "robot_147",
        "robot_149"
    ],
    "available_source_groups": 930,
    "protected_all48_excluded": true,
    "local_selected_identity_hits": 0,
    "observed_unix": 1793885157.343339,
    "limits": "Scoped recorded exposure only; not external/unrecorded jobs. First-use incremental check required before any future launch.",
    "remote": {
        "status": "READ_ONLY_SELECTED_IDENTITY_CHECK",
        "hostname": "minchen-X11DAi-N",
        "root": "/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace",
        "observed_unix": 1793885215.165692,
        "selected_group_names": [
            "av_0b82886b-be71-49f9-83a3-346bc0134c4b",
            "av_2cdc6699-574f-40b7-9b5b-15905c540274",
            "av_5da7e548-93f4-4a9f-b59d-418051e7c859",
            "av_ba7d9ba6-04e5-4d30-a882-e51abe37aa84",
            "av_dc14df7f-b671-4d66-a98b-b751d8112e6c",
            "av_snowy_1_0",
            "common_sense_f66000f7-6b6d-4bab-a889-cca8beb5b827",
            "human_222",
            "misc_3105317-hd_1920_1080_24fps",
            "physics_050"
        ],
        "identity_hits": [],
        "metadata_files_read": 316,
        "inventory_sha256": "75f520e81510bd15ba090bc1bac2cc776dc0a7a0604bf333dd3bc7e104921604",
        "scope": "Own project output paths plus declared collection/request/input/metric/result/receipt/score metadata; no external jobs",
        "Native_reuse_found": false,
        "GPU_submissions": 0,
        "ledger_written": false
    }
}''')


def read(name):
    return json.loads((ROOT / name).read_text())


def build():
    original = read(CAL)
    frozen = read(FREEZE + '/frozen_masks_r16_r18_r21.json')
    assert frozen['frozen']
    profile = profile_from(original['profile'])
    roles = {'NATIVE35': copy.deepcopy(original['roles']['NATIVE35']),
             'F17_A2_LIGHT_C': copy.deepcopy(original['roles']['F17_A2_LIGHT_C'])}
    roles['NATIVE35']['schedule'] = original['schedule']
    masks = {'NATIVE35': dict(mask='D' * 36, D=36, A=0, C=0, actual_updates=36),
             'F17_A2_LIGHT_C': dict(mask=''.join(roles['F17_A2_LIGHT_C']['policy']['actions']),
                                   D=17, A=10, C=9, actual_updates=36)}
    for name, selected in frozen['selected'].items():
        mask = selected['mask']
        roles[name] = dict(kind='speed_policy', requested_steps=35,
            policy=policy(profile, mask, [None] * 36), light_C=True, partial_updates=[],
            light_C_semantics=original['roles']['F17_A2_LIGHT_C']['light_C_semantics'],
            delta_semantics=original['roles']['F17_A2_LIGHT_C']['delta_semantics'])
        masks[name] = {k: selected[k] for k in ('mask', 'D', 'A', 'C', 'actual_updates')}
    order = ['NATIVE35', 'F17_A2_LIGHT_C', 'R18C', 'R16C', 'R21C']
    roles = {name: roles[name] for name in order}
    for name, role in roles.items():
        role['expected_updates'] = masks[name]['actual_updates']
    masks = {name: masks[name] for name in order}

    catalog = {row['name']: row for row in read(CATALOG)['records']}
    template = read('plans/cara_next_stage_20261105/avslc_minitest/manifest.json')['inputs'][0]
    inputs, provenance = [], []
    for name in MEMBERS:
        record = catalog[name]
        source = 'vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/' + name + '.json'
        raw = (ROOT / source).read_bytes()
        sample = json.loads(raw)
        assert hashlib.sha256(sample['prompt'].encode()).hexdigest() == record['prompt_sha256']
        inputs.append(dict(template, name=name, prompt=sample['prompt'], seed=0, partition='CONFIRM'))
        provenance.append(dict(record, source_ref=source, source_sha256=hashlib.sha256(raw).hexdigest(), seed=0))

    matrix = []
    def add(member, role, section):
        matrix.append(dict(id=f'CONFIRM10_{len(matrix)+1:03d}', member=member, role=role,
            section=section, seed=0, target_update=None, audit=False,
            eligible_clean_time=section != 'warm'))
    add(MEMBERS[0], 'F17_A2_LIGHT_C', 'warm')
    for i, member in enumerate(MEMBERS):
        rotated = order[i % len(order):] + order[:i % len(order)]
        for role in rotated:
            add(member, role, 'c')

    # Use the exact six-decimal coefficients specified for this card.
    cost = dict(shared=70.734852, D=6.772260, A=0.993956, original_C=0.637948)
    prices = {name: cost['shared'] + cost['D'] * m['D'] + cost['A'] * m['A']
              for name, m in masks.items()}  # All C readouts here are light C.
    raw = sum(prices[slot['role']] for slot in matrix)
    formal = 10 * sum(prices.values())
    center = (1.1 * raw + 1200) / 3600
    interval = [(.9 * raw + 1200) / 3600, (1.2 * raw + 1200) / 3600]
    anchors = dict(basis='CAL35 complete T_request interpolation, user-specified six-decimal coefficients; light C cost0. GPU bill excludes released CPU scoring.',
        CAL35_ref='reports/cara_f19_speed190_complete_r1_20261103/complete_analysis.json',
        marginal_seconds=cost, native36_assumption='36 actual D updates in the same formula',
        predicted_T_DD_seconds=dict(NATIVE35=252.65663431, F17_A2_LIGHT_C=131.65259999174998,
            **{k: v['T_pred'] for k, v in frozen['selected'].items()}),
        predicted_T_DD_sources='Native/F17 CAL35 means; generated arms use frozen7.51+6.81*nD+0.85*nA. k18 deferred.')
    quote = dict(anchors=anchors, request_prices_seconds=prices, request_sum_seconds=raw,
        formal_request_seconds=formal, warm_request_seconds=raw-formal,
        forecast_GPUh=center, range_GPUh=interval, hard_GPUh=math.ceil(interval[1]*10)/10,
        hard_limit_is_suggestion_only=False, expected_wall_hours=center,
        expected_wall_seconds=center*3600, model_load_seconds=600, release_margin_seconds=600,
        formal_requests=50, warm_requests=1, total_requests=51,
        warm_roles=['F17_A2_LIGHT_C'],
        approval_required_for_any_run=True, user_approved=True, GPU_submissions=0, ledger_reservations=0)
    sources = [FREEZE + '/frozen_masks_r16_r18_r21.json', FREEZE + '/frozen_gen_v1.json', CAL]
    card = dict(schema='CARA_CONFIRM10_PREPARE_QUOTE_R1', run_id='cara-generator-v1-confirm10-r1-20261105',
        phase='USER_APPROVED_PENDING_FRESH_ADMISSION', GPU_dispatch_ready=True,
        authority=dict(execution_authorized=True, ledger_reservation_authorized=True, sync_launch_authorized=True,
            user_quote='批准 confirm10：先去掉 Native-k18 上卡，k18 接线验收后单独补跑；硬限按重报的数',
            authorization_date='2026-11-05', cumulative_budget_policy='RUNNING_TOTAL_NO_CUMULATIVE_CAP'),
        reservation_event='CONFIRM10_WHOLE4_1_RESERVE', gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        inputs=inputs, inputs_by_alias={f'C{i+1:02d}': name for i, name in enumerate(MEMBERS)},
        input_provenance=provenance, input_exclusion_check=EXCLUSION_EVIDENCE,
        profile=original['profile'], schedule=original['schedule'], settings=original['settings'],
        roles=roles, matrix=matrix, mask_summary=masks, seed=0,
        counts=dict(a=0, b=0, c=50, warm=1, controls=10, total_requests=51, LPIPS_pairs=40, quality_positions=0),
        generated_A_alpha=1.0, F17_A2_gains=dict(other_A=1.0, step25=.5, step26=.5),
        native_references={}, native_reference_source='Ten new same-run NATIVE35 formal rows in collection.json; no historical Native reuse',
        fresh_Native_timing_requests=10, native_reuse_count=0,
        frozen_predictions_vs_F17={k: v['pred_mean4'] for k, v in frozen['selected'].items()},
        frozen_prediction_scope='Fixed old-four-input mean ratios transferred unchanged to new ten inputs; no prompt-specific sensitivity fit.',
        bootstrap=dict(unit='prompt', replicates=100000, seed=20261105, interval='linear percentile95'),
        primary=dict(candidate='R18C', reference='F17_A2_LIGHT_C',
            effect='Alex(candidate, Native36)-Alex(reference, Native36)',
            success='mean<0 and CI95.upper<0', secondary_noninferiority_margin=.01,
            secondary_success='If primary not met, CI95.upper<0.01'),
        contrasts=[dict(candidate=name, reference=reference, members=MEMBERS)
            for name, reference in [('R18C', 'F17_A2_LIGHT_C'), ('R16C', 'F17_A2_LIGHT_C'),
                                    ('R21C', 'F17_A2_LIGHT_C')]],
        deferred_supplements=['NATIVE_K18: 10 formal requests after adapter CPU acceptance and separate approval; R18C-vs-k18 secondary endpoint deferred'],
        execution_readiness=dict(scope='Five36-update arms supported by current Requests; Linux CPU and fresh admission required'),
        runtime_entry='plans/cara_next_stage_20261104/sensitivity/runner.py',
        loaded_request_entry='wcomr.cara_f19_speed190_requests_r1.Requests',
        runtime_setup_ref='configs/f1_setup.json', runtime_torch_version='2.7.1+cu128',
        host='two_card', future_route='relay',
        postrelease_CPU_entry='plans/cara_next_stage_20261105/confirm10/postprocess.py',
        postrelease_CPU_resources=dict(cpus=2, RAM_GiB=8, wall_seconds=7200, max_vCPUh=4),
        postrelease_inputs=sources, storage=copy.deepcopy(read('plans/cara_next_stage_20261105/avslc_minitest/manifest.json')['storage']),
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/cara-generator-v1-confirm10-r1-20261105',
        preregistration_ref='plans/cara_next_stage_20261105/confirm10/PREREGISTRATION.md', quote=quote)
    card['scope_sha256'] = digest(card)
    return card


if __name__ == '__main__':
    card = build()
    for name, value in [('manifest.json', card), ('quote.json', dict(card['quote'], mask_summary=card['mask_summary'], blocked=False))]:
        (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(center=card['quote']['forecast_GPUh'], range=card['quote']['range_GPUh'],
        suggested_hard=card['quote']['hard_GPUh'], requests=len(card['matrix']), GPU_dispatch_ready=True)))
