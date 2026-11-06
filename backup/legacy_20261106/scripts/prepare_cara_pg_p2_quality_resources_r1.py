#!/usr/bin/env python3
"""Prepare exact original five-model resources locally; no server or GPU writes.

Missing resources remain in the complete denominator. The packet is staging
material, not a replacement for the four-card actual-model CPU acceptance.
"""
import argparse,hashlib,json,subprocess,sys,time,zipfile,email
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.automatic_quality_models_r1 import ROLES,WEIGHTS,BPE_SHA,MUSIQ_SOURCE_SHA
from wcomr.immutable_stage_payload_r1 import local_python_closure
from wcomr.policy_generator_r1.continuation_preparation import require


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def prepare(resources_root, packet):
    require(not packet.exists(),'Preserve original resource packet')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    entries=['scripts/run_cara_pg_p2_quality_r1.py','scripts/evaluate_wc_N10_metric_model_cpu_r1.py',
             'scripts/evaluate_wc_N10_models_cpu_bundle_r1.py','scripts/accept_wc_N10_models_cpu_r1.py']
    names=set(local_python_closure(ROOT,entries))|set(entries)
    payload={}
    for n in names:
        raw=(ROOT/n).read_bytes()
        require(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)==raw,'Commit exact entry first: '+n)
        payload[n]=raw
    pack=json.loads((ROOT/'reports/wc_paper_N10_complete_pinned_code_resource_pack_20261016.json').read_text())
    for r in pack['records']:
        p=ROOT/pack['source_root']/r['path'];raw=p.read_bytes()
        require(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'Pinned VBench changed')
        payload['upstream/'+r['path']]=raw
    old=json.loads((ROOT/'reports/wc_paper_N10_existing_resource_hashes_scoped_20261016.json').read_text())['observation']
    missing=[]
    for r in old['DINO_cached_python_sources']:
        p=resources_root/'dino'/r['relative']
        if not p.is_file() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:
            missing.append('DINO_SOURCE:'+r['relative']);continue
        payload['external/dino/'+r['relative']]=p.read_bytes()
    p=ROOT/'.sync/wc-N10-official-tokenizer-pinned-r1-20261016/bpe_simple_vocab_16e6.txt.gz'
    require(sha(p)==BPE_SHA,'Pinned tokenizer changed');payload['cache/ViCLIP/'+p.name]=p.read_bytes()
    resources={}
    for role in ROLES:
        p=resources_root/(role+'.pth') if role!='ViCLIP' else ROOT/'.sync/wc-N10-viclip-direct-r4-20261017/ViClip-InternVid-10M-FLT.pth'
        size,digest=WEIGHTS[role]
        okay=p.is_file() and p.stat().st_size==size and sha(p)==digest
        resources[role]=dict(local_path=str(p.resolve()),bytes=size,sha256=digest,local_bytes_accepted=okay)
        if not okay:missing.append('WEIGHT:'+role)
    wheels=[]
    for name in ('pyiqa-0.1.10','timm-1.0.24','easydict-1.13'):
        found=list((resources_root/'wheels').glob(name+'-*.whl'))
        require(len(found)==1,'Exact independent dependency wheel required: '+name)
    for p in sorted((resources_root/'wheels').glob('*.whl')):
        with zipfile.ZipFile(p) as z:
            metadata=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
            if metadata['Name'].lower()=='pyiqa':
                require(hashlib.sha256(z.read('pyiqa/archs/musiq_arch.py')).hexdigest()==MUSIQ_SOURCE_SHA,'Original MUSIQ architecture differs')
        wheels.append(dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p),name=metadata['Name'],version=metadata['Version'],requires=metadata.get_all('Requires-Dist',[])))
    packet.mkdir()
    for n,raw in payload.items():
        target=packet/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    value=dict(status='P2_LOCAL_ORIGINAL_QUALITY_PACKET_READY_NOT_RUNTIME' if not missing else 'P2_LOCAL_QUALITY_PACKET_RESOURCE_GAPS',
        observed_unix=time.time(),source_revision=revision,source_root=str(packet.resolve()),
        official_VBench_commit=pack['official_commit'],roles=list(ROLES),
        payload_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sorted(payload.items())},resources=resources,
        isolated_overlay_wheels=wheels,missing=missing,four_card_real_model_CPU_accepted=False,
        checkpoint_bytes=sum(size for size,_ in WEIGHTS.values()),
        requires_dependency_closure_check=True,remote_files_modified=False,GPU_submissions=0,final_budget_determined=False,
        execution_constraints=dict(CUDA_visible_devices='',network='none',cpus=1,memory_GiB=8,
            minimum_free_disk_GiB=40,minimum_MemAvailable_GiB=32,base_environment_modified=False,
            active_P1_stage_modified=False,real_model_CPU_all_five_required=True))
    (packet/'packet.json').write_text(json.dumps(value,indent=2)+'\n')
    return value


def main():
    p=argparse.ArgumentParser()
    for n in ('resources-root','packet','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();value=prepare(a.resources_root,a.packet)
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({k:value[k] for k in ('status','missing','four_card_real_model_CPU_accepted','GPU_submissions')}))
if __name__=='__main__':main()
