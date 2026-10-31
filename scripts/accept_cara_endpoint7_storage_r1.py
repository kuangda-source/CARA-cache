"""Accept the independent E1 volume, preserving every original experiment volume."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    packet=json.loads(args.capture.read_text());assert packet['exit_code']==0
    r=packet['result'];state=r['state'];result=state['result'];independent=r['independent_storage_observation']
    assert r['observation']['original_live'] is False and r['operator_intact'] is True
    assert state['status']==result['status']=='TWO_CARD_PRIVATE64_STORAGE_PROVISIONED_NO_GPU'
    assert state['identity']==r['launch']['identity']
    operator=subprocess.check_output(['git','show',packet['source_revision']+':scripts/provision_cara_endpoint7_storage_r1.py'],cwd=ROOT)
    assert hashlib.sha256(operator).hexdigest()==state['operator_sha256']==r['launch']['operator_sha256']
    config=result['storage_contract']
    old_ref='reports/cara_budget_successor_storage_accepted_r1_20261031.json'
    old=json.loads((ROOT/old_ref).read_text())
    assert config['run_id']=='cara-S-endpoint-seven46-r1-20261101'
    assert config['image_bytes']==64*2**30 and config['journal_bytes']==48*2**20
    assert config['minimum_output_free_bytes']==8*2**30 and config['minimum_host_free_bytes']==16*2**30
    assert state['fresh_resources']['data_free_bytes']>=80*2**30
    for field in ('output_mount','output_device','image_path','image_inode','journal_path'):
        assert config[field]!=old['storage_contract'][field],field
    original_capture=json.loads((ROOT/old['capture_ref']).read_text())['result']
    assert result['helper_sha256']==original_capture['state']['helper_sha256']==sha(ROOT/'src/wcomr/history104_storage_r2.py')
    assert result['persistence_probe_bytes']==2**20 and result['persistence_probe_removed'] is True
    assert result['persistence_probe_sha256']==hashlib.sha256(bytes(range(256))*4096).hexdigest()
    assert result['journal_pristine'] is independent['journal_pristine'] is True
    assert independent['output_children']==[]
    assert independent['image_allocated_bytes']>=config['image_bytes']
    assert independent['journal_allocated_bytes']==config['journal_bytes']
    assert independent['storage_guard']['output_available']>=60*2**30
    mount=independent['findmnt']['filesystems'];assert len(mount)==1
    assert mount[0]['fstype']=='ext4' and {'rw','nosuid','nodev','noexec'}<=set(mount[0]['options'].split(','))
    assert state['fresh_resources']['data_device']!=state['fresh_resources']['journal_device']
    assert state['started_unix']<=state['ended_unix']<=r['observed_unix']
    assert not any(result[k] for k in ('GPU_submissions','ledger_written'))
    accepted=dict(status='ENDPOINT7_PRIVATE64_STORAGE_AND_INDEPENDENT_JOURNAL_ACCEPTED_NO_GPU',observed_unix=time.time(),
        storage_contract=config,provision_sha256=independent['provision_sha256'],helper_sha256=result['helper_sha256'],
        source_revision=packet['source_revision'],operator_sha256=state['operator_sha256'],original_process=r['observation'],
        persistence_probe_bytes=2**20,persistence_probe_sha256=result['persistence_probe_sha256'],
        original_storage_ref=old_ref,original_storage_sha256=sha(ROOT/old_ref),original_storage_paths_not_reused=True,
        full93_IO_unchanged_component_ref='reports/cara_budget_private_RGB_CPU_accepted_r1_20261031.json',
        new_volume_full93_IO_remeasured=False,universal_IO_bound_established=False,
        capture_ref=str(args.capture),capture_sha256=sha(args.capture),independent_storage_observation=independent,
        GPU_submissions=0,ledger_written=False,execution_authorized=False)
    with args.output.open('x') as stream:json.dump(accepted,stream,indent=2);stream.write('\n')
    print(accepted['status'])


if __name__=='__main__':main()
