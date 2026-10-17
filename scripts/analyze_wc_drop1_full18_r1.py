#!/usr/bin/env python3
"""Offline independent whole18 acceptance and per-scene three contrasts."""
import argparse,collections,gzip,hashlib,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG='configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json'
METHODS=['S26-C','S25-C','S25-A']
def analyze(v,c):
    launch=v['launch'];errors=[]
    def check(ok,label):
        if not ok:errors.append(label)
    check(v['mode']=='terminal','Terminal raw capture required')
    check(all(v['payload_verified'].values()) and all(v['runtime_verified'].values()),'All immutable payload/runtime sources')
    check(v['registration_sha256']==launch['registration_sha256'],'Original registration')
    sup,runner,post=v.get('supervisor',{}),v.get('runner',{}),v.get('post_exit',{})
    check(sup.get('source_revision')==runner.get('source_revision')==launch['source_revision'],'Original source identities')
    check(sup.get('child_exit_code')==0 and post.get('exit_code')==0,'Original GPU and CPU terminal success')
    check(all(q['state'] in (None,'Z','X') for q in v['original_processes'].values()),'Original owned processes terminal')
    check(v['own_UUID_lock_free'],'Own UUID lock released')
    own_apps=[s for s in v['compute_apps'].splitlines() if s.split(',')[0].strip()==launch['gpu_uuid']]
    check(not own_apps,'Own UUID compute released')
    bill=v.get('billing',{});job=v['pool']['jobs'].get(launch['run_id'],{})
    check(bill.get('run_id')==job.get('job_id')==launch['run_id'],'Original billed job')
    actual=bill.get('actual_GPUh')
    check(actual is not None and math.isclose(actual,bill.get('wall_seconds',-1)/3600,abs_tol=1e-12),'Actual whole-wall charge')
    check(job.get('status')=='SETTLED' and math.isclose(job.get('actual_GPUh',-1),actual or -2,abs_tol=1e-12),'Additive settled original task')
    check(v['pool']['cap_gpu_hours']==226,'Current cumulative cap226')
    final=v.get('final',{});rows=final.get('rows',[]);runs=runner.get('runs',[])
    check(len(rows)==len(runs)==18,'Original all18 positions')
    ids=[q['id'] for q in rows];check(len(ids)==len(set(ids)),'Unique original path IDs')
    check(final.get('scope_counts')==c['scope_counts']==launch['scope_counts'],'Complete bound scope')
    check(final.get('status')=='DROP1_FULL12_SCIENCE_ALL18_AUDITED_93FRAME_SCORED','All applicable raw/scoring controls')
    for q in final.get('original_baseline_controls',[]):check(q['status'].startswith('PASS'),'Original front26 control '+q['scene'])
    check(len(final.get('original_baseline_controls',[]))==4,'All four original front26 controls')
    check(len(final.get('warm_guided_controls',[]))==3 and all(q['status'].startswith('PASS') and q['outputs_per_arm']==36 for q in final.get('warm_guided_controls',[])),'Three all36 guided warm controls')
    check(len(final.get('warm_repeat_controls',[]))==3 and all(q['warm_repeats_outputs_actions_RGB_equal'] and q['same_scene_formal_repeat_equal'] for q in final.get('warm_repeat_controls',[])),'Every warm/formal endpoint RGB repeat')
    check(len(final.get('request_memory_records',[]))==18 and all(q['owners_alive_after']==0 for q in final.get('request_memory_records',[])),'All18 request owners released')
    formal={};outcomes=collections.Counter()
    for row in rows:
        outcomes[row['status']]+=1
        if row['status']!='COMPLETE':continue
        plan=c['plans'][row['method']]
        check(row['semantic_plan']==plan and row['actions']==['DD' if x=='D' else 'CC' for x in plan],row['id']+' exact plan')
        check(row['solver_steps']==row['guided_pairs']==36 and len(row['source_history'])==36,row['id']+' all36 updates')
        check(row['online_teacher_calls']==row['in_timing_hashes']==row['research_checkpoints']==0,row['id']+' no extra teachers/hash')
        check(row['in_timing_guided_copies']==(36 if row['section']=='WARMUP' else 0),row['id']+' audit boundary')
        check(row.get('endpoint_audit')=='PASS' and row['decoded_video']['frames']==93,row['id']+' all93 RGB')
        check(row['core_seconds']>0 and row['write_deferred_after_main_timer'],row['id']+' main timing boundary')
        for step,(a,h) in enumerate(zip(plan,row['source_history']),1):
            rr=h['A_readout'];check(rr['readout_action']==a and not h['teacher_calls'] and not rr['teacher_calls'],row['id']+' actual readout')
            if a!='D':check(h['true_D_before']==h['true_D_after'],row['id']+' trustedD unchanged')
            if a=='A':check(step==21 and rr['shared_alpha']==1,row['id']+' A21 alpha1')
            if a=='C':check(rr['shared_alpha']==rr['extra_heads']==0,row['id']+' plainC')
        if row['section']=='TIMED':
            score=row.get('LPIPS');check(bool(score),row['id']+' compatible reference')
            if not score:continue
            frames=score['frame_distances'];check(len(frames)==score['frames']==93,row['id']+' all93 scores')
            check(all(math.isfinite(t) and t>=0 for t in frames),row['id']+' finite LPIPS')
            quality=statistics.mean(frames);check(math.isclose(quality,score['mean_LPIPS'],abs_tol=1e-12),row['id']+' independent mean')
            formal[(row['scene'],row['method'])]=dict(LPIPS=quality,seconds=row['core_seconds'],counts=row['counts'],frames=frames)
    scenes=[q['name'] for q in c['requests']];contrasts=[]
    for candidate,baseline in [('S25-A','S25-C'),('S25-A','S26-C'),('S25-C','S26-C')]:
        pairs=[]
        for scene in scenes:
            a,b=formal.get((scene,candidate)),formal.get((scene,baseline))
            if not a or not b:pairs.append(dict(scene=scene,status='MISSING_OR_REJECTED_RETAINED'));continue
            pairs.append(dict(scene=scene,status='SCORED',candidate_LPIPS=a['LPIPS'],baseline_LPIPS=b['LPIPS'],absolute_change=a['LPIPS']-b['LPIPS'],relative_change_percent=100*(a['LPIPS']/b['LPIPS']-1),candidate_seconds=a['seconds'],baseline_seconds=b['seconds'],speedup_baseline_over_candidate=b['seconds']/a['seconds'],improved_frames=sum(x<y for x,y in zip(a['frames'],b['frames'])),worsened_frames=sum(x>y for x,y in zip(a['frames'],b['frames'])),candidate_counts=a['counts'],baseline_counts=b['counts']))
        valid=[p for p in pairs if p['status']=='SCORED'];complete=len(valid)==4
        contrasts.append(dict(candidate=candidate,baseline=baseline,denominator=4,scored_scenes=len(valid),per_scene=pairs,
            complete_four_scene_absolute_LPIPS_change=statistics.mean(p['absolute_change'] for p in valid) if complete else None,
            complete_four_scene_relative_mean_change_percent=100*(statistics.mean(p['candidate_LPIPS'] for p in valid)/statistics.mean(p['baseline_LPIPS'] for p in valid)-1) if complete else None))
    return dict(status='DROP1_WHOLE18_INDEPENDENT_RAW_FRAME_COST_ACCEPTED' if not errors else 'DROP1_WHOLE18_GAPS_OR_FAILURES_RETAINED',accepted=not errors,errors=errors,outcomes=dict(outcomes),scope_counts=c['scope_counts'],scientific_slots=12,scored_scientific_paths=len(formal),contrasts=contrasts,actual_GPUh=actual,cap226=True,GPU_submissions=0,ledger_written=False,independent_new_input_confirmation=False,stable_repeated_clean_speed_claim=False,per_scene_winner_splicing=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    v=json.loads(gzip.decompress(a.capture.read_bytes()));c=json.loads((ROOT/CONFIG).read_text())
    assert hashlib.sha256((ROOT/CONFIG).read_bytes()).hexdigest()==v['launch']['config_sha256']
    result=analyze(v,c);result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='contrasts'}))
    raise SystemExit(0 if result['accepted'] else 1)
if __name__=='__main__':main()
