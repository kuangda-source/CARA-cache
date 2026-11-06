#!/usr/bin/env python3
"""Release the sequential cost card only after independently captured main evidence.

No scoring, GPU dispatch, resource reservation, or alteration of old receipts.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    refs=['reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json',
          'reports/wc_ra_plus_a_score_cpu_r1_terminal_20261010_capture_and_independent_audit.json']
    evidence=[json.loads(Path(n).read_text()) for n in refs]
    primary,score=evidence
    assert primary['independent_checks']['success'] and score['independent_checks']['success']
    assert primary['GPU_exit_code']==primary['CPU_exit_code']==score['exit_code']==0
    assert primary['planned_scope']['complete_paths']==32
    assert score['independent_checks']['original_28_paths_four_reference_slots_and_32_costs_verified']
    assert score['independent_checks']['all_ten_registered_contrasts_independently_reconstructed']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    for name in refs:
        assert Path(name).read_bytes()==subprocess.check_output(['git','show',revision+':'+name])
    sequence=json.loads(Path('reports/wc_action_cost_real_r1_sequence_launch_20261010.json').read_text())
    mainroot='outputs/wc-ra-plus-a-full-video-r1'
    rawroot='.sync/wc-ra-plus-a-post-cpu-r1-20261010'
    scoreroot='.sync/wc-ra-plus-a-score-cpu-r1-20261010'
    accepted={'status':'ORIGINAL_COMPLETE32_INDEPENDENT_GPU_RAW_AND_ALL93_CAPTURE_ACCEPTED',
              'main_source_revision':primary['source_revision'],
              'score_source_revision':score['source_revision'],
              'independent_evidence_commit':revision,
              'local_evidence_sha256':{n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in refs},
              'remote_receipt_sha256':{
                  mainroot+'/supervisor.json':primary['files']['supervisor']['sha256'],
                  mainroot+'/diagnostic/receipt.json':primary['files']['runner']['sha256'],
                  rawroot+'/receipt.json':primary['files']['CPU_receipt']['sha256'],
                  rawroot+'/result.json':primary['files']['CPU_result']['sha256'],
                  scoreroot+'/receipt.json':score['files']['receipt']['sha256'],
                  scoreroot+'/result.json':score['files']['result']['sha256']},
              'planned_paths':32,'scientific_win_is_not_required':True,
              'GPU_submissions_by_acceptance':0,'ledger_written':False,'observed_unix':time.time()}
    local=Path('reports/wc_ra_plus_a_r1_independent_acceptance_for_next_card_20261010.json')
    assert not local.exists()
    code='P='+repr(accepted)+'\nS='+repr(sequence)+'\n'+r'''
import hashlib,json,pathlib
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');post=pathlib.Path(S['sequence_stage'])
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in P['remote_receipt_sha256'].items())
queue=json.loads((post/'receipt.json').read_text())
assert queue['pid']==S['sequence_pid'] and queue['GPU_submissions']==0
assert queue['status']=='WAITING_ORIGINAL_MAIN_INDEPENDENT_CAPTURE_NOT_GPU'
target=post/'main-independent-acceptance.json';assert not target.exists()
with target.open('x') as f:f.write(json.dumps(P,indent=2)+'\n')
print(json.dumps({'written':str(target),'GPU_submissions':0,'ledger_written':False}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=40)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    accepted['server_write_receipt']=json.loads(call.stdout)
    local.write_text(json.dumps(accepted,indent=2)+'\n')
    print(json.dumps(accepted['server_write_receipt']))


if __name__=='__main__':main()
