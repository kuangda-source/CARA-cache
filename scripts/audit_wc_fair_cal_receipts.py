#!/usr/bin/env python3
"""Independent Native/short Native/tuned WC/stage fourteen-video audit, no Torch."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import subprocess

spec=importlib.util.spec_from_file_location('online_primitives',Path(__file__).with_name('audit_wc_online_stage_receipts.py'))
online=importlib.util.module_from_spec(spec);spec.loader.exec_module(online)
base=online.base
POINTS=[dict(name=n,mode=m,requested_steps=s,threshold=t) for n,m,s,t in [
    ('native35','native',35,None),('native23','native',23,None),
    ('wc004','worldcache',35,.04),('wc006','worldcache',35,.06),
    ('wc008','worldcache',35,.08),('stage_every1','stage',35,.06)]]
NATIVE='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'
WC='cosmos_predict2._src.predict2.inference.worldcache_utils.worldcache_mini_train_dit_forward'


def binding(receipt):
    assert receipt['run_card']=='WC-FAIR-CAL-R1-20261004-A'
    c=receipt['scope']
    assert c['run_id']=='wc-fair-cal-r1' and c['sample_names']==online.SAMPLES
    assert c['expected_WC_sha256']==online.D_SHA
    assert c['workpoints']==receipt['workpoints']==POINTS
    assert receipt['planned_total_phases']==receipt['planned_output_files']==14
    assert receipt['role']=='TWO_EXPOSED_CAL_NATIVE_FEWER_STEP_TUNED_WC_STAGE_FAIR_COMPARISON_NOT_CONF'
    p=receipt['stage_policy']
    assert p['sparse_layers']==online.FULL and (p['every'],p['first_solver_step'],p['last_solver_step'])==(1,23,27)
    contexts=receipt['reference_contexts']
    assert len(contexts)==2 and contexts[0][1]==contexts[1][1]
    assert [v[0] for v in contexts]==['wc-fair-cal-r1:'+s for s in online.SAMPLES]
    assert [v[2] for v in contexts]==[
        '3f7f757246c121fc1da737dfbb4dfbd24de751a2fb11cb8735135826ab6f0c7e',
        '762b295ec6a4d74f8ba16034abf34d64956614733eb909fbd7dbae4abebeefc4']
    origins=receipt['native_forward_sources']
    assert NATIVE in origins and len(origins)==2
    for origin in origins.values():
        assert origin['sha256']==c['upstream_source_sha256'][origin['source']]


def phase_structure(p, point):
    assert p['workpoint']==point and p['status']=='COMPLETE_FULL93_WORKPOINT_NOT_QUALITY_OR_SPEED_ACCEPTANCE'
    steps=point['requested_steps']+1;calls=steps*2;native=point['mode']=='native'
    assert p['solver_steps']==steps and p['CFG_calls']==calls and p['prepare_calls']==1
    trace=p['trace'];assert len(trace)==calls and [v['call'] for v in trace]==list(range(1,calls+1))
    full=sum(v['deep_executed'] for v in trace)
    assert p['block_counts']=={'denoiser_calls':calls,'full_calls':full,'skipped_deep_calls':calls-full}
    assert p['worldcache_enabled']==(not native)
    assert p['base_forward_identity']==(NATIVE if native else WC)
    sampling=p['sampling']
    assert sampling['requested_steps']==point['requested_steps'] and sampling['actual_schedule_steps']==steps
    assert len(sampling['timesteps'])==steps and all(math.isfinite(v) for v in sampling['timesteps'])
    assert sampling['use_kerras_sigma'] is True and p['substage_cuda_isolated'] is False
    if native:
        assert full==calls and sampling['worldcache_horizon'] is None
        assert 'refresh_provenance' not in p
        assert all(v['cache_counter_before']==0 for v in trace)
    else:
        assert sampling['worldcache_horizon']==70
        assert [v['cache_counter_before'] for v in trace]==list(range(70))+[0,1]
        assert all(v['deep_executed'] for v in trace[-2:])
        assert ('refresh_provenance' in p)==(point['mode']=='stage')
    assert math.isfinite(p['pipeline_wall_seconds']) and p['pipeline_wall_seconds']>0
    assert set(p['substage_host_wall'])=={'prepare','sample','decode','video_guardrail','write'}
    assert all(v['calls']==1 and math.isfinite(v['seconds']) and v['seconds']>0
               for v in p['substage_host_wall'].values())
    events=p['pipeline_events'];assert [v['stage'] for v in events]==base.STAGES
    assert events[2]['value']['shape']==[1,3,93,432,768]
    assert events[3]['value']['shape']==events[4]['value']['shape']==[93,432,768,3]
    assert events[5]['value']['shape']==[3,93,432,768]
    assert p['flags_before']==p['flags_after']
    return full


def phase_audit(p,path,context,point):
    full=phase_structure(p,point)
    artifact,=p['artifacts']
    assert path.name==artifact['name'] and path.stat().st_size==artifact['bytes']
    assert base.sha(path)==artifact['sha256']
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
        '-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames',
        '-of','json',str(path)],text=True,timeout=90))['streams'][0]
    assert (probe['width'],probe['height'],int(probe['nb_read_frames']))==(768,432,93)
    n,d=map(int,probe['r_frame_rate'].split('/'));assert n/d==16
    decoded=subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(path),
        '-map','0:v:0','-f','null','-'],capture_output=True,text=True,timeout=90)
    assert decoded.returncode==0 and not decoded.stderr.strip(),decoded.stderr
    f={'path':str(path),'sha256':artifact['sha256'],'bytes':artifact['bytes'],'ffprobe':probe,
       'full93_decode':True,'index':p['index'],'variant':point['name'],'workpoint':point,
       'pipeline_wall_seconds':p['pipeline_wall_seconds'],'solver_steps':p['solver_steps'],
       'CFG_calls':p['CFG_calls'],'deep_CFG_calls':full,'performance_sample':True}
    if point['mode']=='stage':
        f['provenance']=online.stage_provenance(p,context,sparse_allowed=True)
    return f


def control(receipt,directory):
    binding(receipt)
    result=base.dense_control(receipt,directory)
    phases=receipt['dense_control']['phases']
    result['files'][1]['provenance']=online.stage_provenance(phases[1],receipt['dense_control']['context'],sparse_allowed=False)
    assert result['files'][0]['sha256']==result['files'][1]['sha256']==online.D_SHA[online.SAMPLES[0]]
    result.update(status='FAIR_CAL_DD_TWO_OUTPUT_AUDIT_PASS_FOURTEEN_CARD_PENDING',planned_phases=14,planned_outputs=14)
    return result


def audit(receipt,directory):
    binding(receipt)
    if receipt['status']!='FOURTEEN_COMPLETE_FAIR_OUTPUTS_REQUIRE_AUDIT_NOT_FRONTIER_ACCEPTANCE':
        return {'status':'INCOMPLETE_FAIR_FOURTEEN_CARD_NOT_ACCEPTED','planned_outputs':14,
            'runner_status':receipt['status'],'error':receipt.get('error'),
            'present_files':[str(p) for p in directory.rglob('*.mp4')],'files':[],
            'quality_acceptance':False}
    result=control(receipt,directory);groups=[]
    assert receipt['measurements']['status']=='TWELVE_FAIR_CAL_OUTPUTS_REQUIRE_INDEPENDENT_AUDIT_METRICS'
    requests=receipt['measurements']['requests'];assert [q['sample_name'] for q in requests]==online.SAMPLES
    for q,context in zip(requests,receipt['reference_contexts']):
        assert q['status']=='SIX_COMPLETE_NATIVE_FEWER_STEP_TUNED_WC_STAGE_OUTPUTS_REQUIRE_AUDIT_METRICS'
        assert q['planned_phases']==q['planned_outputs']==len(q['phases'])==6
        assert q['workpoints']==POINTS and q['context']==context and q['native_forward_identity']==NATIVE
        assert q['fresh_prepare_per_phase'] and q['performance_sample'] and not q['checkpoint_restore']
        assert not q['diagnostic_observers'] and not q['per_forward_tensor_diagnostic_hashes']
        assert q['refresh_ledger_and_kernel_checks_counted_in_wall'] and q['timing_wrappers_CUDA_boundary_sync_only']
        files=[]
        for i,(p,point) in enumerate(zip(q['phases'],POINTS)):
            assert p['index']==i and 'observers' not in p
            path=directory/'measurement'/q['sample_name']/(str(i).zfill(3)+'_'+point['name'])/(q['sample_name']+'.mp4')
            if i!=1:
                assert p['sampling']['timesteps']==q['phases'][0]['sampling']['timesteps']
            files.append(phase_audit(p,path,context,point))
        assert files[3]['sha256']==online.D_SHA[q['sample_name']]
        assert q['phases'][5]['refresh_provenance']['selection_policy']==receipt['stage_policy']
        native=files[0]['pipeline_wall_seconds']
        groups.append({'sample_name':q['sample_name'],'files':files,'all_runs_included':True,
            'single_ordered_run_not_replicated_speed':True,
            'descriptive_timings':[{'variant':f['variant'],'seconds':f['pipeline_wall_seconds'],
                'Native35_over_variant':native/f['pipeline_wall_seconds'],
                'wall_reduction_fraction':1-f['pipeline_wall_seconds']/native} for f in files]})
        result['files'].extend(files)
    assert len(result['files'])==len(list(directory.rglob('*.mp4')))==14
    result.update(status='FOURTEEN_FAIR_CAL_NATIVE_WC_STAGE_VIDEO_AUDIT_PASS_NOT_QUALITY',
        measurement_outputs=12,measurement_groups=groups,metric_reference='native35',
        planned_native_relative_pairs=10,independent_confirmation=False,
        native_GPU_uninstrumented_parity=False,deployment_speed_claim=False,
        limits=['Two exposed CAL, all six configurations, one ordered run per configuration.',
            'Native uses the pinned original class method; no separate uninstrumented GPU parity run.',
            'D/D diagnostic timing excluded; complete measurement walls include necessary stage overhead.',
            'Encoded Native-relative fidelity is not semantic/physics or independent CONF acceptance.'])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('directory','receipt','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--control-only',action='store_true');a=p.parse_args()
    r=json.loads(a.receipt.read_text());result=(control if a.control_only else audit)(r,a.directory)
    result.update(receipt_sha256=base.sha(a.receipt),audit_code_sha256=base.sha(Path(__file__)),
        reused_primitives_sha256={n:base.sha(Path(__file__).with_name(n)) for n in
            ['audit_wc_online_stage_receipts.py','audit_wc_light_output_receipts.py']})
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'files':len(result['files']),'quality_acceptance':False}))
