"""Accept only the saved original ended private64GiB P1 provisioning process."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.cara_source_lifecycle_p1_identity_r1 import RUN_ID
from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import PROFILE,validate_profile
from wcomr.cara_source_lifecycle_p1_identity_r1 import SCOPE_SHA256

OPERATOR='scripts/provision_cara_source_lifecycle_p1_storage_r1.py'
PROJECT=Path('/data20t/gaokuangda/worldcache_workspace')


def accept(capture_path):
    raw=Path(capture_path).read_bytes();capture=json.loads(raw);assert capture['exit_code']==0
    cap=capture['result'];state=cap['state'];result=state['result'];launch=cap['launch']
    assert cap['status']=='ORIGINAL_TWO_CARD_STORAGE_CAPTURE'
    assert cap['observation']['original_live'] is False and cap['operator_intact']
    assert state['identity']==launch['identity'] and state['status']==result['status']=='TWO_CARD_P1_PRIVATE64_STORAGE_PROVISIONED_NO_GPU'
    assert state['started_unix']<state['ended_unix']<=state['started_unix']+300
    revision=launch['source_revision'];source=subprocess.check_output(['git','show',revision+':'+OPERATOR],cwd=ROOT)
    assert launch['operator_sha256']==result['operator_sha256']==hashlib.sha256(source).hexdigest()
    config=result['storage_contract'];profile=json.loads((ROOT/PROFILE).read_bytes())
    validate_profile(profile,SCOPE_SHA256)
    assert config['run_id']==RUN_ID and config['image_bytes']==profile['storage']['output_image_bytes']==64*2**30
    assert config['journal_bytes']==profile['storage']['independent_journal_bytes']==48*2**20
    assert config['output_mount']==str(PROJECT/'outputs'/RUN_ID)
    assert config['image_path']==str(PROJECT/'.sync/storage-reservations/source-lifecycle-P1-full146-r1/output.ext4')
    assert config['journal_path']=='/home/gaokuangda/cara_control/source-lifecycle-P1-full146-r1/control.journal'
    for key in ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes'):
        assert config[key]==profile['storage'][key]
    observed=cap['independent_storage_observation'];checked=observed['storage_guard']
    assert checked['output_available']>=config['minimum_output_free_bytes']
    assert checked['host_available']>=config['minimum_host_free_bytes'] and checked['free_inodes']>=config['minimum_free_inodes']
    assert observed['journal_pristine'] and observed['output_children']==[]
    assert observed['image_allocated_bytes']>=64*2**30 and observed['journal_allocated_bytes']>=48*2**20
    assert result['persistence_probe_bytes']==2**20 and result['persistence_probe_removed']
    assert result['persistence_probe_sha256']==hashlib.sha256(bytes(range(256))*4096).hexdigest()
    assert config['shared_disk_reserve_ratio_modified'] is False and config['reboot_remount_must_be_reverified'] is True
    return dict(status='ORIGINAL_P1_PRIVATE64_STORAGE_ACCEPTED_NO_GPU',capture_ref=str(capture_path),
        capture_sha256=hashlib.sha256(raw).hexdigest(),original_identity=launch['identity'],source_revision=revision,
        operator_sha256=launch['operator_sha256'],provision_sha256=observed['provision_sha256'],storage_contract=config,
        original_process_exited=True,journal_pristine=True,output_empty=True,
        persistence_probe_bytes=result['persistence_probe_bytes'],persistence_probe_sha256=result['persistence_probe_sha256'],
        new_volume_full93_IO_remeasured=False,original_full93_IO_component_reused=True,
        P1_GPU_authorized=False,real_four_card_accessed=False,GPU_submissions=0,ledger_written=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists();result=accept(args.capture)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','original_process_exited','GPU_submissions')}))
