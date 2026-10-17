"""Independent complete24 raw-receipt, frame-statistic and whole-bill audit."""
import math
from statistics import mean

from .drop1_window24_production_r1 import COUNTS, RUN, validate_contract
from .drop1_window_original_controls_r1 import expected_plans
from .drop1_window24_cpu_acceptance_r1 import validate_bundle
from .drop1_window24_execution_envelope_r1 import validate_authority
from .frozen_shared_acceptance_r1 import original_alive, digest
from .gpu_budget_pool_v2 import BudgetPool

METHODS = ('S26-C', 'S25-C', 'S25-A1', 'S25-A3')
CONTRASTS = (('S25-A3','S25-A1'), ('S25-A3','S25-C'), ('S25-A3','S26-C'),
             ('S25-C','S26-C'), ('S25-A1','S25-C'), ('S25-A1','S26-C'))


def original_matrix(scenes):
    rows=[]
    for r in (1,2):
        for m in METHODS if r==1 else METHODS[::-1]:
            rows.append(dict(id=f'warm_{r}_{m}',scene=scenes[0],method=m,section='WARMUP',round=r))
    for i,s in enumerate(scenes):
        for m in METHODS if i%2==0 else METHODS[::-1]:
            rows.append(dict(id=f'timed_{i}_{m}',scene=s,method=m,section='TIMED',round=1))
    return rows


def _financial(v, launch, config):
    errors=[]
    def check(ok,label):
        if not ok: errors.append(label)
    bill=v.get('billing');pool=v['pool'];job=pool['jobs'].get(RUN)
    if not bill or not job:
        return dict(actual_GPUh=None,finance_accepted=False,errors=['Missing original bill or settlement'])
    actual=bill.get('actual_GPUh')
    check(isinstance(actual,(int,float)) and math.isfinite(actual) and actual>=0,'Finite actual charge')
    check(all(bill.get(k)==launch[k] for k in ('source_revision','launch_id','gpu_uuid','run_id','scope_counts')),'Original whole bill identity')
    check(math.isclose(bill['wall_seconds']/3600,actual or 0,rel_tol=1e-12,abs_tol=1e-12),'Actual whole wall/3600')
    check(job.get('status')=='SETTLED' and job.get('actual_GPUh')==actual
          and job.get('billing_sha256')==v['billing_sha256'],'Original additive settlement')
    check(v['supervisor'].get('billing_sha256')==v['billing_sha256'],'Original supervisor bill bytes')
    check(all(job.get(k)==launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','scope_counts')),'Settled exact full24 scope')
    check(all(job.get(k)==launch[k] for k in ('production_CPU_sha256','authorization_sha256','bound_input_fingerprint')),'Billed original CPU/authority/input binding')
    check(pool['cap_gpu_hours']>=226 and pool['origin_used_gpu_hours']==79.99637737158223,'Cumulative window retained')
    check(all(math.isclose(pool[k],n,rel_tol=1e-12,abs_tol=1e-12) for k,n in BudgetPool.accounting(pool).items()),'Complete pool totals')
    own={launch['supervisor_pid'],v.get('supervisor',{}).get('child_pid')}
    apps=[s.split(',') for s in v.get('compute_apps','').splitlines() if s.strip()]
    check(not v.get('GPU_telemetry_error') and v.get('own_GPU','').split(',')[0].strip()==launch['gpu_uuid'],'Actual original UUID telemetry')
    check(not any(s[0].strip()==launch['gpu_uuid'] and int(s[1]) in own for s in apps),'Original compute PIDs released')
    later=False
    for key,other in pool['jobs'].items():
        if key==RUN or other['status']!='RESERVED_OR_RUNNING' or other['gpu_uuid']!=launch['gpu_uuid']:continue
        identity=v.get('other_reservation_identities',{}).get(key)
        later |= original_alive(dict(pid=other['supervisor_pid'],start_ticks=other['supervisor_start_ticks']),identity)
    check(v.get('own_UUID_lock_exists') is True and (v.get('own_UUID_lock_free') is True or later),'Original lease released or documented subsequent owner')
    check(bill['billed_limit_GPUh']==config['billed_limit_GPUh']==job['billed_limit_GPUh'],'Original complete billed limit')
    respected=actual is not None and actual<=config['billed_limit_GPUh']
    if config['billed_limit_GPUh']>=12:check(job.get('kind')=='V2_SPECIFIC_WHOLE_CARD_APPROVAL','Specifically approved complete >=12 card retained')
    check(respected or pool.get('budget_overrun_recorded') is True,'Any actual overrun preserved')
    return dict(actual_GPUh=actual,finance_accepted=not errors,billed_limit_respected=respected,errors=errors)


def accept(v, launch):
    if v.get('launch')!=launch or launch['run_id']!=RUN or v.get('mode')!='terminal':
        raise ValueError('Original whole24 terminal capture required')
    if v['observed_unix']<launch['next_check_not_before_unix']:
        raise ValueError('Original ETA applies to final acceptance')
    if v.get('status')=='WINDOW24_ORIGINAL_STILL_RUNNING_TECHNICAL_ONLY':
        return dict(status='WINDOW24_ORIGINAL_STILL_RUNNING_REESTIMATE_ONCE',scientific_accepted=False,
                    registered_paths=24,GPU_submissions=0)
    if (v.get('status')!='WINDOW24_ORIGINAL_ONCE_CAPTURE'
            or v['registration_sha256']!=launch['registration_sha256']
            or v['registration']['source_revision']!=launch['source_revision']
            or not v['registration']['payload_sha256'] or not v['registration']['runtime_source_sha256']
            or v['payload_actual_sha256']!=v['registration']['payload_sha256']
            or v['runtime_actual_sha256']!=v['registration']['runtime_source_sha256']):
        raise ValueError('Complete original source/runtime and exact registration required')
    sup=v.get('supervisor',{});processes=v['original_processes']
    if any(original_alive(x,processes.get(k)) for k,x in (
            ('supervisor',launch['supervisor_identity']),('post',launch.get('post_watcher_identity')),('runner',sup.get('child_identity')))):
        return dict(status='WINDOW24_ORIGINAL_STILL_RUNNING_REESTIMATE_ONCE',scientific_accepted=False,registered_paths=24,GPU_submissions=0)
    required=('config','production_CPU','CPU_bundle','CPU_independent','CPU_launch','authorization','final','post_exit','runner','supervisor','old_controls','baseline')
    if not all(v.get(k) for k in required):
        return dict(status='WINDOW24_ORIGINAL_TERMINAL_MISSING_OR_FAILED_RETAINED',scientific_accepted=False,
                    registered_paths=24,actual_GPUh=v.get('billing',{}).get('actual_GPUh'),GPU_submissions=0)
    c=v['config'];validate_contract(c)
    if launch['scope_counts']!=COUNTS:raise ValueError('The original full24 dispatch scope is immutable')
    if c['plans']!={k:list(x) for k,x in expected_plans().items()}:
        raise ValueError('Independent frozen four plans differ')
    if v['config_sha256']!=launch['config_sha256'] or v['config_sha256']!=v['registration']['payload_sha256'].get(
            'configs/wc_drop1_correction_window_full24_production_r1_20261018.json'):
        raise ValueError('Original selected config SHA required')
    validate_bundle(v['CPU_bundle'],v['production_CPU'],c,v['registration'],
        registration_sha256=v['registration_sha256'],config_sha256=v['config_sha256'],proof_sha256=v['production_CPU_sha256'])
    validate_authority(c,v['registration'],v['production_CPU'],v['CPU_independent'],v['authorization'],
        source_revision=launch['source_revision'],gpu_uuid=launch['gpu_uuid'],registration_sha256=v['registration_sha256'],
        config_sha256=v['config_sha256'],proof_sha256=v['production_CPU_sha256'],accepted_sha256=v['CPU_independent_sha256'])
    if v['authorization_sha256']!=launch['authorization_sha256'] or v['CPU_independent_sha256']!=launch['independent_CPU_acceptance_sha256']:
        raise ValueError('Exact original dispatch authority and independent CPU file required')
    if v['CPU_launch']['identity']!=v['CPU_independent']['original_CPU_identity'] or v['CPU_launch']['source_revision']!=launch['source_revision']:
        raise ValueError('Independent actual CPU acceptance belongs to the original CPU handle')
    errors=[]
    def check(ok,label):
        if not ok:errors.append(label)
    final=v['final'];runner=v['runner'];post=v['post_exit'];scenes=[r['name'] for r in c['requests']]
    plan=original_matrix(scenes);runs=runner.get('runs',[]);rows=final.get('rows',[])
    check(sup.get('source_revision')==runner.get('source_revision')==launch['source_revision'],'Original GPU source')
    check(sup.get('config_sha256')==runner.get('config_sha256')==launch['config_sha256'],'Original GPU config')
    check(sup.get('child_exit_code')==0 and post.get('exit_code')==0,'Original GPU/post successful exit')
    check(sup.get('status')=='WINDOW24_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT' and sup.get('runner_sha256')==v['runner_sha256'],'Original supervisor runner bytes')
    check(post.get('status')=='WINDOW24_POST_CPU_TERMINAL' and post.get('original_supervisor')==
          {k:launch['supervisor_identity'][k] for k in ('pid','start_ticks')},'Original supervised CPU post handle')
    check(post.get('source_revision')==launch['source_revision'] and post.get('config_sha256')==launch['config_sha256'],'Original post source/config')
    check(post.get('final_result_sha256')==v['final_sha256'],'Original post final bytes')
    check(final.get('source_revision')==launch['source_revision'] and final.get('scope_counts')==COUNTS,'Original full24 post source/scope')
    check(final.get('GPU_supervisor')==sup and runner.get('matrix')==plan,'Original supervisor and complete GPU matrix')
    check(sup.get('scope_counts')==runner.get('scope_counts')==COUNTS,'Original GPU full24 scope')
    check(final.get('status')=='WINDOW24_FULL16_SCIENCE_ALL24_AUDITED_93FRAME_SCORED','Complete original raw/post status')
    check(len(runs)==len(rows)==24,'All original24 GPU and post positions')
    if len({r['id'] for r in runs})!=len(runs) or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('Duplicate original path ID')
    expected_ids=[r['id'] for r in plan]
    check([r['id'] for r in rows]==expected_ids and [r['id'] for r in runs]==expected_ids,'Original order and full denominator')
    originals={r['id']:r for r in runs};lookup={r['id']:r for r in rows}
    native={r['scene']:r['video_artifact']['sha256'] for r in v['baseline']['rows'] if r['method']=='NATIVE'}
    check(v['baseline_sha256']==c['references']['baseline']['sha256'] and v['old_controls_sha256']==c['references']['old_controls']['sha256'],'Original Native/control bindings')
    valid={};outcomes={};references={}
    for planned in plan:
        row=lookup.get(planned['id']);status=row.get('status') if row else 'NOT_REACHED_FULL_SCOPE_RETAINED'
        outcomes[status]=outcomes.get(status,0)+1
        if row is None:continue
        check(all(row.get(k)==x for k,x in planned.items()),planned['id']+' original metadata')
        before=originals.get(row['id'],{})
        check(all(row.get(k)==x for k,x in before.items()),row['id']+' original GPU values retained')
        if status not in ('COMPLETE','VIDEO_REJECTED'):continue
        expected=expected_plans()[row['method']];label=row['id']
        check(row['semantic_plan']==expected and row['actions']==['DD' if a=='D' else 'CC' for a in expected],label+' exact mask/actions')
        check(row['solver_steps']==row['guided_pairs']==36 and len(row['source_history'])==len(row['A_history'])==36,label+' full36')
        check(row['online_teacher_calls']==row['in_timing_hashes']==row['research_checkpoints']==0,label+' no teacher/hash')
        check(row['in_timing_guided_copies']==(36 if row['section']=='WARMUP' else 0),label+' audit boundary')
        check(row.get('audit') is (row['section']=='WARMUP'),label+' actual audit mode')
        check(row['core_seconds']>0 and math.isfinite(row['core_seconds']) and row['write_deferred_after_main_timer'],label+' timing boundary')
        if status=='COMPLETE':
            check(row.get('endpoint_audit')=='PASS' and row['decoded_video']['frames']==93
                  and row['decoded_video']['probe']['HWC']==[432,768,3]
                  and digest(row['decoded_video']['RGB_sha256']) and digest(row['final_latent_sha256']),label+' complete93 raw endpoint')
            if row['section']=='WARMUP':
                check(row.get('warm_guided_outputs')==36 and digest(row.get('warm_guided_tree_sha256')),label+' complete36 warm tensors')
        for action,h in zip(expected,row['source_history']):
            a=h['A_readout']
            check(a['readout_action']==action and not h['teacher_calls'] and not a['teacher_calls'] and not a['extra_deep_blocks']
                  and not h['P_updates_true_D_or_zero_risk_RA_anchor'],label+' actual readout')
            if action!='D':check(h['true_D_before']==h['true_D_after'],label+' trusted D history')
            if action=='A':check(a['shared_alpha']==1 and a['extra_heads']==2,label+' beta1 correction')
            if action=='C':check(a['shared_alpha']==a['extra_heads']==0,label+' plain reuse')
        if row['section']!='TIMED' or status!='COMPLETE' or row.get('endpoint_audit')!='PASS' or 'LPIPS' not in row:continue
        score=row['LPIPS'];dist=score['frame_distances']
        if (len(dist)!=93 or score['frames']!=93 or len(score['pts'])!=93
                or row['decoded_video']['frames']!=93 or row['decoded_video']['probe']['HWC']!=[432,768,3]
                or any(not math.isfinite(x) or x<0 for x in dist)
                or not math.isclose(mean(dist),score['mean_LPIPS'],rel_tol=0,abs_tol=1e-12)
                or score['reference_sha256']!=native.get(row['scene'])):
            errors.append(label+' all93 compatible finite frame scores');continue
        identity=(score['reference_sha256'],score['pts'])
        if row['scene'] in references and references[row['scene']]!=identity:
            errors.append(label+' common Native/PTS');continue
        references[row['scene']]=identity
        counts=dict(DD=expected.count('D'),PP=0,C_plain=expected.count('C'),A=expected.count('A'),C_or_A_after_P=0)
        check(row['counts']==counts,label+' actual quotas')
        valid[(row['scene'],row['method'])]=dict(loss=mean(dist),frames=dist,seconds=row['core_seconds'],counts=counts)
    check(len(valid)==16,'All16 full93 formal endpoints')
    for field,count in [('warm_guided_controls',4),('original_baseline_controls',12),('warm_common_prefix_controls',2)]:
        values=final.get(field,[]);check(len(values)==count and all(x['status'].startswith('PASS') for x in values),field+' complete original controls')
    guides=final.get('warm_guided_controls',[])
    check({x['method'] for x in guides}==set(METHODS) and all(x.get('outputs_per_arm')==36 for x in guides),'Four distinct all36 guided controls')
    prefix=final.get('warm_common_prefix_controls',[])
    check({x['round'] for x in prefix}=={1,2} and all(x.get('compared_outputs')==21 for x in prefix),'Both all21 common prefixes')
    controls=final.get('original_baseline_controls',[])
    check({(x['scene'],x['method']) for x in controls}=={(s,m) for s in scenes for m in METHODS[:3]},'All distinct12 original endpoint controls')
    check(len(v['old_controls']['rows'])==12 and {(x['scene'],x['window_method']) for x in v['old_controls']['rows']}==
          {(s,m) for s in scenes for m in METHODS[:3]},'All original12 bound endpoints')
    for binding in v['old_controls']['rows']:
        old=binding['original_row'];row=next((r for r in rows if r['section']=='TIMED' and r['scene']==binding['scene'] and r['method']==binding['window_method']),None)
        if row and row.get('endpoint_audit')=='PASS':
            check(all(row[k]==old[k] for k in ('final_latent_sha256','actions','A_history'))
                  and row['decoded_video']['RGB_sha256']==old['decoded_video']['RGB_sha256'],'Original old12 raw endpoint identity')
    warm=final.get('warm_repeat_controls',[])
    check(len(warm)==4 and all(x['warm_repeats_outputs_actions_RGB_equal'] and x['same_scene_formal_repeat_equal'] for x in warm),'Four warm/formal repeats')
    for method in METHODS:
        pairs=[lookup.get(f'warm_{r}_{method}') for r in (1,2)]
        formal=next((r for r in rows if r['section']=='TIMED' and r['scene']==scenes[0] and r['method']==method),None)
        if all(p and p.get('endpoint_audit')=='PASS' for p in pairs) and formal and formal.get('endpoint_audit')=='PASS':
            check(all(pairs[0][k]==pairs[1][k] for k in ('final_latent_sha256','actions','warm_guided_tree_sha256'))
                  and pairs[0]['decoded_video']['RGB_sha256']==pairs[1]['decoded_video']['RGB_sha256'],'Warm actual repeat hashes')
            check(all(pairs[0][k]==formal[k] for k in ('final_latent_sha256','actions'))
                  and pairs[0]['decoded_video']['RGB_sha256']==formal['decoded_video']['RGB_sha256'],'Warm/formal actual repeat hashes')
    memory=final.get('request_memory_records',[])
    check(len(memory)==24 and memory==runner.get('request_memory_records') and [r['id'] for r in memory]==expected_ids
          and all(r['owners_alive_after']==0 for r in memory),'All request owners released')
    contrasts=[]
    for candidate,baseline in CONTRASTS:
        paired=[]
        for scene in scenes:
            a,b=valid.get((scene,candidate)),valid.get((scene,baseline))
            if a is None or b is None:paired.append(dict(scene=scene,status='MISSING_OR_REJECTED_RETAINED'));continue
            paired.append(dict(scene=scene,status='SCORED',candidate_LPIPS=a['loss'],baseline_LPIPS=b['loss'],
                absolute_change=a['loss']-b['loss'],relative_change_percent=100*(a['loss']/b['loss']-1) if b['loss'] else None,
                candidate_seconds=a['seconds'],baseline_seconds=b['seconds'],speedup_baseline_over_candidate=b['seconds']/a['seconds'],
                improved_frames=sum(x<y for x,y in zip(a['frames'],b['frames'])),worsened_frames=sum(x>y for x,y in zip(a['frames'],b['frames'])),
                candidate_counts=a['counts'],baseline_counts=b['counts']))
        done=[r for r in paired if r['status']=='SCORED'];complete=len(done)==4
        contrasts.append(dict(candidate=candidate,baseline=baseline,denominator=4,scored_scenes=len(done),scene_rows=paired,
            complete_four_scene_relative_mean_change_percent=100*(mean(r['candidate_LPIPS'] for r in done)/mean(r['baseline_LPIPS'] for r in done)-1)
                if complete and mean(r['baseline_LPIPS'] for r in done)>0 else None))
    finance=_financial(v,launch,c)
    full_protocol=not errors and finance['finance_accepted'] and finance['billed_limit_respected']
    return dict(status='WINDOW24_FULL24_ALL16_INDEPENDENTLY_ACCEPTED' if full_protocol else 'WINDOW24_FULL_SCOPE_ISSUES_OR_REJECTIONS_RETAINED',
        scientific_accepted=not errors,full_protocol_accepted=full_protocol,
        errors=errors,finance=finance,registered_paths=24,formal_denominator=16,scored_scientific_paths=len(valid),outcomes=outcomes,
        contrasts=contrasts,actual_GPUh=finance['actual_GPUh'],independent_new_input_confirmation=False,
        stable_repeated_clean_speed_claim=False,per_scene_winner_splicing=False,GPU_submissions=0,ledger_written=False)
