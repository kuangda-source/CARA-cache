"""Fixed 48-group delta over both current hosts and the retired two-card outputs.
Read identities and hashes only. No outcomes, inference, GPU or ledger writes.
"""
import argparse,json,time,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from audit_cara_new_pool_delta_r1 import audit,sha
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
import os,json,sys,hashlib,pathlib,time
p=json.load(sys.stdin);assert hashlib.sha256(p['module'].encode()).hexdigest()==p['module_sha256'];os.nice(10)
ns={};exec(compile(p['module'],'FROZEN_IDENTITY_AUDIT','exec'),ns)
rows=[]
for root in p['roots']:
 v=ns['collect_outputs'](root,p['records']);v['requested_root']=root;v['resolved_root']=str(pathlib.Path(root).resolve());rows.append(v)
print(json.dumps(dict(host=p['host'],observed_unix=time.time(),roots=rows)))
'''
def reader(payload):
 configs=[('four_card',four_ssh,['/data20t/gaokuangda/worldcache_workspace']),('two_card',ssh,['/data20t/gaokuangda/worldcache_workspace','/home/gaokuangda/data/gkd/worldcache_omr'])]
 with ThreadPoolExecutor(2) as ex:
  futures=[ex.submit(f,CODE,dict(payload,host=h,roots=roots),timeout=600) for h,f,roots in configs]
  hosts=[f.result() for f in futures]
 out=dict(hosts=hosts,identity_hits={},documents=[],read_errors=[])
 for host in hosts:
  for root in host['roots']:
   out['documents'] += [dict(d,path=host['host']+':'+d['path']) for d in root['documents']]
   out['read_errors'] += [dict(e,host=host['host'],requested_root=root['requested_root']) for e in root['read_errors']]
   for name,hits in root['identity_hits'].items():out['identity_hits'].setdefault(name,[]).extend([dict(h,host=host['host']) for h in hits])
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists()
 v=audit(remote_reader=reader,prior_delta='reports/cara_new_input_pool48_delta_r1_20261025.json')
 v['limits']=[x for x in v['limits'] if 'two-card' not in x.lower() and 'two_card' not in x.lower()]
 v.update(dual_host_script_sha256=sha(Path(__file__).read_bytes()),coverage='Local registered metadata + four-card current outputs + two-card current and historical outputs; no claim about unknown external storage')
 a.output.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v[k] for k in ('status','scoped_no_execution_evidence','local_blockers','local_read_errors','protected_remote_hits')}));print(json.dumps(v['remote']['read_errors']))
 if not v['scoped_no_execution_evidence']:raise SystemExit(2)
