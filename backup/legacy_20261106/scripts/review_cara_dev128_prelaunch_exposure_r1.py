"""Exact metadata exemptions, retaining the unmodified broad exposure original."""
import argparse,json,hashlib
from pathlib import Path
from wcomr.policy_generator_r1.dev128_card import MANIFEST,check_card
ROOT=Path(__file__).resolve().parents[1]
def review(v):
 assert not v['local_read_errors'] and not v['remote']['read_errors'] and not v['protected_remote_hits']
 prior='reports/cara_DEV128_dual_host_exposure_20261026.json';allowed={prior,MANIFEST}
 assert {b['ref'] for b in v['local_blockers']}==allowed
 old=json.loads((ROOT/prior).read_text());assert old['scoped_no_execution_evidence'] and not old['local_blockers'] and not old['protected_remote_hits'] and old['GPU_submissions']==0 and not old['endpoint_values_exported']
 check_card(json.loads((ROOT/MANIFEST).read_text()))
 for b in v['local_blockers']:
  assert hashlib.sha256((ROOT/b['ref']).read_bytes()).hexdigest()==b['sha256']
  prefix=('$.roles.',) if b['ref']==prior else ('$.matrix[','$.DEV_members[')
  assert all(h['location'].startswith(prefix) for h in b['identity_locations'])
 v['reviewed_metadata_only_hits']=v['local_blockers'];v['local_blockers']=[]
 v.update(status='DEV128_FIRST_USE_SCOPED_CLEAR_METADATA_REVIEWED',scoped_no_execution_evidence=True,metadata_review_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),metadata_review_reason='Exact previous no-execution audit roles and immutable planned matrix; no generated results')
 return v
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 v=review(json.loads(a.capture.read_text()));v.update(raw_audit_ref=str(a.capture),raw_audit_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest());a.output.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(v['status'])
