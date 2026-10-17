"""Independent original full960 journal/decoder/source/bill acceptance.

No model, video, GPU, SSH or original file is opened here. Complete attempt,
valid score evidence, whole quality scope and actual billing are separate.
"""
import base64
from collections import Counter
from fractions import Fraction
import hashlib
import gzip
import json
import math
from pathlib import PurePosixPath

from .automatic_quality_batch_r1 import initial_rows, reconstruct
from .automatic_quality_models_r1 import ROLES, WEIGHTS, SELF_REF
from .automatic_quality_production_cpu_r1 import accept as accept_CPU, original_alive
from .automatic_quality_production_r1 import validate_authority
from .automatic_quality_quote_r1 import validate_selected
from .automatic_quality_r1 import DIMENSIONS
from .gpu_budget_pool_v2 import BudgetPool


def checked_artifact(artifact):
    raw=base64.b64decode(artifact['raw_base64'],validate=True)
    if len(raw)!=artifact['bytes'] or hashlib.sha256(raw).hexdigest()!=artifact['sha256']:
        raise ValueError('Original artifact bytes/SHA differ')
    if 'data' in artifact:
        parsed=json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        if parsed!=artifact['data']:raise ValueError('Parsed metadata differs from original file bytes')
    return raw


def journal_bytes(artifact):
    raw=base64.b64decode(artifact['raw_base64'],validate=True)
    if len(raw)!=artifact['bytes'] or hashlib.sha256(raw).hexdigest()!=artifact['sha256']:
        raise ValueError('The exact original complete journal bytes are required')
    lines=raw.splitlines(keepends=True);events=[];tail=None
    for i,line in enumerate(lines):
        if not line.endswith(b'\n'):
            if i!=len(lines)-1:raise ValueError('Only an original last write may be incomplete')
            tail=dict(bytes=len(line),sha256=hashlib.sha256(line).hexdigest());break
        events.append(json.loads(line))
    return events,tail


def decoder_evidence(row):
    evidence=row['decoder_evidence'];dimension=row['dimension'];sampling=row['observed_sampling']
    if dimension=='MUSIQ_LONGER512':
        times=[Fraction(tick)*Fraction(base) for tick,base in row.get('pts',[])]
        if (evidence.get('backend')!='ORIGINAL_FFMPEG_READER'
                or evidence.get('model_input_shapes')!=[[1,3,288,512]]*93
                or len(times)!=93 or any(b-a!=Fraction(1,16) for a,b in zip(times,times[1:]))):
            raise ValueError('All93 actual MUSIQ shapes/timestamps are required')
        return
    readers=evidence.get('readers',[])
    if (len(readers)!=1 or readers[0].get('source_frames')!=93
            or not math.isclose(readers[0].get('source_fps',0),16.,abs_tol=1e-6,rel_tol=0)
            or evidence.get('decoder_pixels_or_preprocessing_not_replaced') is not True
            or evidence.get('metric_decoder_not_assumed_byte_equal_to_N07_RGB_backend') is not True):
        raise ValueError('Original full93 decoder observation and preprocessing boundary required')
    if dimension in ('subject_consistency','overall_consistency'):
        if (readers[0].get('backend')!='DECORD' or evidence.get('batches')!=[sampling['frame_indices']]
                or evidence.get('selections')!=[]):
            raise ValueError('Original decord source-index batch required')
    else:
        expected=[sampling['frame_indices'],sampling['target_indices']] if dimension=='motion_smoothness' else [sampling['frame_indices']]
        if (readers[0].get('backend')!='OPENCV' or readers[0].get('released') is not True
                or evidence.get('batches')!=[] or evidence.get('selections')!=expected):
            raise ValueError('Original OpenCV release and actual source/target selection required')


def verify_prompt_means(bundle,rows,summary,comparisons):
    """Separate arithmetic check: both seeds, then equally weighted prompts."""
    cases={r['id']:r for r in bundle['cases']};prompts=sorted({c['prompt_id'] for c in cases.values()})
    values={(r['case_id'],r['method'],r['dimension']):r.get('value') if r['status']=='SCORED' else None for r in rows}
    def average(items):return math.fsum(items)/len(items) if items else None
    def near(left,right):return left is right if left is None or right is None else math.isclose(left,right,rel_tol=1e-11,abs_tol=1e-12)
    grouped={};method_rows={(r['method'],r['dimension']):r for r in summary['methods']}
    if len(method_rows)!=60:raise ValueError('All ten-method/six-dimension summary positions required')
    for dimension in DIMENSIONS:
        for method in bundle['methods']:
            old=method_rows[method,dimension];expected=[]
            for prompt in prompts:
                selected=[c for c in cases.values() if c['prompt_id']==prompt]
                if sorted(c['seed'] for c in selected)!=[17,43]:raise ValueError('Both original seeds per prompt required')
                eligible=dimension!='temporal_flickering' or selected[0]['static_eligible']
                raw=[values[c['id'],method,dimension] for c in selected]
                value=average(raw) if all(x is not None for x in raw) else None
                grouped[prompt,method,dimension]=value
                expected.append(dict(prompt_id=prompt,eligible=eligible,value=value))
            if (len(old['prompt_rows'])!=8 or any(a['prompt_id']!=b['prompt_id'] or a['eligible']!=b['eligible'] or not near(a['value'],b['value'])
                    for a,b in zip(old['prompt_rows'],expected))):raise ValueError('Per-prompt values must come from both original seeds')
            good=[r['value'] for r in expected if r['eligible'] and r['value'] is not None];eligible=sum(r['eligible'] for r in expected)
            full=average(good) if eligible and len(good)==eligible else None
            if (old['registered_prompts']!=8 or old['registered_seed_cases']!=16 or old['eligible_prompts']!=eligible
                    or old['complete_two_seed_prompts']!=len(good) or not near(old['full_eligible_prompt_mean'],full)
                    or not near(old['available_complete_prompt_mean'],average(good))):raise ValueError('Prompt-equal method aggregation differs')
    result={(r['candidate'],r['baseline'],r['dimension']):r for r in summary['comparisons']}
    if len(result)!=len(comparisons)*6:raise ValueError('Every original comparison/dimension is required')
    for dimension in DIMENSIONS:
        eligible=prompts if dimension!='temporal_flickering' else [p for p in prompts if next(c for c in cases.values() if c['prompt_id']==p)['static_eligible']]
        for candidate,baseline in comparisons:
            expected=[p for p in eligible if grouped[p,candidate,dimension] is not None and grouped[p,baseline,dimension] is not None]
            delta=average([grouped[p,candidate,dimension]-grouped[p,baseline,dimension] for p in expected]);old=result[candidate,baseline,dimension]
            full=delta if eligible and len(expected)==len(eligible) else None
            if (old['registered_prompt_denominator']!=8 or old['eligible_prompt_denominator']!=len(eligible)
                    or old['complete_paired_prompt_ids']!=expected or old['missing_eligible_prompt_ids']!=[p for p in eligible if p not in expected]
                    or not near(old['available_cohort_mean_delta'],delta) or not near(old['full_eligible_prompt_mean_delta'],full)
                    or old['cross_dimension_weighted_score'] is not None):raise ValueError('Paired prompt-equal comparison differs')


def financial(value,launch,config):
    files=value.get('files',{});billing=files.get('billing',{});sup=files.get('supervisor',{}).get('data') or {}
    bill=billing.get('data');pool=value.get('pool',{});job=pool.get('jobs',{}).get(launch['run_id'])
    if not bill or not job:
        return dict(finance_accepted=False,actual_GPUh=None,billed_limit_respected=False,
                    errors=['Missing original whole bill or own settlement'])
    errors=[]
    def check(ok,name):
        if not ok:errors.append(name)
    actual=bill.get('actual_GPUh')
    check(isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isfinite(actual) and actual>=0,'Finite actual GPU charge')
    keys=('source_revision','launch_id','run_id','gpu_uuid','config_sha256','scope_counts')
    check(all(bill.get(k)==launch[k] for k in keys),'Original whole bill identity')
    check(bill.get('status')=='N10_FULL960_ACTUAL_SCORING_GPU_BILL' and bill.get('generation_latency_claim') is False,'Scoring cost identity')
    check(isinstance(bill.get('wall_seconds'),(int,float)) and math.isclose(bill['wall_seconds']/3600,actual or 0,abs_tol=1e-12,rel_tol=1e-12),'Whole actual wall/3600')
    check(job.get('status')=='SETTLED' and job.get('actual_GPUh')==actual and job.get('billing_sha256')==billing['sha256'],'Own additive settlement')
    check(sup.get('billing_sha256')==billing['sha256'] and sup.get('actual_GPUh')==actual,'Original supervisor/bill agreement')
    check(all(job.get(k)==launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','scope_counts','production_CPU_sha256','authorization_sha256','bound_input_fingerprint')),'Own CPU/authority/source/scope charge')
    check(job.get('forecast_GPUh')==config['forecast_GPUh'] and job.get('billed_limit_GPUh')==bill.get('billed_limit_GPUh')==config['billed_limit_GPUh'],'Original whole forecast and limit')
    check(pool.get('cap_gpu_hours',0)>=config['cumulative_cap_GPUh'] and pool.get('origin_used_gpu_hours')==config['budget_origin_used_GPUh'],'Cumulative origin retained')
    check(all(math.isclose(pool[k],v,rel_tol=1e-12,abs_tol=1e-12) for k,v in BudgetPool.accounting(pool).items()),'Complete pool totals')
    if config['billed_limit_GPUh']>=12:check(job.get('kind')=='V2_SPECIFIC_WHOLE_CARD_APPROVAL','Original specific full-card approval retained')
    check(not value.get('GPU_telemetry_error') and value.get('own_GPU','').split(',')[0].strip()==launch['gpu_uuid'],'Original actual UUID observed')
    handles=value.get('expected_original_handles',{});observed=value.get('original_processes',{})
    for line in value.get('compute_apps','').splitlines():
        if not line.strip():continue
        gpu,pid=[x.strip() for x in line.split(',')[:2]]
        for name,expected in handles.items():
            if expected and gpu==launch['gpu_uuid'] and int(pid)==expected['pid']:
                now=observed.get(name,{})
                reused=now.get('start_ticks') is not None and now.get('start_ticks')!=expected['start_ticks']
                check(reused,'Own original compute PID still appears')
    later=False
    for name,other in pool['jobs'].items():
        if name!=launch['run_id'] and other['status']=='RESERVED_OR_RUNNING' and other['gpu_uuid']==launch['gpu_uuid']:
            later |= original_alive(dict(pid=other['supervisor_pid'],start_ticks=other['supervisor_start_ticks']),value.get('other_reservation_identities',{}).get(name))
    check(value.get('own_UUID_lock_exists') is True and (value.get('own_UUID_lock_free') is True or later),'Own lease released or documented later owner')
    respected=actual is not None and actual<=config['billed_limit_GPUh']
    check(respected or pool.get('budget_overrun_recorded') is True,'Any actual overrun retained')
    return dict(finance_accepted=not errors,actual_GPUh=actual,billed_limit_respected=respected,errors=errors)


def accept(value,launch):
    if (value.get('launch')!=launch or value.get('mode')!='terminal'
            or value['observed_unix']<launch['next_check_not_before_unix']):
        raise ValueError('Exact original post-ETA N10 terminal capture required')
    if value.get('status')=='N10_FULL960_STILL_RUNNING_TECHNICAL_ONLY':
        return dict(status='N10_ORIGINAL_STILL_RUNNING_REESTIMATE_ONCE',full_protocol_accepted=False,
                    full_scientific_scope_accepted=False,registered_metric_positions=960,GPU_submissions=0)
    if value.get('status')!='N10_FULL960_ORIGINAL_ONCE_CAPTURE':
        raise ValueError('An observation error is not original task completion')
    reg=value['registration'];files=value['files']
    registration_artifact=value['registration_artifact'];checked_artifact(registration_artifact)
    if registration_artifact['sha256']!=value['registration_sha256'] or registration_artifact['data']!=reg:
        raise ValueError('Original registration bytes and parsed source must match')
    if (value['registration_sha256']!=launch['registration_sha256'] or reg['source_revision']!=launch['source_revision']
            or not reg['payload_sha256'] or value['payload_actual_sha256']!=reg['payload_sha256']):
        raise ValueError('All original271 source bytes and exact registration are required')
    sup=files.get('supervisor',{}).get('data') or {}
    expected=dict(supervisor=launch['supervisor_identity'],child=sup.get('child_identity'))
    if any(original_alive(x,value.get('original_processes',{}).get(k)) for k,x in expected.items()):
        return dict(status='N10_ORIGINAL_STILL_RUNNING_REESTIMATE_ONCE',full_protocol_accepted=False,
                    full_scientific_scope_accepted=False,registered_metric_positions=960,GPU_submissions=0)
    CPU=value.get('CPU_capture');saved=value.get('CPU_independent')
    if not CPU or not saved or value.get('local_CPU_provenance_error'):
        raise ValueError('Keep the original independently accepted production CPU provenance')
    for data,body,digest in ((CPU,value['CPU_capture_raw_base64'],value['CPU_capture_sha256']),
                             (saved,value['CPU_independent_raw_base64'],value['CPU_independent_sha256'])):
        raw=base64.b64decode(body,validate=True)
        if hashlib.sha256(raw).hexdigest()!=digest or json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)!=data:
            raise ValueError('Original production CPU file bytes changed')
    actual=accept_CPU(CPU)
    if (not actual.get('CPU_accepted') or any(saved.get(k)!=v for k,v in actual.items())
            or saved['capture_sha256']!=value['CPU_capture_sha256']
            or value['CPU_independent_sha256']!=launch['independent_CPU_acceptance_sha256']
            or CPU['registration']!=reg or CPU['registration_sha256']!=launch['registration_sha256']):
        raise ValueError('Original actual five-command production CPU must match this GPU task')
    required=('config','accepted_inputs','model_CPU_registration','model_CPU_acceptance','model_resources',
              'whole_card_cost','unpriced_scope','production_CPU','production_bundle','CPU_launch','CPU_exit','authorization','CPU_independent_remote')
    if any(not files.get(k,{}).get('data') for k in required):
        raise ValueError('Original full input/CPU/authority/cost files are missing')
    c=files['config']['data'];bundle=files['accepted_inputs']['data']['input_bundle'];initial_rows(bundle)
    for artifact in files.values():
        if artifact.get('exists'):checked_artifact(artifact)
    if (files['config']['sha256']!=launch['config_sha256'] or files['config']['sha256']!=reg['payload_sha256'].get('N10-production-config.json')
            or c['run_id']!=launch['run_id'] or c['scope_counts']!=launch['scope_counts']
            or c['input_bundle_fingerprint']!=launch['bound_input_fingerprint']
            or c['scorer_fingerprint']!=bundle['scorer_fingerprint']):
        raise ValueError('Original full960/actual scorer/config identity differs')
    for name in ('accepted_inputs','model_CPU_registration','model_CPU_acceptance','model_resources','whole_card_cost','unpriced_scope'):
        ref=c['references'][name]
        if files[name]['sha256']!=ref['sha256'] or reg['payload_sha256'].get(ref['ref'])!=ref['sha256']:
            raise ValueError('Original hash-bound '+name+' differs')
    validate_selected(c,files['unpriced_scope']['data'],files['whole_card_cost']['data'])
    proof=files['production_CPU']['data'];authority=files['authorization']['data']
    validate_authority(c,reg,bundle,proof,authority,revision=launch['source_revision'],gpu_uuid=launch['gpu_uuid'],
        config_sha256=launch['config_sha256'],registration_sha256=launch['registration_sha256'],
        proof_sha256=files['production_CPU']['sha256'],worker_sha256=reg['payload_sha256']['scripts/score_wc_paper_N10_full960_r1.py'])
    if (files['production_CPU']['sha256']!=saved['production_CPU_sha256']
            or files['production_bundle']['sha256']!=saved['bundle_sha256']
            or files['CPU_independent_remote']['sha256']!=value['CPU_independent_sha256']
            or files['CPU_independent_remote']['data']!=saved
            or files['authorization']['sha256']!=launch['authorization_sha256']
            or authority.get('independent_CPU_acceptance_sha256')!=value['CPU_independent_sha256']
            or files['CPU_exit']['data']['exit_code']!=0
            or any(files['CPU_launch']['data']['identity'][k]!=saved['original_CPU_identity'][k] for k in ('pid','start_ticks'))):
        raise ValueError('Original actual CPU proof/bundle and whole dispatch authority differ')
    modelreg=files['model_CPU_registration']['data'];models=files['model_CPU_acceptance']['data']
    if (modelreg['roles']!=list(ROLES) or models.get('CPU_accepted') is not True or models.get('accepted_models')!=5
            or models['registration_sha256']!=files['model_CPU_registration']['sha256']
            or models['source_revision']!=modelreg['source_revision']
            or [r['role'] for r in models['rows']]!=list(ROLES)
            or any(r['status']!='CPU_ROLE_ACCEPTED' or r['proof']['constructor_source_sha256']!=reg['payload_sha256'][SELF_REF] for r in models['rows'])
            or any(reg['payload_sha256'].get(n)!=h for n,h in modelreg['payload_sha256'].items())
            or modelreg['payload_sha256'].get(SELF_REF)!=bundle['evaluator_identity']['constructor_source_sha256']
            or set(files['model_resources']['data']['resources'])!=set(ROLES)
            or any((r['bytes'],r['sha256'])!=WEIGHTS[k] for k,r in files['model_resources']['data']['resources'].items())):
        raise ValueError('The complete original five-model source/resource/CPU identity must survive')
    finance=financial(value,launch,c);journal=files.get('journal',{})
    if not journal.get('exists'):
        return dict(status='N10_ORIGINAL_TERMINAL_NO_JOURNAL_RETAINED',full_protocol_accepted=False,
            full_scientific_scope_accepted=False,registered_metric_positions=960,valid_scored_metric_positions=0,
            rows=initial_rows(bundle),summary=None,finance=finance,GPU_submissions=0)
    events,tail=journal_bytes(journal)
    if not events:raise ValueError('An empty original journal cannot establish scored evidence')
    if events[0].get('comparisons')!=c['comparisons'] or events[0].get('bootstrap_repetitions')!=c['bootstrap_repetitions']:
        raise ValueError('Use all original19 contrasts and4096 prompt resamples')
    rebuilt=reconstruct(bundle,events);rows=rebuilt['rows'];scored=[r for r in rows if r['status']=='SCORED']
    stage=PurePosixPath(launch['stage'])
    for row in scored:
        decoder_evidence(row)
        required_sources={'src/wcomr/imaging_quality.py','src/wcomr/rv0_video_reader.py'} if row['dimension']=='MUSIQ_LONGER512' else {'upstream/vbench/'+row['dimension']+'.py'}
        if row['dimension'] in ('subject_consistency','overall_consistency'):required_sources.add('upstream/vbench/utils.py')
        actual_sources=set()
        for source,digest in row['metric_source_sha256'].items():
            path=PurePosixPath(source)
            if not path.is_absolute() or not path.is_relative_to(stage) or reg['payload_sha256'].get(str(path.relative_to(stage)))!=digest:
                raise ValueError('An original scored metric source changed or escaped its CPU-accepted stage')
            actual_sources.add(str(path.relative_to(stage)))
        if actual_sources!=required_sources:raise ValueError('Exact original per-dimension metric/helper sources required')
    final=rebuilt['final'];metric=files.get('metrics',{});saved_ok=False
    if final is not None and metric.get('data'):
        wanted=dict(final,original_journal_sha256=journal['sha256'],original_journal_bytes=journal['bytes'])
        if metric['data']!=wanted:raise ValueError('Saved result differs from the independently rebuilt original journal')
        saved_ok=True
    if final is not None:verify_prompt_means(bundle,rows,final['summary'],c['comparisons'])
    runner=files.get('runner',{}).get('data') or {};errors=[];provenance_errors=[]
    def check(ok,name,provenance=True):
        if not ok:
            errors.append(name)
            if provenance:provenance_errors.append(name)
    for original,label in ((sup,'supervisor'),(runner,'runner')):
        check(all(original.get(k)==launch[k] for k in ('source_revision','config_sha256','scope_counts')),label+' original source/config/scope')
    check(all(sup.get('supervisor_identity',{}).get(k)==launch['supervisor_identity'].get(k) for k in ('pid','start_ticks')),'Original supervisor handle')
    check(all(sup.get(k)==launch[k] for k in ('run_id','launch_id','gpu_uuid','registration_sha256')),'Original supervisor whole task identity')
    check(value.get('expected_original_handles')==expected,'Original observed handle set')
    admission=runner.get('original_admission',{})
    check(all(admission.get(k)==launch[k] for k in ('run_id','launch_id','gpu_uuid'))
        and admission.get('reservation_limit_GPUh')==c['billed_limit_GPUh'] and admission.get('ledger_written') is False,'Original admitted child')
    check(sup.get('runner_sha256')==files.get('runner',{}).get('sha256'),'Original runner bytes')
    check(sup.get('status')=='N10_FULL960_ORIGINAL_GPU_TERMINAL_NOT_QUALITY_ACCEPTANCE','Original GPU supervisor terminal state',False)
    check(sup.get('child_exit_code')==0 and runner.get('status')=='N10_FULL960_FINISHED_FAILURES_RETAINED','Original GPU worker completed',False)
    check(runner.get('input_bundle_fingerprint')==bundle['fingerprint'],'Original GPU input identity')
    if final is not None:
        check(runner.get('metric_status_counts')==final['metric_status_counts']
            and runner.get('all_ready_positions_scored')==final['all_ready_positions_scored']
            and runner.get('original_journal_sha256')==journal['sha256'],'Original runner/final journal agreement')
    complete=final is not None and final['all_ready_positions_scored'] and len(scored)==645 and tail is None and not provenance_errors
    lifecycle=rebuilt['lifecycle']
    if complete:
        if [r['dimension'] for r in lifecycle]!=list(DIMENSIONS):raise ValueError('All six original model lifecycle records required')
        for info in lifecycle:
            if info['dimension']=='temporal_flickering':
                if info['status']!='NO_ELIGIBLE_INPUTS_NO_SCORER_ENTERED' or info['attempted']!=0:raise ValueError('Static N/A must not enter a scorer')
            elif info['status']!='CONTEXT_RELEASED' or info['attempted']!=129 or info['accepted']!=129:
                raise ValueError('Every complete five-model context must release after all129 observed scores')
    protocol=not errors and saved_ok and tail is None and finance['finance_accepted'] and finance['billed_limit_respected']
    return dict(status='N10_FULL960_ALL645_SCORES_AND_PROTOCOL_INDEPENDENTLY_ACCEPTED' if protocol and complete else 'N10_ORIGINAL_FULL_SCOPE_ISSUES_OR_PARTIAL_EVIDENCE_RETAINED',
        full_protocol_accepted=protocol and complete,original_terminal_attempt_protocol_accepted=protocol,
        full_scientific_scope_accepted=complete,journal_evidence_accepted=True,valid_scored_metric_positions=len(scored),
        registered_generation_positions=160,registered_metric_positions=960,original_input_status_counts=dict(Counter(r['input_status'] for r in bundle['rows'])),
        observed_metric_status_counts=rebuilt['metric_status_counts'],original_unfinished_tail=tail,errors=errors,provenance_errors=provenance_errors,
        rows=rows,lifecycle=lifecycle,summary=final['summary'] if final else None,finance=finance,
        original_saved_result_matches_journal=saved_ok,comparison_pairs=c['comparisons'],prompt_bootstrap_repetitions=c['bootstrap_repetitions'],
        independent_prompt_seed_means_verified=final is not None,
        actual_GPUh=finance['actual_GPUh'],new_generation_paths=0,GPU_submissions=0,
        evidence_kind='SYNTHETIC_UNIT_ONLY_NOT_REAL_RESEARCH' if value.get('unit_fixture_only') else 'ORIGINAL_ACTUAL_SCORING_RECEIPT',
        no_cross_dimension_weighted_total=True,not_full_official_VBench=True,no_physics_or_human_review_claim=True)
