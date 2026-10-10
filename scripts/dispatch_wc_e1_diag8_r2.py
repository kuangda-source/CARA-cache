"""Unique scoped8 dispatch only after independently accepted actual CPU proof."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    target=root/'reports/wc_e1_diag8_gpu_r2_launch_20261011.json';assert not target.exists()
    capture=json.loads((root/'reports/wc_e1_diag8_production_cpu_r2_terminal_20261011_capture.json').read_text())
    assert capture['exit_code']==0 and capture['original_source_actual_entry_contract_and_wrapper_independently_verified']
    launch=json.loads((root/'reports/wc_e1_diag8_production_cpu_r2_launch_20261011.json').read_text())
    c=json.loads((root/'configs/wc_e1_diag8_production_r2_20261011.json').read_text())
    assert capture['source_revision']==launch['source_revision'] and c['forecast_complete_GPUh']<=8
    receipt_item=capture['files']['production-CPU-receipt.json']
    raw=gzip.decompress((root/receipt_item['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==receipt_item['sha256']
    receipt=json.loads(raw);assert receipt['exit_code']==receipt['child_exit_code']==0
    selector='scripts/select_wc_e1_diag8_r2.py'
    original=subprocess.check_output(['git','show',launch['source_revision']+':'+selector],cwd=root)
    assert hashlib.sha256(original).hexdigest()==c['payload_sha256'][selector]
    packet={'source_revision':launch['source_revision'],'stage':launch['stage'],
        'receipt_sha256':receipt_item['sha256'],'config_sha256':launch['config_sha256'],
        'selector_sha256':c['payload_sha256'][selector]}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,pathlib,subprocess
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=pathlib.Path(P['stage'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old/'production-CPU-receipt.json')==P['receipt_sha256']
assert sha(old/'e1-diag8-r2-config.json')==P['config_sha256']
assert sha(old/'scripts/select_wc_e1_diag8_r2.py')==P['selector_sha256']
selected=root/'.sync/wc-e1-diag8-selected-r2-20261011'
assert not selected.exists() and not (root/'outputs/wc-e1-cold-prefix-storage-diag8-r2').exists()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
 str(old/'scripts/select_wc_e1_diag8_r2.py'),'--project',str(root),'--CPU-stage',str(old),
 '--selected-stage',str(selected),'--source-revision',P['source_revision']]
value=subprocess.check_output(command,text=True)
print(value,end='')
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True)
    # Preserve transport failures; recover original handles before any follow-up.
    raw_path=root/'.sync/wc-e1-diag8-dispatch-r2-20261011.json';assert not raw_path.exists()
    raw_path.write_text(json.dumps({'returncode':call.returncode,'stdout':call.stdout,'stderr':call.stderr},indent=2)+'\n')
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout);assert value['source_revision']==launch['source_revision'] and value['planned_paths']==8
    target.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
