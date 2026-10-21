#!/usr/bin/env python3
"""Fixed LPIPS assets and offline CPU validation of the unchanged four-card env.

No Cosmos weights are loaded. Only the small, explicitly registered CPU LPIPS
probe loads pretrained AlexNet/LPIPS weights; it produces no research scores.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.parse
import urllib.request


ALEX_SHA = '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
ALEX_BYTES = 244408911
LINEAR_SHA = 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
ALEX_URL = 'https://download.pytorch.org/models/alexnet-owt-7be5be79.pth'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda: stream.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def atomic(path, value):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2)+'\n');tmp.replace(path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def validate_alex(asset):
    if (asset.get('url'), asset.get('bytes'), asset.get('sha256')) != (ALEX_URL, ALEX_BYTES, ALEX_SHA):
        raise ValueError('Unregistered LPIPS backbone/source rejected')


def cache_valid(path):
    if not path.exists() and not path.is_symlink():return False
    if path.is_symlink() or not path.is_file() or path.stat().st_size != ALEX_BYTES or sha(path) != ALEX_SHA:
        raise ValueError('Existing LPIPS backbone mismatch retained')
    return True


def fetch_alex(asset, partial, opener, policy, support, progress, event,
               deadline, clock=time.time, sleeper=time.sleep):
    validate_alex(asset)
    assert not partial.is_symlink()
    if not partial.exists():partial.touch(mode=0o600, exist_ok=False)
    assert 0 <= partial.stat().st_size <= ALEX_BYTES
    with partial.open('r+b') as out:
        out.seek(0, os.SEEK_END)
        while out.tell() < ALEX_BYTES:
            start=out.tell();end=min(ALEX_BYTES-1,start+policy['chunk_bytes']-1);count=end-start+1
            for attempt in range(policy['attempts_per_chunk']):
                if clock() >= deadline:raise support.TransferError('LPIPS_RESOURCE_WALL_LIMIT')
                url=ALEX_URL+'?wc_start=%d&wc_nonce=%d'%(start,time.time_ns())
                req=urllib.request.Request(url,headers={'Range':'bytes=%d-%d'%(start,end),'Accept-Encoding':'identity'})
                try:
                    with opener.open(req,timeout=policy['socket_timeout_seconds']) as response:
                        assert response.status==206
                        assert response.headers.get('Content-Range')=='bytes %d-%d/%d'%(start,end,ALEX_BYTES)
                        assert response.headers.get('Content-Length')==str(count)
                        left=count
                        while left:
                            if clock()>=deadline:raise support.TransferError('LPIPS_RESOURCE_WALL_LIMIT')
                            block=response.read(min(1<<20,left))
                            if not block or len(block)>left:raise support.TransferError('SHORT_LPIPS_RESPONSE')
                            out.write(block);left-=len(block)
                    out.flush();os.fsync(out.fileno());progress(out.tell());break
                except Exception as error:
                    out.flush();out.truncate(start);out.seek(start);os.fsync(out.fileno())
                    info=support.error_info(error);event(dict(range_start=start,range_end=end,attempt=attempt+1,**info))
                    if info.get('http_status') in (401,403,404) or info['code']=='LPIPS_RESOURCE_WALL_LIMIT' or attempt+1==policy['attempts_per_chunk']:
                        raise support.TransferError('LPIPS_BOUNDED_DOWNLOAD_FAILED',last_error=info) from None
                    delay=support.retry_delay(error,attempt,policy,clock())
                    if clock()+delay>=deadline:raise support.TransferError('LPIPS_RESOURCE_WALL_LIMIT')
                    sleeper(delay)
    assert partial.stat().st_size==ALEX_BYTES and sha(partial)==ALEX_SHA


NETWORK_GUARD = '''import socket
def deny_network(*a,**k):raise RuntimeError('OFFLINE_CPU_NETWORK_EXECUTION_DENIED')
socket.socket.connect=deny_network
socket.socket.connect_ex=deny_network
socket.create_connection=deny_network
'''


def guarded_source(repair_source):
    tree=ast.parse(repair_source)
    values=[n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='guarded' for t in n.targets)]
    assert len(values)==1
    source=ast.literal_eval(values[0]);compile(source,'<original-guarded-CPU-import>','exec')
    return NETWORK_GUARD+source


def offline_assets_probe(assets):
    return NETWORK_GUARD+'ASSETS='+repr(assets)+'\n'+r'''
from pathlib import Path
import os,json,torch
def forbidden(*a,**k):raise RuntimeError('CPU_RESOLVER_DENIES_CUDA_AND_WEIGHT_LOADING')
torch.cuda._lazy_init=forbidden;torch.load=forbidden
from huggingface_hub import hf_hub_download
root=Path(os.environ['HF_HUB_CACHE']);resolved=[]
for a in ASSETS:
 repo=root/('models--'+a['repo_id'].replace('/','--'));blob=repo/'blobs'/a['digest']
 assert blob.is_file() and not blob.is_symlink() and blob.stat().st_size==a['size']
 for revision in a['target_revisions']:
  p=Path(hf_hub_download(a['repo_id'],a['path'],revision=revision,local_files_only=True,cache_dir=str(root)))
  assert p.resolve()==blob.resolve()
 resolved.append(dict(repo_id=a['repo_id'],path=a['path'],digest=a['digest'],size=a['size']))
from transformers import AutoTokenizer,AutoConfig
t=AutoTokenizer.from_pretrained('nvidia/Cosmos-Reason1-7B',revision='3210bec0495fdc7a8d3dbb8d58da5711eab4b423',local_files_only=True,trust_remote_code=False)
assert t.encode('A short CPU-only resource check.')
assert not torch.cuda.is_initialized()
print(json.dumps(dict(resolved_files=len(resolved),offline=True,Cosmos_weights_loaded=0,CUDA_initialized=False)))
print('FROZEN110_OFFLINE_HF_PATHS_AND_REASON_TOKENIZER_CPU_OK')
'''


LPIPS_PROBE=NETWORK_GUARD+r'''
import torch,json,lpips,importlib.metadata
from pathlib import Path
def forbidden(*a,**k):raise RuntimeError('LPIPS_CPU_DENIES_CUDA_OR_NETWORK_DOWNLOAD')
torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
torch.set_num_threads(2)
assert importlib.metadata.version('lpips')=='0.1.4'
model=lpips.LPIPS(net='alex',version='0.1',pnet_rand=False,pretrained=True,use_dropout=True,verbose=False).eval().cpu()
linear=torch.load(Path(lpips.__file__).parent/'weights/v0.1/alex.pth',map_location='cpu',weights_only=True)
assert linear and all(k in model.state_dict() and torch.equal(model.state_dict()[k],v) for k,v in linear.items())
x=torch.zeros((4,3,64,64),dtype=torch.float32);y=x.clone();y[:,:,16:48,16:48]=0.5
with torch.inference_mode():
 a=model(x,x);b=model(x,y);c=model(x,y)
assert torch.equal(a,torch.zeros_like(a)) and torch.isfinite(b).all() and (b>0).all() and torch.equal(b,c)
assert not torch.cuda.is_initialized()
print(json.dumps(dict(package_version='0.1.4',metric_version='0.1',backbone='alex',device='cpu',precision='float32',synthetic_frames=4,HWC=[64,64,3],pretrained_linear_tensors_exact=True,self_zero=True,different_positive=True,repeat_exact=True,Cosmos_weights_loaded=0,CUDA_initialized=False,real_video_scores=0)))
print('OFFICIAL_LPIPS_PRETRAINED_CPU_RESOURCE_ONLY_OK')
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    m=json.loads(a.manifest.read_text());job=a.manifest.parent;root=Path(m['workspace']);env=root/'envs/wc-cosmos-py310-cu128-r3'
    support=load('bounded_resource_support',job/'resource_support.py')
    repair=load('unchanged_repair_support',job/'repair_support.py')
    assert sha(__file__)==m['worker_sha256'] and sha(job/'resource_support.py')==m['resource_support_sha256'] and sha(job/'repair_support.py')==m['repair_support_sha256']
    assert not list(Path('/dev').glob('nvidia*'))
    assert os.environ['HF_HOME']==str(root/'cache/huggingface') and os.environ['HF_HUB_CACHE']==str(root/'cache/huggingface/hub')
    upstream=job/'upstream-assets-acceptance.json';assert sha(upstream)==m['model_assets_acceptance_sha256']
    assert json.loads(upstream.read_text())['frozen_production_model_files_accepted'] is True
    public=job/'upstream-public14-acceptance.json';assert sha(public)==m['public14_acceptance_sha256']
    assert json.loads(public.read_text())['public_auxiliary_assets_accepted'] is True
    fixed=job/'frozen96.json';assert sha(fixed)==m['fixed96_manifest_sha256']
    fixed_assets=json.loads(fixed.read_text())['assets']
    assert len(fixed_assets)==96 and sum(x['size'] for x in fixed_assets)==21358871258
    assert m['availability_assets'][:96]==fixed_assets and len(m['availability_assets'])==110
    assert len({(x['repo_id'],x['path']) for x in m['availability_assets']})==110
    assert sum(x['size'] for x in m['availability_assets'][96:])==5034332532
    with (job/'worker-once.json').open('x') as intent:
        json.dump(dict(manifest_sha256=sha(a.manifest),source_revision=m['source_revision']),intent)
    old=Path(m['previous_validation_job']);assert sha(old/'result.json')==m['previous_result_sha256'] and sha(old/'manifest.json')==m['previous_manifest_sha256']
    previous=json.loads((old/'result.json').read_text());assert previous['status']=='CPU_VALIDATION_COMPLETION_FAILED_RETAINED'
    assert previous['commands'][0]['phase']=='corrected-synthetic-CPU-video-decode' and previous['commands'][0]['exit_code']==0
    before=repair.metadata_fingerprint(env);assert before==m['environment_metadata_sha256']
    assert all(sha(root/'runtime'/k)==v for k,v in m['runtime_source_sha256'].items())
    begin=time.time();state=dict(status='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_RUNNING',started_unix=begin,source_revision=m['source_revision'],worker_sha256=sha(__file__),manifest_sha256=sha(a.manifest),commands=[],resource_error_events=0,environment_metadata_before=before,environment_modified=False,original_successful_decode_reused=True,original_components_acceptance_reused=True,full_fixed96_already_accepted=True,public14_already_accepted=True,Cosmos_weights_loaded=0,LPIPS_CPU_pretrained_weight_files_loaded=0,real_video_scores=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False,production_CPU_accepted=False,GPU_dispatch_ready=False)
    def save():state['updated_unix']=time.time();atomic(job/'health.json',state)
    def event(info):
        state['resource_error_events']+=1;state['last_resource_error']=info;save()
    try:
        state['phase']='fixed-LPIPS-official-weight-resource';save()
        torch_home=root/'cache/torch';dest=torch_home/'hub/checkpoints/alexnet-owt-7be5be79.pth';dest.parent.mkdir(parents=True,exist_ok=True)
        assert not dest.parent.is_symlink()
        existing=cache_valid(dest)
        if not existing:
            part=dest.parent/('.wc-r4-'+m['run_id']+'.partial');assert not part.exists()
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':m['anonymous_server_proxy']}),support.ScopedRedirect())
            def progress(n):state['LPIPS_durable_bytes']=n;save()
            fetch_alex(m['LPIPS_backbone'],part,opener,m['download_policy'],support,progress,event,begin+m['resource_maximum_wall_seconds'])
            assert not dest.exists();part.replace(dest)
        assert cache_valid(dest)
        linear=env/'lib/python3.10/site-packages/lpips/weights/v0.1/alex.pth';assert sha(linear)==LINEAR_SHA
        state['LPIPS_fixed_resource']=dict(backbone_sha256=sha(dest),backbone_bytes=dest.stat().st_size,linear_sha256=sha(linear),existing_backbone_reused=existing)
        def inside(label,source,marker,timeout):
            state['phase']=label;save();script=job/(label+'.py');script.write_text(source)
            start=time.time()
            with (job/(label+'.log')).open('xb') as output:
                try:r=subprocess.run([str(env/'bin/python'),str(script)],stdout=output,stderr=subprocess.STDOUT,timeout=timeout)
                except subprocess.TimeoutExpired:
                    state['commands'].append(dict(phase=label,exit_code=124,wall_seconds=time.time()-start));save();raise
            lines=(job/(label+'.log')).read_text(errors='replace').splitlines()
            item=dict(phase=label,exit_code=r.returncode,wall_seconds=time.time()-start,exact_marker=marker in lines,probe_source_sha256=sha(script))
            state['commands'].append(item);save();assert r.returncode==0 and item['exact_marker'],label
        inside('frozen110-offline-paths-tokenizer',offline_assets_probe(m['availability_assets']),'FROZEN110_OFFLINE_HF_PATHS_AND_REASON_TOKENIZER_CPU_OK',300)
        inside('unchanged-guarded-inference-import',guarded_source((job/'repair_support.py').read_text()),'FROZEN_PRODUCTION_GUARDED_INFERENCE_IMPORT_CPU_ONLY_OK',300)
        state['LPIPS_CPU_pretrained_weight_loading_attempted']=True
        state['LPIPS_CPU_pretrained_weight_files_loaded']=None
        inside('official-LPIPS-pretrained-CPU',LPIPS_PROBE,'OFFICIAL_LPIPS_PRETRAINED_CPU_RESOURCE_ONLY_OK',300)
        state['LPIPS_CPU_pretrained_weight_files_loaded']=2
        state['status']='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_COMPLETE_NOT_PRODUCTION_OR_GPU'
    except BaseException as error:
        state.update(status='R4_CPU_RESOURCE_FAILURE_RETAINED',failure=support.error_info(error))
    finally:
        state['environment_metadata_after']=repair.metadata_fingerprint(env)
        state['environment_metadata_unchanged']=state['environment_metadata_after']==before
        state['runtime_critical_sources_unchanged']=all(sha(root/'runtime'/k)==v for k,v in m['runtime_source_sha256'].items())
        state.update(ended_unix=time.time(),wall_seconds=time.time()-begin);save();atomic(job/'result.json',state)
    return 0 if state['status']=='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_COMPLETE_NOT_PRODUCTION_OR_GPU' else 1


if __name__=='__main__':raise SystemExit(main())
