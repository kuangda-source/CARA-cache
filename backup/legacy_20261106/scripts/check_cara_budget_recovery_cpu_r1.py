"""Bounded CPU recovery tests and copied original production endpoint replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time
import unittest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--host',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();signal.alarm(120);started=time.time()
    assert not args.output.exists()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'tests')]
    from wcomr.cara_budget_rgb_objective_r1 import file_sha
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.cara_budget_endpoint_recovery_r1 import recover_complete_cpu_query
    from wcomr.cara_fast_binding_r2 import load_card
    reg=read_record(args.stage/'registration.json')
    assert reg['host']==args.host and os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(file_sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(file_sha(args.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
    suite=unittest.defaultTestLoader.discover(str(args.stage/'tests'),pattern='test_cara_budget_endpoint_recovery_r1.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun==9 and not result.skipped
    original=Path(reg['original_endpoint_stage'])
    assert file_sha(original/'registration.json')==reg['base_registration_sha256']
    original_proof=read_record(original/'CPU-proof.json')
    assert original_proof['numeric']['budget_component_unit_controls']==31
    card=load_card(args.stage,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    def hashes(root):return {str(p.relative_to(root)):file_sha(p) for p in root.rglob('*') if p.is_file()}
    actual=[]
    for p in sorted((original/'CPU-numeric').rglob('binding.json')):
        binding=read_record(p)
        if 'evaluator_source_sha256' not in binding or p.parent.name not in ('ON','OFF'):continue
        endpoint=p.parent;journal=endpoint.parent/('journal-'+str(binding['timing_enabled']))
        before=dict(endpoint=hashes(endpoint),journal=hashes(journal))
        copied=args.stage/'CPU-recovery'/str(len(actual));copied.mkdir(parents=True)
        shutil.copytree(endpoint,copied/'endpoint');shutil.copytree(journal,copied/'journal')
        final=copied/'journal/query-000003.return.json';expected=read_record(final)['payload']['response']
        final.unlink()  # Explicit fault only in a new private copy; original remains intact.
        recovered=recover_complete_cpu_query(copied/'journal',copied/'endpoint',card=card,
            expected_binding=read_record(journal/'binding.json'),expected_endpoint_binding=binding,query_id=3)
        assert recovered['response']==expected and recovered['new_generation_calls']==0
        after=dict(endpoint=hashes(endpoint),journal=hashes(journal));assert after==before
        second=recover_complete_cpu_query(copied/'journal',copied/'endpoint',card=card,
            expected_binding=read_record(journal/'binding.json'),expected_endpoint_binding=binding,query_id=3)
        assert not second['new_return_written'] and second['response']==expected
        actual.append(dict(original_endpoint=str(endpoint),original_journal=str(journal),
            original_hashes=before,recovered=recovered,second_call_no_write=True))
    assert len(actual)==4 and 'torch' not in sys.modules
    proof=dict(status='CPU_ORIGINAL_ENDPOINT_RECOVERY_COMPONENT_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),registration_sha256=file_sha(args.stage/'registration.json'),
        local_controls=result.testsRun,skipped_tests=0,original_production_copies=actual,
        recovered_complete_two_FIT_objectives=4,new_generation_calls=0,originals_unchanged=True,
        source_sha256=reg['payload_sha256'],original_CPU_proof_sha256=file_sha(original/'CPU-proof.json'),
        GPU_process_terminal_reader_accepted=False,whole_GPU_card_accepted=False,
        GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    signal.alarm(30)
    print(json.dumps(dict(status=proof['status'],host=args.host,controls=9,production_copies=4)),flush=True)


if __name__=='__main__':main()
