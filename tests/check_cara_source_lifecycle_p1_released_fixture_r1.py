"""Fresh full146 CPU media/latent fixture; internal scores are explicitly synthetic.

The accepted real host broker is reused separately. This fixture exercises the
new released reader with real files, original-process observation and the real
93-frame decoder, without replaying a prior algorithm or metric experiment.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

from wcomr import cara_source_lifecycle_p1_artifacts_r1 as reader
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_endpoint_lifecycle_r1 import IDENTITY,SOURCE as LIFECYCLE
from wcomr.cara_source_lifecycle_p1_collection_r1 import Collection
from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUN_ID,STAGE_NAME,CARD,PRECISION,GEOMETRY,WEIGHTS,GPU,IMAGE
from wcomr.cara_source_lifecycle_p1_service_r1 import KIND
from wcomr.gpu_budget_pool_v2 import atomic_json,SCHEMA
from wcomr.policy_price_terminal_r1 import record
from wcomr.wc73_execution_r1 import Pool
from check_cara_s_endpoint_real_video_r1 import write_video
from check_cara_source_lifecycle_p1_score_fixture_r1 import metric
from test_cara_budget_lifecycle_r1 import fixture as lifecycle_fixture,put
from test_cara_source_lifecycle_p1_collection_r1 import SyntheticRequests
from test_cara_source_lifecycle_estimation_r1 import fixture_packet

ROOT=Path(__file__).resolve().parents[1]


def settled_fixture(capture,job):
    """Pure in-memory CPU ledger; never opens a real ledger."""
    bill,launch=record(capture,'billing'),record(capture,'launch')
    before=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=50.,origin_gpu_jobs_launched=10,
        jobs={'old-unknown-16.5':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-OLD',billed_limit_GPUh=16.5),
              launch['run_id']:copy.deepcopy(job)},events=[])
    before.update(Pool.accounting(before));after=copy.deepcopy(before)
    after['jobs'][launch['run_id']].update(status='SETTLED',actual_GPUh=bill['actual_GPUh'],billing_sha256=capture['files']['billing']['sha256'])
    after['events'].append(dict(type='SETTLE_ACTUAL_ADDITIVELY',job_id=launch['run_id']));after.update(Pool.accounting(after))
    return dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=capture['files']['billing']['sha256'],
                central_before=before,central_after=after)


def build(project):
    import torch
    from wcomr.mid_coverage import tree_digest
    from check_cara_s_endpoint_scoring_cli_r1 import write_black
    project=Path(project);stage=project/'.sync'/STAGE_NAME
    stage.mkdir(parents=True)
    names=(reader.SOURCE,CARD,PRECISION,GEOMETRY,WEIGHTS,reader.ASSETS,reader.PROTOCOL,LIFECYCLE,
           'src/wcomr/cara_source_lifecycle_p1_inventory_r1.py','src/wcomr/cara_source_lifecycle_p1_scores_r1.py')
    for name in names:
        path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
    from wcomr.cara_source_lifecycle_p1_plan_r1 import build as build_card
    labels,design,parent=fixture_packet();card=build_card(parent,design)
    # Synthetic labels have their own design identity. The full positions and
    # production request identities remain the same registered complete scope.
    atomic_json(stage/CARD,card)
    weights=[1.]*36
    atomic_json(stage/WEIGHTS,dict(weights=weights,CPU_fixture_only=True))
    capture,_,job=lifecycle_fixture(host='two_card',gpu_uuid=GPU,run_id=RUN_ID,billed_limit_GPUh=18.)
    launch=record(capture,'launch');launch.update(stage=str(stage),scope_sha256=card['scope_sha256'],
                                               container=stage.name+'-gpu',admission_sha256='3'*64)
    allocation={k:launch[k] for k in IDENTITY}
    for name in ('authorization','pending_release','billing','guardian'):put(capture,name,dict(record(capture,name),**allocation))
    authority=record(capture,'authorization');authority['card_kind']=KIND;put(capture,'authorization',authority)
    registration=record(capture,'registration')
    registration.update(stage=str(stage),container_image=IMAGE,payload_sha256={n:file_sha(stage/n) for n in names})
    capture['payload_actual_sha256']=registration['payload_sha256'];reg_sha=put(capture,'registration',registration)
    launch.update(registration_sha256=reg_sha,authorization_sha256=capture['files']['authorization']['sha256'])
    job.update(allocation,registration_sha256=reg_sha,authorization_sha256=launch['authorization_sha256'])
    launch['central_reservation_sha256']=put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
    expected=put(capture,'launch',launch)
    capture['container'].update(name=launch['container'],image=IMAGE,manifest_sha256=reg_sha)
    context={k:launch[k] for k in IDENTITY}
    context.update(CPU_fixture_only=True,guardian_started_monotonic=20.,hard_GPUh=18.,admission_sha256='3'*64,
                   launch_sha256=expected,registration_sha256=reg_sha)
    output=project/'outputs'/RUN_ID;output.mkdir(parents=True)
    cache=project/'media-cache';cache.mkdir()
    decoded={}
    runtime=SyntheticRequests(context,labels)
    original_execute=runtime.execute
    def execute(slot,directory):
        proof=original_execute(slot,directory)
        native=slot['kind'] in ('native','allD')
        candidate='NATIVE35' if native else slot['candidate_id']
        tag='BLACK' if slot['member']=='human_199' else slot['member']+'|'+str(int(digest(candidate)[:2],16)%2)
        cached=cache/(digest(tag)+'.mp4')
        if not cached.exists():
            if tag=='BLACK':write_black(cached)
            else:write_video(cached,tag,height=64,width=64)
        path=Path(proof['video']['path']);shutil.copyfile(cached,path)
        tensor=torch.ones(1,2,2,2,2)*(int(digest(dict(member=slot['member'],candidate=candidate))[:4],16)%100)
        torch.save(tensor,proof['final_latent']['path'])
        proof['video'].update(sha256=file_sha(path))
        proof['final_latent'].update(file_sha256=file_sha(proof['final_latent']['path']),tensor_sha256=tree_digest(tensor))
        proof['pre_encode_RGB']['sha256']=digest(tag)
        proof['T_DD']=None if slot['timing']=='OFF' else .01
        args=next({k:v for k,v in r.items() if k!='partition'} for r in card['inputs'] if r['name']==slot['member'])
        atomic_json(path.with_suffix('.json'),dict(args,seed=0,num_steps=35))
        decoded[file_sha(path)]=reader.decode_video(dict(proof['video'],bytes=path.stat().st_size),shape=(93,64,64,3))
        return proof
    responses={}
    def score(packet,directory):
        accepted=runtime.score(packet,directory)
        by_proof={d['proof_sha256']:decoded[d['sha256']] for pair in packet['pairs'] for d in (pair['candidate'],pair['reference'])}
        accepted.update(full_fidelity_rows=[metric(pair,by_proof) for pair in packet['pairs']],
                        config_sha256=digest(packet),result_sha256=digest(accepted),execution_sha256='e'*64)
        responses[packet['candidate_id']]=copy.deepcopy(accepted)
        return accepted
    bounds=dict(path_seconds=10.,FIT_score_seconds=2.,overhead_seconds=.1)
    collection=Collection(root=output/'algorithm',card=card,context=context,weights=weights,
        execute=execute,score=score,elapsed_seconds=lambda:runtime.clock,query_bounds=bounds,cpu_validation=True,create=True)
    summary=collection.run(allow_new=True)
    assert summary.get('failure') is None,summary.get('failure')
    atomic_json(output/'P1-model-runner.json',dict(status='P1_FULL146_ALGORITHM_COMPLETE_PENDING_RELEASE',
        scope_sha256=card['scope_sha256'],source_revision=launch['source_revision'],CPU_fixture_only=True,semantic_positions=146,
        algorithm_summary_sha256=file_sha(output/'algorithm/algorithm-summary.json'),
        loaded_model_checks=dict(final_state_restored=True,caller_forward_binding_restored=True,shared_eval_verified=True)))
    atomic_json(stage/'whole-quote.json',dict(fair_search_query_bounds=bounds))
    queue=output/'internal-FIT-queue';queue.mkdir()
    spec=dict(project=str(project),stage=str(stage),CPU_fixture_only=True,context=context,
        profile=card['profile'],artifact_root=str(output/'algorithm'),queue=str(queue))
    atomic_json(queue/'binding.json',spec)
    child=subprocess.Popen([sys.executable,'-c','pass'],env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
    service_identity=bind_original_process(child.pid);assert child.wait(timeout=20)==0
    assert observe_original_process(service_identity)['original_live'] is False
    ended=time.time()
    atomic_json(queue/'service-start.json',dict(identity=service_identity,binding_sha256=digest(spec)))
    terminal=dict(binding_sha256=digest(spec),error=None,ended_unix=ended)
    atomic_json(queue/'service-terminal.json',terminal)
    closed=dict(complete=True,identity=service_identity,exit_code=0,terminal_error=None,
        terminal_sha256=file_sha(queue/'service-terminal.json'),binding_sha256=digest(spec),ended_unix=ended)
    atomic_json(queue/'guardian-service-closed.json',closed)
    for candidate,accepted in responses.items():
        target=queue/('score-'+candidate);target.mkdir()
        atomic_json(target/'response.json',dict(payload=accepted))
    bill=record(capture,'billing');bill.update(ended_monotonic=20.+runtime.clock+1,wall_seconds=runtime.clock+1,
        actual_GPUh=(runtime.clock+1)/3600,ended_unix=ended+1.)
    put(capture,'billing',bill)
    guardian=record(capture,'guardian');guardian.update(status='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1',
        billing_sha256=capture['files']['billing']['sha256'],ended_monotonic=bill['ended_monotonic'],FIT_service_terminal_witness=closed)
    guardian['container_terminal_witness']['container']=capture['container'];put(capture,'guardian',guardian)
    settlement=settled_fixture(capture,job)
    return dict(capture=capture,expected_launch_sha256=expected,settlement=settlement,cpu_validation=True,cpu_shape=(93,64,64,3)),\
        dict(collection=collection,runtime=runtime,spec=spec,queue=queue,responses=responses)


def read_fixture(args,state):
    """Only the accepted broker boundary is synthetic; the new reader is real."""
    class SealedHost:
        def recover_query(self,candidate):
            assert candidate in state['responses']
            return dict(status='ORIGINAL_COMPLETE_FIT_ACCEPTED')
    with patch.object(reader.Host,'reader',return_value=SealedHost()):
        return reader.released_artifacts(**args)
