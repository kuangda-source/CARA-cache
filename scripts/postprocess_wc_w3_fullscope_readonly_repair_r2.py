#!/usr/bin/env python3
"""Fresh CPU reader over immutable original W3 outputs; never repair a video."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for n in ('project','original-stage','repair-stage'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
 sys.path.insert(0,str(a.original_stage/'src'))
 guard_spec=importlib.util.spec_from_file_location('separate_readonly_video_guard',a.repair_stage/'src/wcomr/w3_video_failure_audit_r2.py')
 guard_module=importlib.util.module_from_spec(guard_spec);guard_spec.loader.exec_module(guard_module)
 derive_reader=guard_module.derive_reader
 reg=json.loads((a.repair_stage/'registration.json').read_text())
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert all(sha(a.repair_stage/n)==h for n,h in reg['payload_sha256'].items())
 assert sha(a.original_stage/'registration.json')==reg['original_registration_sha256']
 old=a.original_stage/'scripts/postprocess_wc_w3_label64_full864_cpu_r1.py';assert sha(old)==reg['original_post_source_sha256']
 spec=importlib.util.spec_from_file_location('immutable_original_W3_raw_post',old);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
 function,proof=derive_reader(base.main);proof.update(reader_source_revision=reg['source_revision'],original_GPU_source_revision=reg['original_GPU_source_revision'])
 destination=a.repair_stage/'CPU-final-results.json';assert not destination.exists()
 sys.argv=[str(old),'--project',str(a.project),'--stage',str(a.original_stage),'--output',str(destination)]
 start=time.time();state=dict(status='W3_FRESH_READONLY_POST_RUNNING',GPU_submissions=0,ledger_written=False,original_stage_written=False,source_revision=reg['source_revision'],started_unix=start)
 try:
  function();result=json.loads(destination.read_text())
  assert len(result['parents'])==18 and len(result['labels'])==72 and result['GPU_submissions']==0 and not result['CUDA_initialized']
  state.update(status='W3_FRESH_READONLY_POST_TERMINAL_FAILURES_RETAINED',exit_code=0,
      whole_card_scientifically_accepted=False,result_status=result['status'])
 except BaseException as error:
  state.update(status='W3_FRESH_READONLY_POST_TECH_FAILED',exit_code=1,error_type=type(error).__name__,error=str(error));raise
 finally:
  state.update(wall_seconds=time.time()-start,ended_unix=time.time(),derivation_proof=proof,result_sha256=sha(destination) if destination.exists() else None)
  out=a.repair_stage/'CPU-exit.json';assert not out.exists();out.write_text(json.dumps(state,indent=2)+'\n')
if __name__=='__main__':main()
