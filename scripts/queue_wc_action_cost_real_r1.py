#!/usr/bin/env python3
"""One sequential complete action-cost card after the original main evidence chain.

CPU waiting does not submit GPU work, reserve budget, or alter the original card.
The two separately Git-bound lifecycle files preserve the accepted model payload.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def worker(args):
    import fcntl
    import sys
    from importlib import util
    packet = json.loads((args.post/'packet.json').read_text())
    launch, proof = packet['selected_CPU_launch'], packet['selected_CPU_proof']
    stage, root = Path(launch['stage']), args.project
    c = json.loads((stage/'action-cost-config.json').read_text())
    target = args.post/'receipt.json'
    assert not target.exists()
    assert launch['source_revision'] == args.source_revision == proof['source_revision']
    assert proof['exit_code'] == 0 and proof['local_native_bytes_binding_scope_and_request_verified']
    assert sha(stage/'receipt.json') == proof['files']['receipt.json']['sha256']
    assert sha(stage/'action-cost-config.json') == launch['config_sha256']
    assert sha(args.post/'driver.py') == packet['queue_driver_sha256']
    assert all(sha(stage/name) == digest for name, digest in packet['lifecycle_sha256'].items())
    sys.path.insert(0, str(stage/'src'))
    from wcomr.source_aware_action_cost_production_r1 import validate, validate_selected
    validate(root, stage); validate_selected(c, root, stage)
    assert c['execution_run_id'] == 'wc-mf-c-a-p-d-real-cost-r1'
    assert c['preregistration']['forecast']['forecast_complete_GPUh'] <= 4
    state = {'status':'WAITING_ORIGINAL32_GPU_RAW_AND_ALL93_SCORE_NOT_GPU',
             'pid':os.getpid(), 'source_revision':args.source_revision,
             'run_id':c['execution_run_id'], 'started_unix':time.time(),
             'model_payload_files':271, 'GPU_submissions':0, 'ledger_written':False,
             'queue_driver_sha256':packet['queue_driver_sha256'],
             'lifecycle_sha256':packet['lifecycle_sha256'],
             'selected_CPU_receipt_sha256':sha(stage/'receipt.json')}
    write(target, state)
    main = root/'outputs/wc-ra-plus-a-full-video-r1'
    raw_post = root/'.sync/wc-ra-plus-a-post-cpu-r1-20261010'
    score_post = root/'.sync/wc-ra-plus-a-score-cpu-r1-20261010'
    original = packet['original_main_launch']
    try:
        while True:
            gpu = json.loads((main/'supervisor.json').read_text())
            raw = json.loads((raw_post/'receipt.json').read_text())
            score = json.loads((score_post/'receipt.json').read_text())
            assert gpu['pid'] == original['supervisor_pid'] and raw['pid'] == original['post_CPU_pid']
            assert gpu['source_revision'] == raw['source_revision'] == original['source_revision']
            assert score['pid'] == packet['original_score_launch']['supervisor_pid']
            pids = [r.get(key) for r in (gpu,raw,score) for key in ('pid','child_pid')]
            if any(p and Path('/proc/'+str(p)).exists() for p in pids):
                time.sleep(5); continue
            assert gpu['status'] == 'EXITED_REQUIRES_RESULT_AUDIT' and gpu['exit_code'] == 0
            assert raw['exit_code'] == 0 and score['exit_code'] == 0
            assert score['status'] == 'RA_PLUS_A_COMPLETE_ALL93_CPU_SCORING_EXIT0_NOT_METHOD_ACCEPTANCE'
            score_result = json.loads((score_post/'result.json').read_text())
            assert sha(score_post/'result.json') == score['result_sha256']
            assert score_result['status'] == 'RA_PLUS_A_FULL_COMPARISON_COMPLETE_AVAILABLE_ALL93_FIDELITY_AND_COST_NOT_CLEAN_SPEED'
            state['original_main_complete_evidence'] = {
                'GPU_supervisor_sha256':sha(main/'supervisor.json'),
                'raw_CPU_receipt_sha256':sha(raw_post/'receipt.json'),
                'all93_score_CPU_receipt_sha256':sha(score_post/'receipt.json'),
                'all93_score_result_sha256':sha(score_post/'result.json'),
                'original_PIDs_absent':pids,
                'original_GPU_wall_seconds':gpu['wall_seconds'],
                'quality_outcome_is_not_a_standalone_win_gate':True}
            break
        # Capture the original settled budget before any next-card reservation.
        # This is a source/receipt barrier, not a required scientific win.
        state['status'] = 'WAITING_ORIGINAL_MAIN_INDEPENDENT_CAPTURE_NOT_GPU'
        write(target,state)
        accepted = args.post/'main-independent-acceptance.json'
        while not accepted.exists():time.sleep(5)
        acceptance = json.loads(accepted.read_text())
        assert acceptance['status'] == 'ORIGINAL_COMPLETE32_INDEPENDENT_GPU_RAW_AND_ALL93_CAPTURE_ACCEPTED'
        assert acceptance['main_source_revision'] == original['source_revision']
        assert acceptance['score_source_revision'] == packet['original_score_launch']['source_revision']
        for name,digest in acceptance['remote_receipt_sha256'].items():
            assert sha(root/name) == digest
        state['original_main_complete_evidence']['independent_acceptance_sha256'] = sha(accepted)
        assert all(not Path('/proc/'+str(p)).exists() for p in
                   (proof['original_PIDs_absent']) if p)
        spec = util.spec_from_file_location('action_cost_supervisor',stage/'GPU-lifecycle/supervisor.py')
        module = util.module_from_spec(spec);spec.loader.exec_module(module)
        state['status'] = 'WAITING_FRESH_GPU_AND_SETTLED_LEDGER_NOT_SUBMITTED';write(target,state)
        while True:
            before = json.loads((root/'reports/budget.json').read_text())
            assert before['cap_gpu_hours'] == 77.89524658965853 and before['automatic_single_job_gpu_hours'] == 4
            if any('inflight' in k for k in before):
                time.sleep(5); continue
            assert before == gpu['budget_after'], 'Another job changed the settled ledger; return for reconciliation'
            assert before['used_gpu_hours'] + c['preregistration']['forecast']['forecast_complete_GPUh'] <= before['cap_gpu_hours']
            with (root/'.sync/f1.lock').open('a+') as lock:
                try:
                    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    time.sleep(5);continue
                observation = module.observe(c['gpu_uuid'])
                if observation['pids'] or observation['memory_used_mib'] > 1024:
                    time.sleep(5);continue
                assert observation['uuid'] == c['gpu_uuid'] and observation['compute_cap'] == '8.6'
            break
        validate(root,stage);validate_selected(c,root,stage)
        assert not (root/'outputs'/c['execution_run_id']).exists()
        import shutil
        assert shutil.disk_usage(root).free > 50*(1<<30)
        python = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        command = [python,str(stage/'GPU-lifecycle/supervisor.py'),'--project',str(root),
                   '--stage',str(stage),'--source-revision',args.source_revision]
        with (args.post/'GPU-supervisor.log').open('x') as log:
            child = subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        (args.post/'raw-CPU').mkdir()
        (args.post/'raw-CPU/driver.py').write_bytes((stage/'GPU-lifecycle/post_CPU.py').read_bytes())
        post_command = [python,str(args.post/'raw-CPU/driver.py'),'--project',str(root),
                        '--stage',str(stage),'--post',str(args.post/'raw-CPU'),
                        '--source-revision',args.source_revision,'--supervisor-pid',str(child.pid)]
        with (args.post/'raw-CPU/driver.log').open('x') as log:
            auditor = subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(env,CUDA_VISIBLE_DEVICES=''),start_new_session=True)
        gpu_launch = {'run_id':c['execution_run_id'],'stage':str(stage),
                      'post_CPU_stage':str(args.post/'raw-CPU'),'source_revision':args.source_revision,
                      'supervisor_pid':child.pid,'post_CPU_pid':auditor.pid,
                      'config_sha256':sha(stage/'action-cost-config.json'),
                      'payload_files':271,'lifecycle_sha256':packet['lifecycle_sha256'],
                      'post_driver_sha256':packet['lifecycle_sha256']['GPU-lifecycle/post_CPU.py'],
                      'budget_before':before,'planned_scope':c['preregistration']['scope_counts'],
                      'forecast_complete_GPUh':c['preregistration']['forecast']['forecast_complete_GPUh'],
                      'gpu_uuid':c['gpu_uuid'],'command':command,'post_CPU_command':post_command,
                      'selected_CPU_receipt_sha256':sha(stage/'receipt.json'),
                      'observed_unix':time.time(),'GPU_submissions_by_launch':1,
                      'original_main_complete_evidence':state['original_main_complete_evidence']}
        write(args.post/'GPU-launch.json',gpu_launch)
        write(args.post/'raw-CPU/launch.json',gpu_launch)
        state.update(status='COMPLETE_ACTION_COST_GPU_SUBMITTED_ONCE',
                     GPU_submissions=1,supervisor_pid=child.pid,post_CPU_pid=auditor.pid)
        write(target,state)
        child.wait();auditor.wait()
        gpu_receipt = json.loads((root/'outputs'/c['execution_run_id']/'supervisor.json').read_text())
        raw_receipt = json.loads((args.post/'raw-CPU/receipt.json').read_text())
        state.update(status='ACTION_COST_COMPLETE_GPU_AND_RAW_CPU_EXITED_REQUIRE_INDEPENDENT_CAPTURE',
                     GPU_exit_code=gpu_receipt['exit_code'],raw_CPU_exit_code=raw_receipt['exit_code'],
                     exit_code=0 if gpu_receipt['exit_code']==raw_receipt['exit_code']==0 else 1)
    except BaseException as error:
        state.update(status='ACTION_COST_SEQUENTIAL_CHAIN_FAILED_NO_RETRY_COMPLETE_SCOPE_RETAINED',
                     error_type=type(error).__name__,error=str(error),exit_code=1)
    finally:
        state['ended_unix'] = time.time();write(target,state)
    raise SystemExit(state['exit_code'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true')
    p.add_argument('--project',type=Path);p.add_argument('--post',type=Path)
    p.add_argument('--source-revision');args=p.parse_args()
    if args.worker:return worker(args)
    launch=json.loads(Path('reports/wc_action_cost_real_selected_cpu_r1_launch_20261010.json').read_text())
    proof=json.loads(Path('reports/wc_action_cost_real_selected_cpu_r1_terminal_20261010_capture.json').read_text())
    revision=launch['source_revision']
    assert proof['source_revision']==revision and proof['exit_code']==0 and proof['local_native_bytes_binding_scope_and_request_verified']
    destination=Path('reports/wc_action_cost_real_r1_sequence_launch_20261010.json');assert not destination.exists()
    names={'GPU-lifecycle/supervisor.py':'scripts/supervise_wc_action_cost_real_r1.py',
           'GPU-lifecycle/post_CPU.py':'scripts/supervise_wc_action_cost_real_post_cpu_r1.py',
           'queue-driver.py':'scripts/queue_wc_action_cost_real_r1.py'}
    contents={}
    for remote,local in names.items():
        raw=Path(local).read_bytes()
        assert raw==subprocess.check_output(['git','show',revision+':'+local])
        contents[remote]={'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}
    packet={'selected_CPU_launch':launch,'selected_CPU_proof':proof,
            'original_main_launch':json.loads(Path('reports/wc_ra_plus_a_r1_GPU_launch_20261010.json').read_text()),
            'original_score_launch':json.loads(Path('reports/wc_ra_plus_a_score_cpu_r1_launch_20261010.json').read_text()),
            'lifecycle_sha256':{n:v['sha256'] for n,v in contents.items() if n!='queue-driver.py'},
            'queue_driver_sha256':contents['queue-driver.py']['sha256']}
    code='P='+repr(packet)+'\nF='+repr(contents)+'\n'+r'''
import base64,hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(P['selected_CPU_launch']['stage'])
assert hashlib.sha256((stage/'receipt.json').read_bytes()).hexdigest()==P['selected_CPU_proof']['files']['receipt.json']['sha256']
assert all(not pathlib.Path('/proc/'+str(x)).exists() for x in P['selected_CPU_proof']['original_PIDs_absent'])
post=root/'.sync/wc-action-cost-real-sequence-r1-20261010';assert not post.exists();post.mkdir()
assert not (stage/'GPU-lifecycle').exists();(stage/'GPU-lifecycle').mkdir()
for name,value in F.items():
 raw=base64.b64decode(value['base64'],validate=True);assert hashlib.sha256(raw).hexdigest()==value['sha256']
 target=post/'driver.py' if name=='queue-driver.py' else stage/name
 assert not target.exists();target.write_bytes(raw)
binding={'source_revision':P['selected_CPU_launch']['source_revision'],'model_payload_files':271,'run_id':'wc-mf-c-a-p-d-real-cost-r1',
 'model_config_sha256':P['selected_CPU_launch']['config_sha256'],'lifecycle_sha256':P['lifecycle_sha256']}
(stage/'GPU-lifecycle/binding.json').write_text(json.dumps(binding,indent=2)+'\n')
(post/'packet.json').write_text(json.dumps(P,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(post/'driver.py'),'--worker','--project',str(root),'--post',str(post),'--source-revision',P['selected_CPU_launch']['source_revision']]
with (post/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
value={'status':'SEQUENTIAL_CPU_WAITER_DISPATCHED_NOT_GPU_SUBMISSION','sequence_pid':child.pid,'sequence_stage':str(post),'selected_stage':str(stage),
 'source_revision':P['selected_CPU_launch']['source_revision'],'command':command,'queue_driver_sha256':P['queue_driver_sha256'],'lifecycle_sha256':P['lifecycle_sha256'],
 'GPU_submissions_by_queue_dispatch':0,'ledger_written_by_queue_dispatch':False,'observed_unix':time.time()}
(post/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    value=json.loads(call.stdout);destination.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
