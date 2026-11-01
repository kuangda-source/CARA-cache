"""Explicit synthetic M1 files plus temporary original-lifecycle receipts."""
import copy
import json
from pathlib import Path
import shutil

import torch

from wcomr import cara_read_write_artifacts_r1 as reader
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_read_write_runner_binding_r1 import CARD, PRECISION, GEOMETRY, IMAGE, GPU
from wcomr.cara_s_endpoint_lifecycle_r1 import IDENTITY, SOURCE as LIFECYCLE_SOURCE
from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from wcomr.policy_price_terminal_r1 import record
from wcomr.wc73_execution_r1 import Pool
from test_cara_budget_lifecycle_r1 import fixture as lifecycle_fixture, put

ROOT = Path(__file__).resolve().parents[1]


def packet(project, writer):
    project = Path(project)
    stage = project/'.sync/cara-read-write-M1-CPU-fixture-full14'
    stage.mkdir(parents=True)
    names = (CARD, PRECISION, GEOMETRY, reader.ASSETS, reader.PROTOCOL, reader.SOURCE, LIFECYCLE_SOURCE)
    for name in names:
        target = stage/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
    capture, _, job = lifecycle_fixture(host='two_card', gpu_uuid=GPU,
        run_id='cara-read-write-M1-cpu-full14', billed_limit_GPUh=1.95)
    card = json.loads((stage/CARD).read_text())
    launch = record(capture, 'launch')
    launch.update(stage=str(stage), scope_sha256=card['scope_sha256'], container=stage.name+'-gpu', physical_paths=14)
    identity = {k:launch[k] for k in IDENTITY}
    for name in ('authorization', 'pending_release', 'billing', 'guardian'):
        put(capture, name, dict(record(capture, name), **identity))
    registration = record(capture, 'registration')
    registration.update(stage=str(stage), container_image=IMAGE, payload_sha256={p:sha(stage/p) for p in names})
    capture['payload_actual_sha256'] = registration['payload_sha256']
    reg_sha = put(capture, 'registration', registration)
    authority_sha = capture['files']['authorization']['sha256']
    job.update(identity, registration_sha256=reg_sha, authorization_sha256=authority_sha)
    envelope_sha = put(capture, 'central_reservation', dict(central_ledger_host='four_card', job=job))
    launch.update(registration_sha256=reg_sha, authorization_sha256=authority_sha, central_reservation_sha256=envelope_sha)
    expected = put(capture, 'launch', launch)
    container = capture['container']
    container.update(name=launch['container'], image=IMAGE, manifest_sha256=reg_sha)
    guardian = record(capture, 'guardian')
    guardian.update(status='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1', billing_sha256=capture['files']['billing']['sha256'])
    guardian['container_terminal_witness']['container'] = container
    put(capture, 'guardian', guardian)
    before = copy.deepcopy(json.loads((ROOT/'reports/cara_fast_B36_actual_central_reservation_r1_20261029.json').read_text())['central_envelope']['central_before'])
    before['jobs'][job['job_id']] = copy.deepcopy(job)
    before.update(Pool.accounting(before))
    after = copy.deepcopy(before)
    after['jobs'][job['job_id']].update(status='SETTLED', actual_GPUh=.05, billing_sha256=capture['files']['billing']['sha256'])
    after.update(Pool.accounting(after))
    after['events'].append(dict(sequence=len(after['events'])+1, unix=100.,
        type='SETTLE_ACTUAL_ADDITIVELY', job_id=job['job_id']))
    settlement = dict(central_ledger_host='four_card', launch_id=launch['launch_id'],
        billing_sha256=capture['files']['billing']['sha256'], central_before=before, central_after=after)
    output = project/'outputs'/launch['run_id']
    rows = []
    for slot in card['physical_matrix']:
        directory = output/'B'/slot['id']
        directory.mkdir(parents=True)
        role = slot['role']
        tag = {'RW00':'UNIFORM19_C', 'RW11':'D8_CONTROL'}.get(role, role)
        video = directory/(slot['member']+'.mp4')
        writer(video, slot['member']+'|'+tag)
        arguments = next({k:v for k,v in r.items() if k != 'partition'} for r in card['inputs'] if r['name'] == slot['member'])
        atomic_json(video.with_suffix('.json'), arguments)
        tensor = directory.parent/(slot['id']+'.pt')
        torch.save({'final_latent':torch.ones(1,2,2,2,2)*sum(tag.encode())}, tensor)
        result = dict(status='COMPLETE', scope_sha256=card['scope_sha256'], CPU_fixture_only=True,
            slot_id=slot['id'], member=slot['member'], role=role, solver_steps=36, guided_pairs=36,
            physical_model_pairs=card['roles'][role]['physical_pairs'], video_path=str(video),
            video_artifact=dict(path=str(video), bytes=video.stat().st_size, sha256=sha(video)))
        if role != 'NATIVE35':
            actions = card['roles'][role]['policy']['actions'].copy()
            if role.startswith('RW'):
                actions[7] = 'D' if role[-1] == '1' else 'C'
                result['intervention'] = dict(corner=role[2:], parent_state_sha256='a'*64)
            result['semantic_history'] = [dict(actual=a, fallback_reason=None) for a in actions]
        rows.append(dict(slot=slot, status='COMPLETE', result=result,
            tensor_artifact=dict(path=str(tensor), bytes=tensor.stat().st_size, sha256=sha(tensor))))
    collection = dict(scope_sha256=card['scope_sha256'], status='COMPLETE14_PENDING_RELEASE_NOT_SCORED',
        physical_model_pairs=512, scientific_score_pairs=8, diagnostic_timing_only=True, scientific_accepted=False, rows=rows)
    atomic_json(output/'read-write-collection.json', collection)
    atomic_json(output/'read-write-model-runner.json', dict(status='COMPLETE14_COLLECTION_PENDING_RELEASE',
        scope_sha256=card['scope_sha256'], source_revision=launch['source_revision'], complete_paths=14,
        physical_model_pairs=512, CPU_fixture_only=True, collection_sha256=sha(output/'read-write-collection.json')))
    return dict(capture=capture, expected_launch_sha256=expected, settlement=settlement,
        cpu_validation=True, cpu_shape=(93,64,64,3))
