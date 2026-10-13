"""Read four accepted B artifacts on CPU; never inspect the running CONF."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(a.stage/'src'))
    import torch
    torch.set_num_threads(2)
    def forbidden(*args,**kw):raise RuntimeError('Saved B reference audit forbids CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    assert not torch.cuda.is_initialized()
    from wcomr.block_saved_reference_r1 import load_reference
    from wcomr.mid_coverage import tree_digest
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    cfg=json.loads((a.stage/'configs/wc_block_velocity_suffix3_cpu_r1_20261013.json').read_text())
    assert cfg['CPU_only'] and not cfg['GPU_execution_selected'] and len(cfg['points'])==4
    source=a.project/'.sync/wc-fb-probe-cpu-r1-20261013/CPU-final-results.json'
    final=json.loads(source.read_text())
    assert final['status']=='FB_PROBE_ALL432_F16_B4_RAW_AND_LOCAL_ANALYSIS_COMPLETE_NOT_ENDPOINT'
    assert final['source_revision']=='a95b8166efd0371363bd28a1852bbddb448ec935'
    out=a.stage/'CPU-result.json';assert not out.exists();started=time.perf_counter()
    value=dict(status='FOUR_SAVED_B_REFERENCE_READONLY_CPU_AUDIT_RUNNING',rows=[],
        source_FB_final_sha256=sha(source),source_revision=reg['source_revision'],GPU_submissions=0,
        ledger_written=False,inflight_confirmation_not_observed_or_modified=True)
    try:
        for point in cfg['points']:
            old=next(p for p in final['points'] if p['scene']==point['scene'] and p['step']==point['step'])
            assert all(old[k]==v for k,v in point.items())
            ref=load_reference(point,a.project)
            value['rows'].append(dict(scene=ref['scene'],step=ref['step'],artifact_sha256=ref['artifact_sha256'],
                input_sha256=ref['input_sha256'],source_state_sha256=ref['source_state_sha256'],true_D_state_sha256=ref['true_D_state_sha256'],
                vectors={k:dict(tensor_sha256=tree_digest(v),shapes=[list(t.shape) for t in v],dtypes=[str(t.dtype) for t in v]) for k,v in ref['vectors'].items()},
                all_four_repeats_equal=True,same_registered_state=True))
            out.write_text(json.dumps(value,indent=2)+'\n')
        spec=importlib.util.spec_from_file_location('saved_B_loader_refusals',a.stage/'tests/check_block_saved_reference_cpu_r1.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        value['negative_controls']=module.run(a.stage/'CPU-tests')
        assert not torch.cuda.is_initialized()
        value.update(status='FOUR_SAVED_B_REFERENCE_ALL_IDENTITIES_SHAPES_REPEATS_AND_REFUSALS_CPU_PASS',
            CUDA_initialized=False,CPU_wall_seconds=time.perf_counter()-started,payload_sha256=reg['payload_sha256'])
        out.write_text(json.dumps(value,indent=2)+'\n')
        print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))
    except BaseException as error:
        value.update(status='SAVED_B_REFERENCE_CPU_AUDIT_FAILED',error_type=type(error).__name__,error=str(error),CUDA_initialized=torch.cuda.is_initialized())
        out.write_text(json.dumps(value,indent=2)+'\n');raise


if __name__=='__main__':main()
