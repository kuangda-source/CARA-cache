"""Whole E3 envelope: charge all 54 paths, storage observation and 20 loads."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    refs=['manifests/wc_e3_complete64_reuse10_fresh54_blocks_r1_20261011.json',
        'reports/wc_current_birth_full64_r1_terminal_20261010_capture_and_independent_audit.json',
        'reports/wc_e1_diag8_gpu_r2_terminal_20261011_capture.json',
        'reports/wc_current_birth_full64_whole_cost_20261010.json']
    scope,old_capture,e1_capture,prior=[json.loads((root/n).read_text()) for n in refs]
    sources={n:sha(root/n) for n in refs}
    def native(capture,name):
        item=capture['files'][name];p=root/item['local_path'];z=p.read_bytes();raw=gzip.decompress(z)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(z).hexdigest()==item['compressed_sha256']
        sources[item['local_path']]=sha(p)
        return json.loads(raw)
    assert e1_capture['original_source_terminal_scope_and_cost_independently_verified']
    old=native(old_capture,'runner');completed=[]
    for strategy,batch in old['batches'].items():
        for request in batch.get('requests',[]):
            for row in request['paths']:
                if row['status']=='COMPLETE_PARENT_PATH':
                    completed.append({'strategy':strategy,'sample':request['sample_name'],
                        'method':row['collect'],'seconds':row['instrumented_parent_pipeline_wall_seconds']})
    assert len(completed)==14
    paired=[];loads=[old['load_seconds'],prior['parent_model_load_seconds']]
    for label in ('COLD','PREFIX'):
        left=native(e1_capture,'ORIGINAL_'+label+'-receipt')
        right=native(e1_capture,'CPU_'+label+'-receipt')
        loads.extend([left['load_seconds'],right['load_seconds']])
        a=[r for q in left['batch']['requests'] for r in q['paths']]
        b=[r for q in right['batch']['requests'] for r in q['paths']]
        assert len(a)==len(b)==(1 if label=='COLD' else 3)
        for x,y in zip(a,b):
            assert x['label']==y['label'] and x['guided_sha256']==y['guided_sha256'] and x['final_latent_sha256']==y['final_latent_sha256']
            t=x['instrumented_parent_pipeline_wall_seconds'];u=y['instrumented_parent_pipeline_wall_seconds']
            paired.append({'arm':label,'label':x['label'],'original_instrumented_seconds':t,
                'CPU_instrumented_seconds':u,'observed_difference_seconds':u-t})
    assert len(scope['all64_slots'])==64 and len(scope['blocks'])==20
    fresh=sum(len(b['paths']) for b in scope['blocks']);assert fresh==54
    maximum_pipeline=max(r['seconds'] for r in completed)
    maximum_observed_storage_difference=max(r['observed_difference_seconds'] for r in paired)
    maximum_loading=max(loads)
    # This is a planning envelope, not a causal copy-cost estimate. Every path
    # is charged the slowest original full pipeline and the largest paired
    # storage observation, including SOURCE_RA which does not use that owner.
    sampling=fresh*(maximum_pipeline+maximum_observed_storage_difference)
    loading=len(scope['blocks'])*maximum_loading
    subtotal=sampling+loading;seconds=subtotal*1.35+120.
    sources[str(Path(__file__).resolve().relative_to(root))]=sha(__file__)
    value={'status':'E3_COMPLETE64_REUSE10_FRESH54_WHOLE_PLANNING_ENVELOPE_NOT_EXECUTABLE_CARD',
        'scientific_positions':64,'qualified_reused_positions':10,'fresh_complete_paths':54,
        'independent_model_loads':20,'maximum_paths_per_process':3,'fresh_solver_updates':1944,
        'fresh_CFG_calls':3888,'original14_instrumented_pipeline_observations':completed,
        'same_output_E1_storage_pipeline_observations':paired,'all_recorded_loading_seconds':loads,
        'slowest_original_pipeline_seconds':maximum_pipeline,
        'largest_observed_storage_pipeline_difference_seconds':maximum_observed_storage_difference,
        'maximum_observed_model_loading_seconds':maximum_loading,
        'all54_instrumented_pipeline_envelope_seconds':sampling,'all20_loading_seconds':loading,
        'unmargined_seconds':subtotal,'whole_scope_margin_multiplier':1.35,
        'shutdown_flush_reserve_seconds':120.,'forecast_complete_seconds':seconds,
        'forecast_complete_GPUh':seconds/3600.,'automatic_single_job_GPUh':8.,
        'specific_complete_card_approval_required_after_production_CPU':seconds/3600.>8,
        'not_divided_into20_permission_cards':True,'no_simple54_over64_old_cost_discount':True,
        'not_isolated_causal_storage_cost_or_clean_latency_or_runtime_guarantee':True,
        'rationale':'Use all original14 including the dense control, pair E1 observations with identical actual output, conservatively add the largest non-isolated storage difference to every fresh path, and charge20 maximum observed loads. Retain the existing35% whole-scope allowance and120s cleanup reserve. Failed/aborted paths and all model work are billed by the whole-card supervisor.',
        'source_sha256':sources,'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False,
        'actual_production_and_full_supervisor_CPU_pending':True}
    p=root/'reports/wc_e3_complete64_whole_cost_r1_20261011.json';assert not p.exists()
    p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','fresh_complete_paths','independent_model_loads','forecast_complete_GPUh','GPU_submissions')}))


if __name__=='__main__':main()
