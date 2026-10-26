"""Actual dual-host affected entry, full128 orchestration and original quality models.
This proof does not claim a GPU supervisor/financial terminal acceptance.
"""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for n in ('project','stage','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();start=time.time();sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
 assert os.environ['CUDA_VISIBLE_DEVICES']==''
 from wcomr.policy_generator_r1.dev128_card import validate,sha,read,COUNTS
 c,reg,card=validate(a.project,a.stage)
 outputs={};reuse=read(a.stage/'CPU-reuse-binding.json') if (a.stage/'CPU-reuse-binding.json').exists() else None
 for key,script in [('entry','check_cara_dev128_entry_cpu_r1.py'),('combination','check_cara_dev128_combination_cpu_r1.py')]:
  target=a.stage/(key+'-CPU.json')
  if reuse:
   frozen='CPU-reuse-'+key+'.json';assert sha(a.stage/frozen)==reuse['section_files'][frozen]
   outputs[key]=read(a.stage/frozen);continue
  subprocess.run([sys.executable,str(a.stage/'scripts'/script),'--project',str(a.project),'--stage',str(a.stage),'--output',str(target)],check=True,timeout=2400)
  outputs[key]=read(target)
 binding=read(a.stage/'quality-binding.json');qroot=Path(binding['registration']['stage']);qout=a.stage/'DEV128-quality-probe'
 env=dict(os.environ,PYTHONPATH=binding['dependency_overlay']+':'+str(a.stage/'src')+':'+str(a.stage/'scripts'))
 subprocess.run([sys.executable,str(a.stage/'scripts/score_cara_dev128_quality_cpu_r1.py'),'--binding',str(a.stage/'quality-binding.json'),'--declared-synthetic-CPU-probe','--output',str(qout)],env=env,check=True,timeout=2400)
 outputs['quality']=read(qout/'result.json')
 assert outputs['quality']['models_really_loaded']
 proof=dict(status='DEV128_DUAL_HOST_PRODUCTION_CPU_COMPLETE_NOT_GPU',host=c['host'],scope=COUNTS,source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),execution_source_sha256=reg['payload_sha256'],started_unix=start,ended_unix=time.time(),outputs=outputs,reuse=reuse,
  quote=read(a.stage/'manifests/cara_DEV128_dual_host_whole_quote_r1_20261026.json'),GPU_submissions=0,ledger_written=False,CUDA_initialized=False,new_DEV_inference_executed=False,
  GPU_supervisor_financial_terminal_CPU_accepted=False)
 with a.output.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=proof['status'],host=c['host'],wall_seconds=time.time()-start)))
if __name__=='__main__':main()
