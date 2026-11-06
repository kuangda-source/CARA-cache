#!/usr/bin/env python3
"""Rebuild all five model CPU decisions from saved raw artifacts without SSH."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_wc_N10_models_cpu_bundle_r1 import ROLES,PASS,accept_role


def accept(value):
    launch=value['launch'];reg=value['registration']
    if (value['status']!='N10_ORIGINAL_FIVE_MODEL_CPU_ONCE_CAPTURE'
            or value['observed_unix']<launch['first_collection_not_before_unix']
            or value['registration_sha256']!=launch['registration_sha256']
            or reg['purpose']!='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING'
            or reg['source_revision']!=launch['source_revision'] or reg['roles']!=list(ROLES)
            or set(value['payload_verified'])!=set(reg['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Original source/clock/all CPU payload must be accepted')
    if value['original_process_alive']:
        return dict(status='N10_ORIGINAL_MODEL_CPU_STILL_RUNNING_REESTIMATE_ONCE',CPU_accepted=False,
                    completed_role_files=value['role_result_files_present'],GPU_submissions=0)
    files=value['files'];bundle=files['CPU-model-bundle-result.json'].get('data')
    if bundle is None:
        return dict(status='N10_ORIGINAL_MODEL_CPU_TERMINAL_NO_BUNDLE_RETAINED',CPU_accepted=False,
                    registered_model_denominator=5,GPU_submissions=0)
    if (bundle['registered_roles']!=list(ROLES) or bundle['role_denominator']!=5
            or bundle['attempted_role_slots']!=5 or len(bundle['rows'])!=5
            or [r['role'] for r in bundle['rows']]!=list(ROLES)
            or bundle['source_revision']!=launch['source_revision']
            or bundle['registration_sha256']!=launch['registration_sha256']):
        raise ValueError('Preserve every original CPU model slot and source')
    resources=files['model-resources.json']['data']['resources'];rows=[]
    for role,original in zip(ROLES,bundle['rows']):
        saved=files['CPU-model-'+role+'.json'];row=dict(role=role,status='CPU_ROLE_NOT_ACCEPTED')
        try:
            if (original['exit_code']!=0 or not saved['exists'] or 'data' not in saved
                    or original['result_sha256']!=saved['sha256'] or original.get('data')!=saved['data']):
                raise ValueError('Original independent per-model file or process failed')
            row['proof']=accept_role(role,saved['data'],reg,value['registration_sha256'],resources)
            row['status']='CPU_ROLE_ACCEPTED'
        except Exception as error:row.update(error_type=type(error).__name__,error=str(error))
        rows.append(row)
    accepted=all(r['status']=='CPU_ROLE_ACCEPTED' for r in rows)
    if accepted and (bundle['status']!=PASS or bundle['exit_code']!=0 or bundle['accepted_roles']!=5):
        raise ValueError('Original whole-model result disagrees with independent raw proofs')
    return dict(status='N10_ALL_FIVE_MODEL_CPU_INDEPENDENTLY_ACCEPTED_NOT_QUALITY' if accepted
                else 'N10_ORIGINAL_MODEL_CPU_FAILURES_RETAINED_ALL_FIVE',CPU_accepted=accepted,
        source_revision=launch['source_revision'],registration_sha256=value['registration_sha256'],
        registered_model_denominator=5,accepted_models=sum(r['status']=='CPU_ROLE_ACCEPTED' for r in rows),
        rows=rows,CPU_wall_seconds=bundle['wall_seconds'],paper_quality_scores_generated=False,
        final_videos_read=False,GPU_submissions=0,ledger_written=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    raw=a.capture.read_bytes();result=accept(json.loads(gzip.decompress(raw)))
    result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
    result['independent_acceptor_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
