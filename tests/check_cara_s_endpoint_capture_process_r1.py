"""Actual Linux process identity checks with explicitly simulated Docker data."""
import copy
import json
import subprocess
import sys
import time
from unittest.mock import patch

from wcomr import cara_s_endpoint_score_capture_r1 as reader
from wcomr.cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from wcomr.cara_budget_supervisor_r1 import stop_original
from test_cara_s_endpoint_score_capture_r1 import fixture,save,timestamp


def run(root):
    args,container,out=fixture(root)
    children=[]
    try:
        for _ in range(3):
            child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)'],start_new_session=True)
            children.append((child,bind_original_process(child.pid)))
        cli,worker,foreign=children
        args['binding']['cli_identity']=cli[1]
        intent=json.loads((out/'scores-intent.json').read_text());intent['original_identity']=worker[1]
        save(out/'scores-intent.json',intent)
        result=json.loads((out/'scores.json').read_text());result['original_identity']=worker[1]
        result['started_unix']=time.time();result['ended_unix']=time.time();save(out/'scores.json',result)
        container['State'].update(StartedAt=timestamp(result['started_unix']-1),FinishedAt=timestamp(time.time()+1))
        with patch.object(reader,'inspect_original',return_value=dict(status='OBSERVED',container=container)):
            live_cli=reader.recover(**args)
            assert live_cli['status']=='ORIGINAL_SCORE_ACTIVE' and not live_cli['scientific_output_read']
            stop_original(*cli);cli[0].wait(timeout=10)
            live_worker=reader.recover(**args)
            assert live_worker['status']=='ORIGINAL_SCORE_UNKNOWN' and not live_worker['scientific_output_read']
            stop_original(*worker);worker[0].wait(timeout=10)
            complete=reader.recover(**args)
            assert complete['status']=='ORIGINAL_COMPLETE24_SCORE_ACCEPTED'
            assert complete['accepted']['new_scored_pairs']==12 and complete['accepted']['formal_logical_positions']==24
            before={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}
            repeated=reader.recover(**args)
            assert repeated['accepted']['source_rows']==complete['accepted']['source_rows']
            assert before=={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}
            unknown=copy.deepcopy(args)
            unknown['binding']['cli_identity']['host_view']['boot_id']='00000000-0000-0000-0000-000000000000'
            assert reader.recover(**unknown)['status']=='ORIGINAL_SCORE_UNKNOWN'
        assert observe_original_process(foreign[1])['original_live'] is True
        return dict(status='ACTUAL_LINUX_SCORE_RECOVERY_CPU_PASS',controls_passed=5,
            live_cli_status=live_cli['status'],live_worker_status=live_worker['status'],
            complete_status=complete['status'],repeat_read_only_acceptance=True,wrong_boot_status='ORIGINAL_SCORE_UNKNOWN',
            cli_identity=cli[1],worker_identity=worker[1],cli_observation=observe_original_process(cli[1]),
            worker_observation=observe_original_process(worker[1]),foreign_process_preserved=True,
            Docker_observations_simulated=True,score_rows_synthetic=True,metric_computations=0,
            original_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False)
    finally:
        for child,identity in children:
            if child.poll() is None:stop_original(child,identity)
            child.wait(timeout=10)
