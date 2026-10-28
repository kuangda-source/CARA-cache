"""Bounded offline S/Q work on original B1 tensors. No model replay/download."""
import argparse
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import torch
from wcomr.sq_codec_r1 import encode_pair, transform_roundtrip, storage_bytes
from wcomr.sq_risk_r1 import branch_moments, coverage, aggregate, exchanges
from wcomr.policy_interval_readout_r1 import guided
from wcomr.scout_readout_v22 import PARENT_FINGERPRINT


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def metric(a,b):
    total=0.;maximum=0.;n=0
    # Bound FP64 temporaries even for the full hidden feature tensor.
    x,y=a.reshape(-1),b.reshape(-1)
    for lo in range(0,a.numel(),1024**2):
        e=x[lo:lo+1024**2].double()-y[lo:lo+1024**2].double()
        total+=float(e.square().sum());maximum=max(maximum,float(e.abs().max()));n+=e.numel()
    return dict(MSE=total/n,max_abs=maximum)


def describe(value):
    if isinstance(value,torch.Tensor):return dict(shape=list(value.shape),dtype=str(value.dtype),bytes=value.numel()*value.element_size())
    if isinstance(value,dict):return {str(k):describe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [describe(v) for v in value]
    if value is None or isinstance(value,(bool,int,float,str)):return value
    raise ValueError('Unregistered saved object')


def run(assets,expected):
    assert sha(assets/'manifest.json')==expected
    manifest=json.loads((assets/'manifest.json').read_text())
    refs=manifest['unique_anchors']+[r['artifact'] for r in manifest['states']]
    assert len(refs)==32 and len({r['name'] for r in refs})==32
    start=time.monotonic();verified=[]
    for ref in refs:
        p=assets/ref['name']
        assert p.resolve().parent==assets.resolve() and not p.is_symlink()
        assert p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256']
        verified.append(ref)
        print(json.dumps(dict(phase='hash',completed=len(verified),total=32)),flush=True)
    hash_wall=time.monotonic()-start
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_sq_preparation_r1'))
    assert result.wasSuccessful(),stream.getvalue()
    source_test=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),log=stream.getvalue(),
                     pinned_source_C_warp_RF=True,head='DECLARED_NONLINEAR_SMALL_TENSOR_FIXTURE',real_model=False)
    rows=[];schema=None;windows=[]
    prompts=sorted({r['prompt'] for r in manifest['states']})
    for row in manifest['states']:
        v=torch.load(assets/row['artifact']['name'],map_location='cpu',weights_only=True,mmap=True)
        assert v['context'][0]==row['prompt'] and v['context'][-1]==PARENT_FINGERPRINT
        assert all(v[k] for k in ('P0_actual_dense','P1_dense_head_RF_equal','P2_C_actual_parent_equal'))
        pair=v['readouts']['WC_C']['outputs'];teacher=v['teacher']
        moments=branch_moments(pair,teacher)
        canonical=float((guided(pair).double()-guided(teacher).double()).square().mean())
        assert abs(canonical-v['summary']['WC_C']['MSE'])<1e-12
        record=dict(prompt=row['prompt'],parent='Shared25-C',parent_fingerprint=PARENT_FINGERPRINT,
                    step=row['step'],xi=v['xi'],source_anchor_steps=v['source_anchor_steps'],
                    moments=moments,canonical_FP32_guided_MSE=canonical,
                    canonical_vs_FP64_abs_difference=abs(canonical-moments['CFG']),
                    artifact=row['artifact'])
        refs2=v['anchors']
        assert len(refs2)==2 and all(len(p)==2 for p in refs2)
        for c,u in zip(*refs2):
            # Corresponding branch files must have the same prompt and step.
            assert c['name'].split('_0_')[-1]==u['name'].split('_1_')[-1]
        windows.append(dict(prompt=row['prompt'],step=row['step'],
                            branch_anchor_refs=refs2,consumed_window_slots_per_branch=2,
                            source='SOURCE_BOUND_REPLAY_VIEW',full_runtime_window_captured=False,
                            uncompressed_current_bytes=storage_bytes(v['current']),
                            uncompressed_pair_input_bytes=storage_bytes(v['pair_inputs'])))
        if schema is None:
            schema=describe(v)
            # Keep metadata compact: repeated scalar result tables are in old receipts.
            for k in ('gain_moments','summary','innovation_gain','readouts'):
                schema.pop(k,None)
        rows.append(record);del v;gc.collect()
        print(json.dumps(dict(phase='S_local_moments',completed=len(rows),total=12)),flush=True)
    audit=coverage(rows,prompts,('Shared25-C','F19-C'))
    try:
        aggregate(rows,prompts=prompts,parent_weights={'Shared25-C':.5,'F19-C':.5},propagation={t:1. for t in range(8,36) if t!=24})
    except ValueError as e:
        refusal=str(e)
    else:raise AssertionError('Incomplete assets generated a full S risk table')
    structural=exchanges(max_age=6,supports_history=lambda *h:True)
    witnessed={(r['step'],*r['source_anchor_steps']) for r in rows}
    supported=exchanges(max_age=6,supports_history=lambda *h:h in witnessed)
    assert not supported
    pairs={}
    for ref in manifest['unique_anchors']:
        name=ref['name'];prefix,branch,step=name.removesuffix('.pt').rsplit('_',2)
        pairs.setdefault((prefix,int(step)),{})[int(branch)]=ref
    codecs=[];transform=[];anchor_schema=[]
    for identity,refs2 in sorted(pairs.items()):
        assert set(refs2)=={0,1}
        anchors=[torch.load(assets/refs2[b]['name'],map_location='cpu',weights_only=True,mmap=True) for b in (0,1)]
        assert anchors[0]['context']==anchors[1]['context'] and [a['branch'] for a in anchors]==[0,1]
        assert anchors[0]['step']==anchors[1]['step']==identity[1]
        c,u=(a['residual'] for a in anchors)
        rt=transform_roundtrip(c,u)
        transform.append(dict(prompt=anchors[0]['context'][0],step=identity[1],errors=[metric(x,y) for x,y in zip(rt,(c,u))]))
        del rt
        anchor_schema.append(dict(prompt=anchors[0]['context'][0],step=identity[1],
                                  residual=describe(c),probe=describe(anchors[0]['probe']),
                                  branch_pair_raw_r_unique_bytes=storage_bytes((c,u)),
                                  branch_pair_p_unique_bytes=storage_bytes([a['probe'] for a in anchors])))
        for basis in ('I','M'):
            for bits in ((8,8),(4,8),(8,4)):
                start=time.monotonic();p=encode_pair(c,u,basis=basis,bits=bits);encode_seconds=time.monotonic()-start
                start=time.monotonic();decoded=p.decode();decode_seconds=time.monotonic()-start
                item=dict(prompt=anchors[0]['context'][0],step=identity[1],basis=basis,bits=list(bits),
                          rate='R16' if sum(bits)==16 else 'R12',packed=p.info(),
                          raw_r_bytes=storage_bytes((c,u)),raw_reconstruction=[metric(x,y) for x,y in zip(decoded,(c,u))],
                          packed_sha256=hashlib.sha256(p.wire).hexdigest(),encode_CPU_wall_seconds=encode_seconds,
                          decode_CPU_wall_seconds=decode_seconds,actual_C_output_measured=False)
                codecs.append(item);del p,decoded;gc.collect()
        by_rate={}
        for r in codecs[-6:]:by_rate.setdefault(r['rate'],set()).add(r['packed']['actual_bytes'])
        assert all(len(s)==1 for s in by_rate.values()),'I/M and bit directions must have identical actual bytes'
        del anchors,c,u;gc.collect()
        print(json.dumps(dict(phase='Q_packed_anchor_pair',completed=len(transform),total=len(pairs))),flush=True)
    return dict(status='SQ_B1_CPU_PREPARATION_COMPLETE_NOT_GPU_READY',manifest_sha256=expected,
                original_asset_bytes=manifest['written_bytes'],verified=verified,hash_wall_seconds=hash_wall,
                source_bound_small_tensor=source_test,S=dict(local_rows=rows,coverage=audit,plan_refusal=refusal,
                    generated_S_mask=None,structural_candidates=len(structural),fully_witnessed_candidates=len(supported),
                    fixed_max_age=6,propagation='g=1_common_no_fitted_propagation',
                    production_candidate_support_accepted=False),
                Q=dict(codecs=codecs,transform_roundtrip=transform,anchor_schema=anchor_schema,windows=windows,
                    same_bytes_all_pairs=True,actual_model_C_replay=False,global_direction_selected=False,
                    persistent_deployment_bytes=None,peak_allocated=None,peak_reserved=None,clean_speed=None,
                    full_runtime_window_gap='Pinned runtime retains three slots; B1 stores two used anchors, no stale first slot',
                    full_denominator_gap='Actual WC fields, aliases, stale window slot, p and solver require runtime inventory'),
                saved_state_schema=schema,CUDA_initialized=torch.cuda.is_initialized(),new_GPU_submissions=0,
                new_GPUh=0,ledger_writes=0,scientific_benefit_established=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.environ.get('NVIDIA_VISIBLE_DEVICES')=='void'
    def forbid(*a,**kw):raise RuntimeError('GPU and network model downloads forbidden in CPU preparation')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid;torch.set_num_threads(2)
    os.nice(10)
    start=time.monotonic();cpu=time.process_time();result=run(a.assets,a.manifest_sha256)
    assert not torch.cuda.is_initialized()
    result.update(CPU_wall_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-cpu,
                  peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  process_io=Path('/proc/self/io').read_text(),observed_unix=time.time(),torch_version=torch.__version__)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'],flush=True)


if __name__=='__main__':main()
