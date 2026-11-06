#!/usr/bin/env python3
"""Read-only all14 file audit, eligible all93 scores, explicit all64 missingness."""
import argparse
import ast
from collections.abc import Mapping
import copy
import gc
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser()
    for name in ('project','stage'): p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--source-revision', required=True)
    a = p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(a.stage/'src'))
    from wcomr.full64_partial_recovery_cpu import verifier, slots, numerical_pairing, zero_mask_proof, sha_file, function, compile_function
    from wcomr.rv0_video_reader import decoded_video, probe_video
    from wcomr.lpips_resource_identity import audit
    reg = json.loads((a.stage/'preregistration.json').read_text())
    if ({n:sha_file(a.stage/n) for n in reg['payload_sha256']} != reg['payload_sha256']
            or reg['planned_original_paths'] != 64 or reg['maximum_saved_complete_paths'] != 14
            or reg['maximum_numerical_paired_scores'] != 8 or reg['frames_per_pair'] != 93):
        raise ValueError('New per-path CPU scope and original payload required')
    gpu = Path(reg['original_GPU_stage']); out = a.project/'outputs'/reg['original_run_id']
    source = out/'diagnostic/receipt.json'; supervisor = out/'supervisor.json'
    if sha_file(source) != reg['original_runner_sha256'] or sha_file(supervisor) != reg['original_supervisor_sha256']:
        raise ValueError('Original failed terminal receipt changed')
    runner = json.loads(source.read_text()); original_supervisor = json.loads(supervisor.read_text())
    if (runner['status'] != 'COMPLETE64_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED'
            or original_supervisor['exit_code'] != 1
            or any(Path('/proc/'+str(pid)).exists() for pid in reg['original_PIDs'])
            or sha_file(gpu/'current-birth-full64-config.json') != reg['original_config_sha256']
            or runner['config'] != json.loads((gpu/'current-birth-full64-config.json').read_text())):
        raise ValueError('Original failed complete64 identity and terminal handles required')
    c = runner['config']
    for directory, key in [(gpu,'payload_sha256'),(a.project,'project_input_sha256'),(a.project/'runtime','runtime_source_sha256')]:
        if any(sha_file(directory/n) != v for n,v in c[key].items()):
            raise ValueError('Original source or fixed input bytes changed: '+key)
    verify, derivation = verifier(gpu, c['payload_sha256'])
    masked = zero_mask_proof(a.project/'runtime', gpu, c)
    import numpy as np
    import torch
    if torch.__version__ != '2.7.1+cu128' or torch.cuda.is_initialized():
        raise ValueError('Original pinned CPU Torch runtime required')
    def forbidden(*args, **kwargs): raise RuntimeError('Partial recovery CPU forbids CUDA/downloads')
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden; torch.set_num_threads(2)
    digest = compile_function(function(ast.parse((gpu/'src/wcomr/mid_coverage.py').read_text()),'tree_digest'),
        {'hashlib':hashlib,'torch':torch,'np':np,'Mapping':Mapping})
    rows = slots(runner); complete = [s for s in rows if s['written_complete']]
    if len(complete) != 14 or sum(s['row'] is not None and not s['written_complete'] for s in rows) != 1:
        raise ValueError('Original14 complete/1 failed/49 unstarted denominator differs')
    refs = {v['sample_name']:v for v in runner['matched_Native_metadata']}
    old_bytes = gzip.decompress((a.stage/reg['legacy_score_file_ref']).read_bytes())
    old = json.loads(old_bytes)
    if hashlib.sha256(old_bytes).hexdigest() != reg['legacy_score_native_sha256']:
        raise ValueError('Accepted old full32 score original bytes changed')
    resource = a.project/'.sync/wc-rv0-lpips-resource-v2'
    identity = audit(resource, reg['payload_sha256']['src/wcomr/rv0_lpips.py'])
    if identity != old['actual_resource_identity'] or any(reg['payload_sha256'][n] != c['payload_sha256'][n]
            for n in ('src/wcomr/rv0_lpips.py','src/wcomr/rv0_video_reader.py')):
        raise ValueError('Original all93 metric, reader and actual resources required')
    sys.path.insert(0, str(resource/'site'))
    import lpips
    from wcomr.rv0_lpips import score_pair, PROTOCOL
    if (importlib.metadata.version('lpips') != '0.1.4' or Path(lpips.__file__).resolve() != (resource/'site/lpips/__init__.py').resolve()
            or PROTOCOL != identity['protocol']):
        raise ValueError('Fixed offline CPU metric package/protocol origin differs')
    target = a.stage/'result.json'
    if target.exists(): raise ValueError('No repeated per-path CPU result identity')
    before = sha_file(a.project/'reports/budget.json'); started = time.perf_counter()
    result = {'status':'E0_PARTIAL_PATH_AUDIT_AND_SCORING_RUNNING', 'source_revision':a.source_revision,
        'original_card_status_unchanged':'FAILED_TECH', 'original_planned_paths':64,
        'original_saved_complete_paths':14,'original_partial_failure_paths':1,'original_unstarted_paths':49,
        'original_runner_sha256':reg['original_runner_sha256'], 'original_row_verifier_derivation':derivation,
        'numerical_zero_mask_source_proof':masked, 'actual_metric_identity':identity,
        'all64_slots':[], 'pairs':[], 'trajectory_controls':[], 'Native_files':[],
        'budget_before_sha256':before, 'GPU_submissions':0, 'ledger_written':False,
        'clean_speed_claim':False, 'independent_confirmation_claim':False, 'formal_full64_method_acceptance':False}
    def save():
        tmp=target.with_suffix('.tmp'); tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');tmp.replace(target)
    def bound_file(art, directory):
        path=Path(art['path']).resolve()
        if not path.is_relative_to(directory.resolve()) or path.stat().st_size!=art['bytes'] or sha_file(path)!=art['sha256']:
            raise ValueError('Original artifact path, bytes or hash differs')
        return path
    def load_vectors(art, directory):
        path=bound_file(art,directory); x=torch.load(path,map_location='cpu',weights_only=True)
        if (set(x)!= {'guided','final_latent'} or len(x['guided'])!=36
            or any(list(t.shape)!=c['expected_real_shape'] or t.dtype!=torch.float32 or not torch.isfinite(t).all()
                   for t in x['guided']+[x['final_latent']])
            or {k:digest(v) for k,v in x.items()}!=art['tensor_sha256']):
            raise ValueError('Original complete finite vector contents differ')
        return x
    save()
    try:
        for ref in refs.values():
            old_reference = next(v['reference'] for v in old['pairs'] if v['sample_name']==ref['sample_name'])
            if any(old_reference[k] != ref['artifact'][k] for k in ('sha256','bytes')):
                raise ValueError('Reused Native differs from accepted complete32 metric reference')
            path=bound_file(ref['artifact'],a.project/'outputs')
            metadata=probe_video(path)
            with decoded_video(path) as video: count=sum(1 for _ in video)
            if count!=93:raise ValueError('Original Native full93 decode differs')
            result['Native_files'].append({'sample_name':ref['sample_name'],'artifact':ref['artifact'],'decode':metadata})
        for slot in rows:
            entry={k:slot[k] for k in ('strategy','sample_name','method','written_complete')}
            row=slot['row']; directory=out/'diagnostic'/slot['strategy']
            if row is None:entry['path_status']='NOT_WRITTEN'
            elif not slot['written_complete']:
                entry.update(path_status='PARTIAL_FAILED_NOT_ELIGIBLE',original_status=row['status'],original_error=row.get('error'))
            else:
                try:
                    verify(row,slot['strategy'])
                    x=load_vectors(row['vector_artifact'],directory)
                    if [digest(t) for t in x['guided']]!=row['guided_sha256'] or digest(x['final_latent'])!=row['final_latent_sha256']:
                        raise ValueError('Actual all36 guided or final latent differs from row')
                    del x;gc.collect()
                    path=bound_file(row['video_artifact'],directory); metadata=probe_video(path)
                    with decoded_video(path) as video:count=sum(1 for _ in video)
                    if count!=93:raise ValueError('Original saved full93 decode differs')
                    pairing=numerical_pairing(slot,refs[slot['sample_name']],masked)
                    entry.update(path_status='PATH_VALIDATED',pairing=pairing,vector_artifact=row['vector_artifact'],
                        video_artifact=row['video_artifact'],decode=metadata,actions=row['actions'],
                        actual_full_CFG_branches=2*row['actions'].count('DD'),actual_partial_CFG_branches=2*row['actions'].count('PP'),
                        recorded_instrumented_pipeline_seconds=row['instrumented_parent_pipeline_wall_seconds'])
                except (ValueError,KeyError,OSError,RuntimeError) as error:
                    entry.update(path_status='PATH_INVALID',error_type=type(error).__name__,error=str(error))
            result['all64_slots'].append(entry);save()
        bykey={(s['strategy'],s['sample_name'],s['method']):s for s in rows}
        valid={(s['strategy'],s['sample_name'],s['method']) for s in result['all64_slots'] if s['path_status']=='PATH_VALIDATED'}
        for strategy in ('WORKING_P_AGE_KEEP_INTERVAL','WORKING_P_AGE_NONZERO_REBASE'):
            for name in refs:
                for left,right in [('SOURCE_RA','DYNAMIC_NO_P'),('CPD','A_CPD_OFF'),('CPD','REF_CPD')]:
                    keys=[(strategy,name,m) for m in (left,right)]
                    if not all(k in valid for k in keys):continue
                    directory=out/'diagnostic'/strategy
                    x,y=[load_vectors(bykey[k]['row']['vector_artifact'],directory) for k in keys]
                    for v,w in zip(x['guided']+[x['final_latent']],y['guided']+[y['final_latent']]):
                        if right=='REF_CPD':torch.testing.assert_close(v,w,rtol=1e-5,atol=2e-6)
                        elif not torch.equal(v,w):raise ValueError('Original exact full-trajectory control differs')
                    del x,y;gc.collect()
                    result['trajectory_controls'].append({'strategy':strategy,'sample_name':name,'methods':[left,right],
                        'actual36_guided_plus_final_reloaded':True,'comparison':'close_1e-5_2e-6' if right=='REF_CPD' else 'exact_equal'})
        model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in model.parameters():parameter.requires_grad_(False)
        eligible=[s for s in result['all64_slots'] if s['path_status']=='PATH_VALIDATED' and s['pairing']['compatible']]
        if len(eligible)>8:raise ValueError('New E0 original eligible-pair upper scope exceeded')
        for slot in eligible:
            ref=refs[slot['sample_name']]['artifact'];candidate=slot['video_artifact'];tick=time.perf_counter()
            try:
                with decoded_video(ref['path']) as left,decoded_video(candidate['path']) as right:
                    score=score_pair(left,right,model,reference_sha256=ref['sha256'],candidate_sha256=candidate['sha256'])
                result['pairs'].append({'strategy':slot['strategy'],'sample_name':slot['sample_name'],'method':slot['method'],
                    'reference':ref,'candidate':candidate,'score':score,'CPU_wall_seconds':time.perf_counter()-tick})
            except (ValueError,OSError,RuntimeError) as error:
                slot.update(score_error_type=type(error).__name__,score_error=str(error))
            save()
            print(json.dumps({'phase':'score','completed_pairs':len(result['pairs']),'eligible_pairs':len(eligible),'method':slot['method']}),flush=True)
        # Recheck original source and every accepted artifact; no historical failure receipt is modified.
        for s in result['all64_slots']:
            if s['path_status']=='PATH_VALIDATED':
                bound_file(s['vector_artifact'],out/'diagnostic'/s['strategy']);bound_file(s['video_artifact'],out/'diagnostic'/s['strategy'])
        if sha_file(source)!=reg['original_runner_sha256'] or sha_file(supervisor)!=reg['original_supervisor_sha256'] or audit(resource,reg['payload_sha256']['src/wcomr/rv0_lpips.py'])!=identity or sha_file(a.project/'reports/budget.json')!=before:
            raise ValueError('Original source, resources or budget changed during read-only CPU task')
        result.update(status='E0_PARTIAL_PATH_RECOVERY_CPU_COMPLETE_ORIGINAL_FULL64_STILL_FAILED_TECH',
            validated_paths=sum(s['path_status']=='PATH_VALIDATED' for s in result['all64_slots']),
            invalid_paths=sum(s['path_status']=='PATH_INVALID' for s in result['all64_slots']),
            numerical_paired_scores=len(result['pairs']),actual_all93_frame_distances=93*len(result['pairs']),
            strict_original_compatible_pairs=sum(s.get('pairing',{}).get('strict_original_verdict',{}).get('compatible',False) for s in result['all64_slots']),
            missing_prepared_input_paths_retained=[{k:s[k] for k in ('strategy','sample_name','method')} for s in result['all64_slots']
                if s.get('pairing',{}).get('missing_prepare_not_synthesized')],exit_code=0)
    except BaseException as error:
        result.update(status='E0_CPU_TASK_FAILED_RESULTS_AND_ORIGINAL64_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error),exit_code=1)
        raise
    finally:
        result.update(CPU_wall_seconds=time.perf_counter()-started,CUDA_initialized=torch.cuda.is_initialized(),
            budget_after_sha256=sha_file(a.project/'reports/budget.json'));save()
    print(json.dumps({'status':result['status'],'validated_paths':result['validated_paths'],'scored_pairs':len(result['pairs'])}))


if __name__=='__main__':main()
