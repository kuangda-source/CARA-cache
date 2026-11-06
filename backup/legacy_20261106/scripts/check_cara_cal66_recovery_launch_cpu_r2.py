#!/usr/bin/env python3
"""R2 identity/quote/source binding and real CPU lifecycle, without GPU replay."""
import argparse,hashlib,importlib.util,json,os,sys,time,unittest
from pathlib import Path

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();start=time.time();os.environ['CUDA_VISIBLE_DEVICES']=''
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import torch
 torch.set_num_threads(1);assert not torch.cuda.is_initialized()
 from wcomr.policy_generator_r1.shared66_card import RUN,VERSION,CPU_PROOF,MANIFEST,COUNTS,read,sha,execution_quote,validate
 from audit_cara_cal66_entry_cpu_r2 import accept as accept_entry
 c,reg,card=validate(a.project,a.stage)
 assert RUN=='cara-shared-cal66-ada-r2' and VERSION=='CARA_SHARED66_RECOVERY_R2'
 cap=read(a.stage/'reports/cara_CAL66_frozen_entry_CPU_progress_r3_20261025_2030.json')
 entry=accept_entry(cap)
 previous=read(a.stage/'reports/cara_CAL66_frozen_recovery_preparation_accepted_r2_20261025.json')
 assert sha(a.stage/'reports/cara_CAL66_frozen_entry_CPU_progress_r3_20261025_2030.json')==previous['repaired_entry_capture_sha256']
 combined=dict(previous['unchanged_component_source_sha256'],**previous['repaired_source_sha256'])
 identity_changes={'src/wcomr/policy_generator_r1/shared66_card.py','src/wcomr/policy_generator_r1/shared66_terminal.py'}
 assert {n for n,h in combined.items() if reg['payload_sha256'].get(n)!=h}==identity_changes
 for n in ('src/wcomr/policy_generator_r1/exploration_requests.py','src/wcomr/policy_generator_r1/frozen_request_arguments.py'):
  assert reg['payload_sha256'][n]==cap['registration']['payload_sha256'][n]
 assert reg['runtime_source_sha256']['cosmos_predict2/config.py']==cap['registration']['runtime_source_sha256']['cosmos_predict2/config.py']
 # Replay unchanged historical bridge/score/resource evidence, but never reuse
 # the historical mutable-request entry flag to clear the repaired seam.
 components=read(a.stage/'reports/cara_CAL66_complete_CPU_preparation_and_quote_20261025.json')
 binding=(a.stage/'reports/cara_CAL66_quality_binding_20261025.json').read_bytes()
 assert components['CPU_preparation_accepted'] and hashlib.sha256(binding).hexdigest()==components['binding_sha256']
 suite=unittest.defaultTestLoader.loadTestsFromModule(load(a.stage/'tests/test_cara_shared66_combination_r1.py','terminal'))
 tests=unittest.TextTestRunner(verbosity=1).run(suite);assert tests.wasSuccessful()
 life=load(a.stage/'tests/check_cara_shared66_lifecycle_cpu_r1.py','life').run(a.stage,a.stage/'CPU-R2-lifecycle')
 storage=load(a.stage/'tests/check_shared66_storage_cpu_r1.py','storage').run(a.stage,a.stage/'CPU-R2-storage')
 assert not torch.cuda.is_initialized()
 proof=dict(status='CAL66_R2_IDENTITY_QUOTE_LIFECYCLE_CPU_COMPLETE',source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),
  started_unix=start,ended_unix=time.time(),run_id=RUN,scope_counts=COUNTS,repaired_entry=entry,
  previous_preparation_sha256=sha(a.stage/'reports/cara_CAL66_frozen_recovery_preparation_accepted_r2_20261025.json'),
  unchanged_execution_files=len(combined)-len(identity_changes),identity_adaptations=sorted(identity_changes),
  actual_registered_stage_validate=True,actual_runtime_class_SHA_preserved=True,original_scientific_manifest_SHA=sha(a.stage/MANIFEST),
  execution_quote=execution_quote(card),quality_binding_sha256=hashlib.sha256(binding).hexdigest(),
  reused_component_sources=components['source_receipts'],historical_bridge_and_score_CPU_reused=True,
  lifecycle=life,storage_lifecycle=storage,terminal_tests=tests.testsRun,
  real_quality_models_CPU_accepted=True,post_CPU_planning=components['CPU_planning'],
  CUDA_initialized=False,GPU_submissions=0,authoritative_ledger_written=False)
 with a.output.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=proof['ended_unix']-start)))

if __name__=='__main__':main()
