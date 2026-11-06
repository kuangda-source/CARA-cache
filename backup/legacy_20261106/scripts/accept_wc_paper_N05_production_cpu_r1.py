#!/usr/bin/env python3
"""Offline independent production-CPU acceptance; never re-SSH to fix parsing."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def accept(v):
    from wcomr.paper_baseline_production_r1 import CONFIG,COUNTS,PRODUCTION_CPU_STATUS,matrix,sha
    assert v['status']=='N05_PRODUCTION_CPU_ONCE_CAPTURE' and v['process']['state'] in (None,'Z','X')
    assert v['observed_unix']>=v['launch']['first_collection_not_before_unix']
    assert v['registration_SHA256']==v['launch']['registration_sha256'] and all(v['payload_verified'].values())
    bundle=v['files']['CPU-bundle-result.json']['data'];proof=v['files']['production-CPU-result.json']['data']
    assert bundle['status']=='N05_CORE66_COMPLETE_PRODUCTION_CPU_PASS_NOT_GPU' and bundle['exit_code']==0
    assert len(bundle['commands'])==4 and all(r['exit_code']==0 for r in bundle['commands'])
    assert bundle['source_revision']==proof['source_revision']==v['launch']['source_revision']==v['registration']['source_revision']
    assert proof['status']==PRODUCTION_CPU_STATUS and proof['exit_code']==0 and proof['scope_counts']==COUNTS
    assert proof['registration_sha256']==v['registration_SHA256'] and proof['config_sha256']==sha(ROOT/CONFIG)
    c=json.loads((ROOT/CONFIG).read_text())
    assert proof['matrix']==matrix([r['name'] for r in c['requests']]) and len(proof['matrix'])==66
    assert proof['actual_sample_argument_variants']==44 and len(proof['mutations_refused'])==10
    assert {r['requested_steps']:r['actual_updates'] for r in proof['actual_scheduler_CPU_checks']}=={35:36,26:27,18:19}
    assert all(r['all_sigmas_and_timesteps_equal'] for r in proof['actual_scheduler_CPU_checks'])
    assert proof['native_forward_identity']['qualified_name']=='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'
    assert not proof['CUDA_initialized'] and proof['GPU_submissions']==proof['model_weights_loaded']==0
    assert not proof['ledger_written'] and not bundle['ledger_written'] and not bundle['shared_runtime_written']
    assert not bundle['original_N06_stage_written']
    return dict(status='N05_CORE66_REAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU',
        source_revision=v['launch']['source_revision'],payload_count=len(v['payload_verified']),CPU_commands=4,
        formal_denominator=44,full_denominator=66,ordinary_pairs=2220,CFG_calls=4440,
        actual_sample_argument_variants=44,CPU_wall_seconds=bundle['wall_seconds'],
        native_forward_identity=proof['native_forward_identity'],GPU_submissions=0,ledger_written=False,
        original_N06_stage_touched=False,real_video_quality_or_speed_claim=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    v=accept(json.loads(gzip.decompress(a.capture.read_bytes())))
    v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
    a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))

if __name__=='__main__':main()
