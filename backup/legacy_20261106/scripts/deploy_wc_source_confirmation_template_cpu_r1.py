"""CPU-only full50 production template from accepted seed-aware240 core."""
import hashlib,io,json,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
CPU=SERVER+'/.sync/wc-source-conditional-confirmation-cpu-r1-20261013'
STAGE=SERVER+'/.sync/wc-source-confirmation-production-template-r1-20261013'
CONFIG='configs/wc_source_conditional_confirmation_full50_production_template_r1_20261013.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def remote(code):
    compile(code,'confirmation-template-CPU-remote','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def main():
    c=json.loads((ROOT/CONFIG).read_text());assert not c['candidate_frozen'] and c['template_production_CPU_only']
    manifest=json.loads((ROOT/c['input_manifest_ref']).read_text())
    names=[CONFIG,'src/wcomr/source_conditional_confirmation_production_template_r1.py',
        'scripts/run_wc_source_conditional_confirmation_template_r1.py',
        'scripts/supervise_wc_source_conditional_confirmation_template_r1.py',c['authority_ref']]
    names+=[c[key+'_ref'] for key in ('cost','previous_parameters','input_manifest','input_protocol','input_audit','matrix_template')]
    for item in c['table_parameters'].values():
        names.append(item['ref']);names+=list(json.loads((ROOT/item['ref']).read_text())['sources'])
    names+=list(json.loads((ROOT/c['previous_parameters_ref']).read_text())['sources'])
    names+=[source['path'] for source in manifest['selected_sources']]
    names=list(dict.fromkeys(names));packet={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'new_payload':{name:sha(ROOT/name) for name in names}}
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for name in names:archive.add(ROOT/name,arcname=name)
    code='CPU='+repr(CPU)+'\nSTAGE='+repr(STAGE)+'\n'+r'''import pathlib,json,hashlib,shutil
cpu=pathlib.Path(CPU);stage=pathlib.Path(STAGE);assert not stage.exists()
result=json.loads((cpu/'CPU-result.json').read_text());reg=json.loads((cpu/'registration.json').read_text())
assert result['status']=='SOURCE_CONFIRMATION_TWO_FLOW_ALL80_AUDIT80_LEAN80_LEGACY_SEED17_43_CPU_PASS_NOT_GPU'
assert result['actual_CPU_paths']==240 and not result['CUDA_initialized'] and not result['GPU_submissions']
stage.mkdir()
for name,digest in reg['payload_sha256'].items():
 source=cpu/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
shutil.copyfile(cpu/'CPU-result.json',stage/'sampling-CPU-result.json')
shutil.copyfile(cpu/'registration.json',stage/'sampling-CPU-registration.json')
print(json.dumps({'status':'CONFIRMATION_CORE240_COPIED_TEMPLATE_NOT_GPU','payload_files':len(reg['payload_sha256'])}))
'''
    print(remote(code).strip());subprocess.run(HOST+['tar -xzf - -C '+STAGE],input=buffer.getvalue(),check=True)
    code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'sampling-CPU-registration.json').read_text())
reg['source_revision']=P['source_revision'];reg['new_payload_sha256']=P['new_payload']
for name,digest in P['new_payload'].items():
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
 if name in reg['payload_sha256']:assert reg['payload_sha256'][name]==digest
 reg['payload_sha256'][name]=digest
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_source_conditional_confirmation_template_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
receipt={'status':'SOURCE_CONFIRMATION_PRODUCTION_TEMPLATE_CPU_STARTED_NOT_GPU','pid':child.pid,'command':command,'stage':str(stage),
 'source_revision':P['source_revision'],'new_payload_sha256':P['new_payload'],'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}
print(json.dumps(receipt))
'''
    receipt=json.loads(remote(code));(ROOT/'reports/wc_source_confirmation_template_r1_production_cpu_launch_20261013.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({key:receipt[key] for key in ('status','pid','source_revision','GPU_submissions')}))


if __name__=='__main__':main()
