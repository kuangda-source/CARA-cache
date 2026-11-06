#!/usr/bin/env python3
"""Independently accept complete original PG entry CPU evidence, never GPU prices."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def accept(v):
    c=v['container'];L=v['launch'];reg=v['registration'];proof=v['proof']
    if c['state']['Running'] or c['state']['ExitCode']!=0 or c['state']['OOMKilled']:raise ValueError('Original CPU exit0 required')
    if c['image']!='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d' or not c['readonly_root'] or c['devices'] or c['device_requests'] or c['nano_cpus']!=10**9 or c['memory_bytes']!=4*2**30:
        raise ValueError('Pinned bounded GPU-hidden CPU container required')
    if reg['namespace']!='CARA_CAL66_ENTRY_CPU_R2' or reg['source_revision']!=L['source_revision'] or reg['stage']!=L['stage']:
        raise ValueError('Original registered source/stage required')
    if hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()!=L['registration_sha256'] or 'cosmos_predict2/config.py' not in reg['runtime_source_sha256']:
        raise ValueError('Registration and actual frozen class source binding required')
    if v['payload_actual_sha256']!=reg['payload_sha256'] or v['runtime_actual_sha256']!=reg['runtime_source_sha256']:
        raise ValueError('Registered source/runtime changed')
    if not proof['exists']:raise ValueError('Original full proof missing')
    p=proof['data']
    if p['source_revision']!=reg['source_revision'] or p['registration_sha256']!=L['registration_sha256'] or p['actual_request_count']!=60 or p['guard_refusal_controls']!=60 or not p['actual_SetupArguments']:
        raise ValueError('60 actual role/request-step and SetupArguments boundaries required')
    b=p['frozen_boundary']
    if (p['status']!='SHARED_CAL66_FROZEN_ENTRY_CPU_R2_COMPLETE_NOT_GPU'
            or b['actual_class']!='cosmos_predict2.config.InferenceArguments'
            or not all(b[k] for k in ('actual_class_frozen','old_bug_reproduced','full_resolution_request_identity_preserved','failed66_original_denominator_retained','original_requests_unchanged'))
            or b['preload_validated_slots']!=66 or b['actual_adapter_guard_refusals']!=60
            or b['failed66_completed']!=0 or b['failed66_unreached']!=65
            or b['negative_controls']!=['invalid_override']*5+['real_schema_constraint','bad_slot_grid','failed_slot_no_replay']):
        raise ValueError('Real frozen class must pass through Requests before model load and both engine boundaries')
    if p['CUDA_initialized'] or p['model_weights_loaded'] or p['GPU_submissions'] or p['ledger_written']:raise ValueError('CPU boundary exceeded')
    if p['codec']['RGB_frames']!=93 or not all(p['codec'][k] for k in ('actual_NLTK_tokenization','ordinary_video_writer','ffprobe_exit0')):
        raise ValueError('Actual tokenizer/93-frame codec boundary failed')
    if not all(p['transport'][k] for k in ('parent_and_namespace_match','original_fd_inode_match','independent_open_refused','GPU_hidden','child_exited','fixture_lock_released')):
        raise ValueError('CPU inherited handle transport failed')
    if p['batch_controls_passed']!=9:raise ValueError('Whole timing batch controls required')
    checks=p['numeric']['checks']
    if len(checks)!=2 or {x['flow'] for x in checks}!={False,True}:raise ValueError('Both full flow states required')
    card=json.loads((ROOT/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json').read_text())
    for x in checks:
        if not all(x[k] for k in ('actual_frozen_InferenceArguments','original_request_unchanged','writer_failure_retained','failed_slot_replay_refused')) or x['fixture_geometry']!='16,16':raise ValueError('Actual frozen class numeric chain/negative controls missing')
        if x['status']!='PASS' or x['complete_paths']!=30 or x['actual_Cosmos_weights'] or x['real_generated_video']:
            raise ValueError('All15 roles times2 repeats must complete for each flow')
        if ({r['role'] for r in x['roles']}!=set(card['roles']) or len(x['roles'])!=15
                or any(r['updates']!=card['roles'][r['role']]['requested_steps']+1 for r in x['roles'])):
            raise ValueError('Missing/duplicate registered role')
        if not all(r['repeat_all_guided_final_RGB_equal'] for r in x['roles']):
            raise ValueError('Repeated guided/final/RGB differs')
        if not all(x[k] for k in ('all15_production_roles','repeat_identity_verified','original_alpha_and_D_preserved',
                                  'duplicate_refused','guard_refusal_preserved')):
            raise ValueError('New request boundary failed')
    if checks[0]['roles']!=checks[1]['roles']:raise ValueError('Flow changed tested scope')
    if proof['sha256']!=hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest():
        raise ValueError('Original proof bytes binding failed')
    return dict(status='SHARED_CAL66_FROZEN_ENTRY_CPU_R2_ACCEPTED_NOT_GPU',
        source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=proof['sha256'],
        production_entry_CPU_accepted=True,frozen_request_chain_CPU_accepted=True,preload_validated_slots=66,actual_class=b['actual_class'],old_bug_reproduced=True,complete_CPU_paths=60,actual_request_count=60,
        roles=checks[0]['roles'],both_flow_modes=True,original_alpha_and_D_preserved=True,
        actual_guardrail_codec_transport=True,GPU_submissions=0,actual_Cosmos_weights=False,
        full_GPU_lifecycle_accepted=False,GPU_dispatch_ready=False,quality_or_speed_result=False)




def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.capture.read_bytes();v=accept(json.loads(raw));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
    with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
    print(json.dumps(v))
if __name__=='__main__':main()
