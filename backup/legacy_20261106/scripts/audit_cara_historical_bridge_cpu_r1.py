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
    if reg['namespace']!='CARA_PG_P1_CPU_R1' or reg['source_revision']!=L['source_revision'] or reg['stage']!=L['stage']:
        raise ValueError('Original registered source/stage required')
    if v['payload_actual_sha256']!=reg['payload_sha256'] or v['runtime_actual_sha256']!=reg['runtime_source_sha256']:
        raise ValueError('Registered source/runtime changed')
    if not proof['exists']:raise ValueError('Original full proof missing')
    p=proof['data']
    if p['source_revision']!=reg['source_revision'] or p['registration_sha256']!=L['registration_sha256'] or p['actual_request_count']!=6 or p['guard_refusal_controls']!=6 or not p['actual_SetupArguments']:
        raise ValueError('Six actual FIT/SELECT request and SetupArguments boundary required')
    if p['CUDA_initialized'] or p['model_weights_loaded'] or p['GPU_submissions'] or p['ledger_written']:raise ValueError('CPU boundary exceeded')
    if p['codec']['RGB_frames']!=93 or not all(p['codec'][k] for k in ('actual_NLTK_tokenization','ordinary_video_writer','ffprobe_exit0')):
        raise ValueError('Actual tokenizer/93-frame codec boundary failed')
    if not all(p['transport'][k] for k in ('parent_and_namespace_match','original_fd_inode_match','independent_open_refused','GPU_hidden','child_exited','fixture_lock_released')):
        raise ValueError('CPU inherited handle transport failed')
    if p['status']!='HISTORICAL_BRIDGE_ACTUAL_ENTRY_AND_FULL148_CPU_COMPLETE_NOT_GPU':
        raise ValueError('Wrong production proof kind')
    raw=(json.dumps(p,indent=2,allow_nan=False)+'\n').encode()
    if hashlib.sha256(raw).hexdigest()!=proof['sha256']:raise ValueError('Proof bytes binding differs')
    checks=p['numeric']['checks']
    if len(checks)!=2 or {x['flow'] for x in checks}!={False,True}:raise ValueError('Both full flow states required')
    if p['numeric']['actual_CPU_paths']!=148 or p['numeric']['ordinary_pairs']!=5328:raise ValueError('Full148 scope required')
    roles={'S26_C','S26_A_PHASE','SHARED26_C','S25_C','S25_A_PHASE','S24_C','S24_A_PHASE'}
    for x in checks:
        if x['status']!='PASS' or x['complete_CPU_paths']!=74 or not x['Native_allD_equal'] or not x['all36_audit_lean_controls']:
            raise ValueError('Whole actual executor equivalence scope required')
        rows=x['checks']
        if len(rows)!=28 or {r['role'] for r in rows}!=roles or len({r['input'] for r in rows})!=4:
            raise ValueError('All seven roles and four declared inputs required')
        if len({(r['role'],r['input']) for r in rows})!=28:raise ValueError('Duplicate pair')
        if sum(r['audit_lean_checked'] for r in rows)!=7:raise ValueError('Missing per-role audit/lean controls')
        if not all(all(r[k] for k in ('all36_guided_equal','final_latent_and_mock_video_equal','alpha_and_true_anchor_history_equal')) for r in rows):
            raise ValueError('Historical/PG numerical or alpha mismatch')
    quote='manifests/cara_historical_bridge104_scope_quote_r1_20261024.json'
    if reg['payload_sha256'][quote]!=hashlib.sha256((ROOT/quote).read_bytes()).hexdigest():raise ValueError('Quote not bound to accepted source')
    return dict(status='HISTORICAL_BRIDGE_PRODUCTION_ENTRY_EQUIVALENCE_CPU_ACCEPTED_GPU_PENDING',
        source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=proof['sha256'],
        production_entry_CPU_accepted=True,complete_CPU_paths=148,actual_request_count=6,
        historical_masks_and_original_phase_alpha_preserved=True,full36_Native_control=True,
        actual_guardrail_codec_transport=True,GPU_submissions=0,clean_prices_accepted=False,
        full_GPU_lifecycle_accepted=False,GPU_dispatch_ready=False,quality_or_speed_result=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.capture.read_bytes();v=accept(json.loads(raw));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
    with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
    print(json.dumps(v))
if __name__=='__main__':main()
