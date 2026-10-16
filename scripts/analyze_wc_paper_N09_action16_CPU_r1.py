#!/usr/bin/env python3
"""Read all original local CPU tensors; no model, CUDA, SSH or new trial."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('capture','output'):parser.add_argument('--'+n,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve independent original CPU acceptance')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    import torch
    from wcomr.action_price16_audit_r1 import audit_scene
    from wcomr.mid_coverage import tree_digest
    torch.set_num_threads(2)
    value=json.loads(gzip.decompress(args.capture.read_bytes()));stage=args.capture.parent.resolve()
    if (value['status']!='N09_ACTION16_TWO_FLOW_FULL24_CPU_PASS_NOT_GPU_PRICES'
            or value['actual_CPU_paths']!=24 or value['state_mode_positions']!=64
            or value['total_pairs']!=1888 or value['CUDA_initialized'] or value['GPU_submissions']
            or {r['flow'] for r in value['checks']}!={False,True}):
        raise ValueError('Complete original two-flow full24 CPU evidence required')
    files=[]
    def loader(asset):
        p=Path(asset['path']).resolve();p.relative_to(stage/'artifacts')
        raw=torch.load(p,weights_only=True,map_location='cpu')
        if tree_digest(raw)!=asset['tensor_sha256']:raise ValueError('Raw original tensor tree differs')
        files.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
        return raw
    flows=[]
    for flow in value['checks']:
        if (flow['complete_CPU_paths']!=12 or len(flow['checks'])!=4 or flow['trial_pairs']!=512
                or not flow['ordinary_initial_state_restored']):raise ValueError('All original paths required')
        scenes=[]
        for scene in flow['checks']:
            if (scene['complete_CPU_paths']!=3 or not scene['all36_guided_actions_final_and_Toy_video_equal']
                    or not scene['audit_lean_all16_trial_outputs_and_paid_packets_equal']):
                raise ValueError('Full parent and repeated action parity required')
            scenes.append(audit_scene(scene['records'],loader,expected_shape=(1,2048,2,8,8)))
        flows.append(dict(flow=flow['flow'],scenes=scenes))
    assert len(files)==64 and len({r['path'] for r in files})==64 and not torch.cuda.is_initialized()
    result=dict(status='N09_ACTION16_FULL24_RAW640_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU_PRICES',
        capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),raw_files=64,raw_tensors=640,
        trial_intervals=1024,formal_intervals=768,flows=flows,artifact_identity_receipts=files,
        real_model_or_GPU_prices=False,real_video_or_speed_result=False,
        actual_Cosmos_production_CPU=False,GPU_submissions=0,SSH_queries=0,ledger_written=False)
    with args.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False)
    print(json.dumps({k:result[k] for k in ('status','raw_files','raw_tensors','trial_intervals')}))


if __name__=='__main__':main()
