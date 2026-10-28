"""Check the new physical S composition, hiding GPUs and forbidding weights."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'scripts')]


def actual_decode_control(host):
    """Exercise the production adapter's default decoder on a synthetic MP4."""
    from test_sq_s_physical_r1 import Base, IDENTITY
    from wcomr.sq_s_physical_r1 import PhysicalRequests, make_physical_scope
    video=ROOT/'CPU-synthetic-black93.mp4'
    subprocess.run(['ffmpeg','-v','error','-n','-threads','1','-filter_threads','1',
        '-f','lavfi','-i','color=c=black:s=768x432:r=16','-frames:v','93','-an',
        '-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
    base=Base(lambda s,r:r.update(encoded_video=dict(path=str(video))))
    physical=make_physical_scope(base.scope,host,IDENTITY)
    entry=PhysicalRequests(base,physical,IDENTITY)
    row=entry(base.scope['slots'][0],ROOT/'CPU_DECODE_ONLY_NO_PARENT_PATH')
    expected=hashlib.sha256();frame=bytes(432*768*3)
    for _ in range(93):expected.update(frame)
    assert row['RGB']==dict(frames=93,sha256=expected.hexdigest())
    assert row['CPU_decode_fixture'] is False
    return dict(status='PASS',frames=93,HWC=[432,768,3],production_default_decoder=True,
        actual_full_parent_sampling=False,synthetic_video=True,Cosmos_generated_video=False,
        RGB_sha256=expected.hexdigest(),encoded_bytes=video.stat().st_size)


def main():
    p=argparse.ArgumentParser()
    for name in ('assets','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile','scope','manifest-sha256'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain the original physical S CPU evidence')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('All GPUs must be hidden for the CPU composition')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    original_load=torch.load
    def forbidden(*a,**kw):raise RuntimeError('Physical S CPU cannot initialize CUDA, load weights or download')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    torch.set_num_threads(2);os.nice(10)
    runtime=ROOT/'cache/runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('CPU S refuses Triton execution: '+name)
    triton.runtime.driver.active=Driver()
    import transformers.utils as transformer_utils
    from transformers.utils import import_utils
    saved=(transformer_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    transformer_utils.is_flash_attn_2_available=import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:
        transformer_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=saved
    import test_sq_s_physical_r1 as units
    log=io.StringIO()
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(units))
    scope=json.loads((ROOT/args.scope).read_text());expected=scope['hosts'][args.profile]
    if not tests.wasSuccessful() or tests.testsRun!=scope['unit_controls'] or tests.skipped:
        raise ValueError('Physical S controls failed: '+log.getvalue())
    decode=actual_decode_control(args.profile)
    retained=json.loads((ROOT/scope['retained_CPU_fixture_ref']).read_text())
    if args.profile=='two_card':
        registration=json.loads((ROOT/'registration.json').read_text())
        if retained['base']['stage']!=registration['base']['stage']:
            raise ValueError('Use the original accepted tiny OFF fixture stage')
    artifacts=ROOT/'S-physical-CPU-artifacts';loads=[]
    def tiny_loader(path,**kwargs):
        path=Path(path)
        if (path.is_symlink() or not path.resolve().is_relative_to(artifacts.resolve())
                or path.parent.name!='streaming' or path.stat().st_size>8*2**20
                or not path.name.startswith(('anchor-','state-')) or path.suffix!='.pt'
                or kwargs!={'map_location':'cpu','weights_only':True}):
            raise ValueError('Only this stage\'s tiny streaming output may be loaded')
        loads.append(path.name)
        return original_load(path,**kwargs)
    from check_sq_s_physical_cpu_r1 import run
    fixture=run(runtime,artifacts,tiny_loader,args.profile,retained)
    rows=fixture['checks']
    if len(rows)!=2 or {r['flow'] for r in rows}!={False,True} or len(loads)!=80 or torch.cuda.is_initialized():
        raise ValueError('Both complete physical flow matrices and80 tiny loads required')
    for row in rows:
        if (row['status']!='PASS' or row['physical_counts']!=expected['counts_per_flow']
                or row['complete_new_CPU_paths']!=expected['counts_per_flow']['new_paths']
                or row['logical_paths']!=10 or len(row['OFF_ON_controls'])!=4
                or row['observed_head_forward_calls']!=expected['counts_per_flow']['branch_readouts']
                or row['observed_deep_block_calls']!=expected['counts_per_flow']['deep_block_calls']
                or row['reload_audit']['files_SHA_and_bytes_reloaded']!=140
                or not row['exact_full36_guided_final_latent_and_CPU_RGB_witness']):
            raise ValueError('Physical S complete cohort or actual forward counts differ')
    children=resource.getrusage(resource.RUSAGE_CHILDREN)
    result=dict(status='S_PHYSICAL_MATRIX_CPU_PASS_NOT_GPU_OR_SCIENTIFIC_ACCEPTANCE',profile=args.profile,
        scope=scope,rows=rows,upstream_sha256=fixture['upstream_sha256'],
        actual_synthetic93_MP4_decode_control=decode,
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        reaped_child_CPU_seconds=children.ru_utime+children.ru_stime,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        unit_controls=dict(tests=tests.testsRun,skipped=len(tests.skipped),log=log.getvalue()),
        tiny_tensor_files_loaded=len(loads),actual_Cosmos_weights=False,real_generated_video=False,
        model_weight_loads_forbidden=True,CUDA_initialized=False,S_labels_collected=0,
        real_OFF_ON_equivalence_accepted=False,complete_S_GPU_card_accepted=False,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
