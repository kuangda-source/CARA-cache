"""Independently require actual SM86-host CPU entry and complete failure tests."""
import argparse
import hashlib
import json
from pathlib import Path
from cara_cal66_a6000_profile_r1 import RUN, VERSION
from wc_four_card_resource_cpu_r4 import write


def accept(cap):
    L=cap['launch'];reg=cap['registration'];proof=cap['proof'];con=cap['container']
    assert cap['registration_sha256']==L['registration_sha256']==proof['registration_sha256']
    assert reg['namespace']==VERSION and reg['stage']==L['stage']
    assert reg['source_revision']==L['source_revision']==proof['source_revision']
    assert cap['payload_actual_sha256']==reg['payload_sha256']==proof['execution_source_sha256']
    assert cap['runtime_actual_sha256']==reg['runtime_source_sha256']
    assert not con['State']['Running'] and con['State']['ExitCode']==0 and not con['State']['OOMKilled']
    assert con['HostConfig']['ReadonlyRootfs'] and con['HostConfig']['NanoCpus']==2*10**9
    assert con['HostConfig']['Memory']==8*2**30 and not con['HostConfig']['DeviceRequests']
    assert con['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
    env=dict(x.split('=',1) for x in con['Config']['Env'])
    assert env['CUDA_VISIBLE_DEVICES']=='' and env['NVIDIA_VISIBLE_DEVICES']=='void'
    assert proof['status']=='CAL66_A6000_PRODUCTION_COMBINATION_CPU_COMPLETE' and proof['run_id']==RUN
    assert proof['scope_counts']['total_paths']==66 and proof['terminal_tests']==60
    entry=proof['real_entry'];b=entry['frozen_boundary']
    assert entry['actual_request_count']==entry['guard_refusal_controls']==60
    assert b['preload_validated_slots']==66 and b['old_bug_reproduced'] and b['original_requests_unchanged']
    assert b['failed66_original_denominator_retained'] and b['failed66_unreached']==65
    assert entry['numeric']['checks'] and {r['flow'] for r in entry['numeric']['checks']}=={False,True}
    # The exact lifecycle schema is supplied by the already reviewed checker;
    # require all expected scenarios rather than a loose "passed" summary.
    assert len(proof['lifecycle']['checks'])==10
    assert len(proof['storage_lifecycle']['checks'])==6
    q=proof['quality_probe'];assert q['models_really_loaded'] and q['frames']==93
    assert {r['dimension'] for r in q['rows']}=={'MUSIQ_LONGER512','subject_consistency','motion_smoothness'}
    assert not any(proof[k] for k in ('CUDA_initialized','GPU_submissions','authoritative_ledger_written'))
    assert not entry['CUDA_initialized'] and not q['CUDA_initialized']
    return dict(status='CAL66_A6000_COMPLETE_CPU_ACCEPTED_NOT_GPU',production_CPU_accepted=True,
                full_GPU_lifecycle_CPU_accepted=True,independent_quality_models_CPU_accepted=True,
                source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],
                proof_sha256=cap['proof_sha256'],execution_source_sha256=reg['payload_sha256'],
                observed_unix=cap['observed_unix'],scope_counts=proof['scope_counts'],GPU_submissions=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    value=accept(json.loads(a.capture.read_text()));value.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
    write(a.output,value);print(value['status'])


if __name__=='__main__':main()
