#!/usr/bin/env python3
"""Production scope, charged failure settlement and signed/missing full93 scoring."""
import argparse
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def checks(stage,config):
    from wcomr.w1_native_reference_execution import validate_config,reserve_budget,settle_budget,audit_settlement,APPROVAL,CARD
    from wcomr.w1_native_reference_evaluation import reference_plan,summarize_scores
    validate_config(config)
    selected=copy.deepcopy(config);binding={'approval_ref':APPROVAL,'approved_card':CARD,'run_id':config['run_id'],
        'single_run_inclusive_cap_seconds':3600,'new_reference_phases':5,'original_denominator':[8,7,1],
        'usage_reset':False,'source_user_text':'CPU_SYNTHETIC_SCOPE_ONLY_NOT_HUMAN_AUTHORIZATION','approval_sha256':'a'*64}
    selected.update(GPU_execution_selected=True,gpu_uuid='GPU-CPU-SYNTHETIC-NOT-ADMISSION',execution_scope_authority=binding,
        production_cpu_stage='.sync/CPU_SYNTHETIC_NOT_ACTUAL',production_cpu_receipt_sha256='b'*64,
        production_cpu_payload_sha256=dict(config['payload_sha256'],**{'native-prod-config.json':'c'*64}))
    selected['payload_sha256'][APPROVAL]='a'*64;validate_config(selected,selected=True)
    refused=[]
    def refuse(label,fn):
        try:fn()
        except (ValueError,KeyError,RuntimeError,TypeError):refused.append(label)
        else:raise RuntimeError('Damaged production evidence accepted: '+label)
    mutations={
        'four_references':lambda c:c.update(new_reference_phases=4),
        'replace_original_rejection':lambda c:c.update(original_denominator=[8,8,0]),
        'seven_must_win':lambda c:c.update(all_seven_must_improve=True),
        'longer_cap':lambda c:c['execution_limits'].update(timeout_seconds=4500),
        'budget_as_scope':lambda c:c.update(execution_scope_authority={'cap':24}),
        'changed_CPU_core':lambda c:c['payload_sha256'].update({'src/wcomr/w1_native_reference_sampling.py':'0'*64}),
        'dropped_metric_reader':lambda c:c['payload_sha256'].pop('scripts/score_w1_native_references_cpu.py'),
    }
    for label,mutate in mutations.items():
        damaged=copy.deepcopy(config);mutate(damaged);refuse(label,lambda:validate_config(damaged))
    for label,mutate in {'unselected_GPU':lambda c:c.update(GPU_execution_selected=False),
                         'lost_production_CPU':lambda c:c.update(production_cpu_payload_sha256={}),
                         'longer_direct_scope':lambda c:c['execution_scope_authority'].update(single_run_inclusive_cap_seconds=4500)}.items():
        damaged=copy.deepcopy(selected);mutate(damaged);refuse(label,lambda:validate_config(damaged,selected=True))
    before=copy.deepcopy(config['budget_snapshot']);source='d'*40
    prepaid=reserve_budget(before,selected,1001)
    if prepaid['used_gpu_hours']!=before['used_gpu_hours']+1 or prepaid['gpu_jobs_launched']!=48:
        raise RuntimeError('Single complete five-reference prepaid job differs')
    # Includes an immediate spawn failure, a normal full run and a cap overshoot: each still charged.
    for wall in [0.125,2626.577,3601.0]:
        after=settle_budget(prepaid,before,selected,wall,1001)
        if abs(after['used_gpu_hours']-before['used_gpu_hours']-wall/3600)>1e-12:raise RuntimeError('Actual failure/run cost lost')
    wall=2626.577;after=settle_budget(prepaid,before,selected,wall,1001)
    supervisor={'source_revision':source,'run_id':config['run_id'],'config':selected,'reserved_seconds':3600,
        'hard_wall_cap_exceeded':False,'wall_seconds':wall,'budget_before':before,'budget_after':after,'pid':1001,'child_pid':1002}
    audit_settlement(supervisor,{'source_revision':source,'pid':1003},selected,after,source)
    changed=copy.deepcopy(prepaid);changed['used_gpu_hours']+=.1
    refuse('concurrent_ledger_change',lambda:settle_budget(changed,before,selected,wall,1001))
    bad=copy.deepcopy(before);bad['another_inflight']={}
    refuse('inflight_other_job',lambda:reserve_budget(bad,selected,1001))
    bad=copy.deepcopy(before);bad['used_gpu_hours']=23.01
    refuse('insufficient_whole_card',lambda:reserve_budget(bad,selected,1001))
    bad=copy.deepcopy(supervisor);bad['hard_wall_cap_exceeded']=True
    refuse('overshoot_not_full_acceptance',lambda:audit_settlement(bad,{'source_revision':source,'pid':1003},selected,after,source))
    core=json.loads((stage/'reports/wc_w1_native_reference_core_actual_cpu_r2_20261006.json').read_text())
    batches=next(c['result']['batches'] for c in core['checks'] if c['name']=='two-complete-five-reference-torch-fixtures')
    draft=json.loads((stage/'w1-reference-draft.json').read_text());artifacts=stage/'SYNTHETIC_NO_VIDEO/artifacts'
    plans=[]
    for batch in batches:
        receipt=copy.deepcopy(batch);receipt.update(run_card=CARD,backend_flags=receipt['cases'][0]['flags_before'])
        for case in receipt['cases']:
            if case['artifact'] is not None:
                case['artifact']['path']=str(artifacts/case['sample_name']/(case['sample_name']+'.mp4'))
        plan=reference_plan(receipt,draft,artifacts);plans.append(plan)
        expected=7 if batch['accepted_references']==5 else 5
        if plan['matched_accepted_scene_count']!=expected or not plan['complete_five_attempted']:raise RuntimeError('Accepted/rejected denominator lost')
        if batch['accepted_references']==5:
            bad=copy.deepcopy(receipt);bad['cases'][0]['sampling']['timesteps'][0]=994
            refuse('different_native_grid',lambda:reference_plan(bad,draft,artifacts))
            bad=copy.deepcopy(receipt);bad['cases'][0]['status']='VIDEO_REJECTED'
            refuse('outcome_status_mismatch',lambda:reference_plan(bad,draft,artifacts))
            bad=copy.deepcopy(receipt);bad['cases']=bad['cases'][:2]
            partial=reference_plan(bad,draft,artifacts)
            if partial['complete_five_attempted'] or partial['matched_accepted_scene_count']!=4:raise RuntimeError('Partial card relabelled full or gaps zero-filled')
    pairs=[]
    for pair in plans[0]['pairs']:
        index=next(r['original_CAL_index'] for r in draft['rows'] if r['scene']==pair['scene'])
        a=.3;value=a if pair['method']=='official_WC' else (.2 if index%3==0 else .4 if index%3==1 else .3)
        score={'frames':93,'pts':[[i,'1/16'] for i in range(93)],'frame_distances':[value]*93,
            'mean_LPIPS':sum([value]*93)/93,'reference_sha256':pair['reference']['sha256'],'candidate_sha256':pair['candidate']['sha256']}
        pairs.append({**pair,'score':score})
    summary=summarize_scores(pairs,plans[0])
    if not summary['improved_scenes'] or not summary['degraded_scenes'] or not summary['tied_scenes']:
        raise RuntimeError('Positive/negative/tie evidence discarded')
    for label,mutate in {'missing_loss':lambda p:p.pop(),
        'wrong_candidate_SHA':lambda p:p[0]['score'].update(candidate_sha256='0'*64),
        'short_video':lambda p:p[0]['score'].update(frames=92),
        'NaN_frame':lambda p:p[0]['score']['frame_distances'].__setitem__(0,float('nan')),
        'mean_not_frames':lambda p:p[0]['score'].update(mean_LPIPS=.99)}.items():
        bad=copy.deepcopy(pairs);mutate(bad);refuse(label,lambda:summarize_scores(bad,plans[0]))
    supervised=supervisor_checks(stage,selected,before)
    return {'status':'FIVE_REFERENCE_PRODUCTION_CPU_CONTRACT_AND_SIGNED_MISSING_SCORING_PASS_NOT_GPU',
        'refusals':refused,'refusal_count':len(refused),'complete_original_slots':5,'original_denominator':[8,7,1],
        'all_accepted_matched_scenes':7,'retained_rejections_matched_scenes':5,'partial_card_preserved':True,
        'mixed_signed_scene_scores':summary,'supervisor_CPU_integration':supervised,
        'CPU_synthetic_not_video_or_GPU_evidence':True,'GPU_submissions':0}


def supervisor_checks(stage,config,budget):
    """Real CPU child/process-group/FD/ledger; only admission and GPU command replaced."""
    supervisor=load(stage/'scripts/supervise_w1_native_references.py','w1_supervisor_cpu_integration')
    real_popen=supervisor.subprocess.Popen;results=[]
    for scenario in ['ordinary_CPU_child','spawn_failure','foreign_GPU_observation_stop_own_CPU_child']:
        with tempfile.TemporaryDirectory(prefix='w1-supervisor-CPU-',dir=stage) as directory:
            project=Path(directory);(project/'.sync').mkdir();(project/'reports').mkdir()
            (project/'runtime').mkdir();(project/'reports/budget.json').write_text(json.dumps(budget))
            selected=project/'.sync/selected';selected.mkdir();(selected/'native-prod-config.json').write_text(json.dumps(config))
            (selected/'src').symlink_to(stage/'src',target_is_directory=True)
            args=SimpleNamespace(project=project,stage=selected,output=project/'outputs'/config['run_id'],
                gpu_uuid=config['gpu_uuid'],source_revision='d'*40)
            observations=[0]
            def query(command,**kwargs):
                if '--query-gpu=uuid,name,memory.used,compute_cap' in command:
                    return config['gpu_uuid']+', NVIDIA RTX A6000, 0, 8.6\n'
                observations[0]+=1
                return (config['gpu_uuid']+', '+str(os.getpid())+'\n') if (
                    scenario=='foreign_GPU_observation_stop_own_CPU_child' and observations[0]>2) else ''
            def launch(command,**kwargs):
                if scenario=='spawn_failure':raise OSError('CPU_TEST_SIMULATED_SPAWN_FAILURE')
                if kwargs.get('start_new_session') is not True or len(kwargs.get('pass_fds',()))!=1:
                    raise RuntimeError('Supervisor lost isolated process group or inherited shared lock')
                seconds=5 if scenario.startswith('foreign_') else .02
                return real_popen([sys.executable,'-c','import time;time.sleep('+str(seconds)+')'],**kwargs)
            with patch.object(supervisor.argparse.ArgumentParser,'parse_args',return_value=args),\
                    patch.object(supervisor.subprocess,'check_output',side_effect=query),\
                    patch.object(supervisor.subprocess,'run',return_value=SimpleNamespace(returncode=0)),\
                    patch.object(supervisor.subprocess,'Popen',side_effect=launch):
                supervisor.main()
            result=json.loads((args.output/'supervisor.json').read_text())
            after=json.loads((project/'reports/budget.json').read_text())
            if (after['gpu_jobs_launched']!=budget['gpu_jobs_launched']+1
                    or any(k.endswith('_inflight') for k in after)
                    or abs(after['used_gpu_hours']-budget['used_gpu_hours']-result['wall_seconds']/3600)>1e-12):
                raise RuntimeError('Real supervisor failed inclusive CPU failure/exit settlement: '+str(result))
            if scenario=='ordinary_CPU_child' and result['exit_code']!=0:raise RuntimeError('Ordinary CPU child failed')
            if scenario=='spawn_failure' and (result['stop_reason']!='SUPERVISOR_ERROR' or result['child_pid'] is not None):
                raise RuntimeError('Spawn failure lost its durable state')
            if scenario.startswith('foreign_') and result['stop_reason']!='GPU_CONFLICT':raise RuntimeError('Foreign-use own-child stop failed')
            if result['child_pid'] is not None:
                try:os.kill(result['child_pid'],0)
                except ProcessLookupError:pass
                else:raise RuntimeError('Original CPU child remained alive')
            os.kill(os.getpid(),0)  # The synthetic foreign process (this checker) must survive.
            results.append({'scenario':scenario,'status':result['status'],'CPU_wall_seconds':result['wall_seconds'],
                'child_reaped':True,'charged_only_in_temporary_CPU_ledger':True,'GPU_submissions':0})
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--runtime',type=Path);p.add_argument('--actual-import',action='store_true');a=p.parse_args()
    sys.path.insert(0,str(a.stage/'src'));c=json.loads((a.stage/'native-prod-config.json').read_text())
    if a.actual_import:
        sys.path[:0]=[str(a.runtime),str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
        checker=load(a.stage/'scripts/check_w1_native_reference_core_cpu.py','native_core_import_check')
        draft=json.loads((a.stage/'w1-reference-draft.json').read_text())
        proof=checker.actual_import(a.stage,a.runtime,draft)
        runner=load(a.stage/'scripts/run_w1_native_references.py','native_prod_runner')
        setup,samples,rows=runner.build_arguments(draft,c,a.stage/'CPU_ARGUMENTS_ONLY',importlib.import_module('cosmos_predict2.config'))
        import torch
        for name in ['w1_native_reference_execution','w1_native_reference_evaluation','rv0_video_reader','rv0_lpips']:
            module=importlib.import_module('wcomr.'+name)
            if not Path(module.__file__).resolve().is_relative_to((a.stage/'src').resolve()):raise RuntimeError('Actual production import origin differs')
        if torch.cuda.is_initialized():raise RuntimeError('Production CPU import initialized CUDA')
        print(json.dumps({'status':'FIVE_REFERENCE_ACTUAL_PRODUCTION_ARGUMENTS_IMPORT_PASS_NO_MODEL_OR_CUDA',
            'native_source':proof,'selected_original_requests':len(samples),'changed_setup_keys':['worldcache_enabled','output_dir'],
            'GPU_submissions':0,'CUDA_initialized':False}));return
    print(json.dumps(checks(a.stage,c),allow_nan=False))


if __name__=='__main__':main()
