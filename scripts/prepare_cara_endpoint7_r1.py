"""Build both prospective E1 scopes from original accepted local receipts."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_endpoint7_plan_r1 import build,quote
P='plans/cara_next_stage_20261101/e1/'
def read(f):return json.loads((ROOT/f).read_text())
def write(f,value):(ROOT/f).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    refs=dict(proposal='plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json',
      diagnostic='reports/cara_s_initialization_sensitivity_r1_20261031.json',
      accepted='reports/cara_budget_successor_complete_accepted_r1_20261101.json',
      frozen='plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUCCESSOR14_FROZEN_MASK_R1_20261101.json',
      capture='reports/cara_budget_successor_final_CPU_capture_r4_20261101.json',
      analysis='reports/cara_fast_B36_complete_analysis_r1_20261029.json')
    values={k:read(v) for k,v in refs.items()}
    for key,field in [('accepted','accepted'),('frozen','frozen')]:
        raw=(ROOT/refs[key]).read_bytes(); captured=values['capture']['result'][field]
        assert raw==captured['raw_utf8'].encode() and hashlib.sha256(raw).hexdigest()==captured['sha256']
    assert hashlib.sha256((ROOT/refs['frozen']).read_bytes()).hexdigest()=='f1e0b08b9dc31fd9cd3c02a80b01cbb874e9348003ec6aad3a5aa9f82d848c86'
    base=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    slowest=max(t['T_request'] for r in values['analysis']['per_member'] if r['role']=='NATIVE35' for t in r['timing_samples'])
    for same in (False,True):
        card=build(base,values['proposal'],values['diagnostic'],values['accepted'],values['frozen'],same_batch_f19=same)
        count=len(card['physical_matrix']);write(P+f'ENDPOINT7_{count}_MANIFEST_R1.json',card)
        write(P+f'ENDPOINT7_{count}_QUOTE_R1.json',quote(card,slowest))
    provenance=dict(source_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        input_document_sha256=hashlib.sha256((ROOT/'plans/cara_next_stage_20261101/USER_DESIGN_INPUT_R1.md').read_bytes()).hexdigest(),
        evidence_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in refs.values()},
        original_reader_reexecuted=False,original_freeze_written=False,original_scoring_reexecuted=False,GPU_submissions=0,ledger_written=False)
    write(P+'PREPARATION_PROVENANCE_R1.json',provenance)
    print('Prepared both39/46 manifests; original freeze raw bytes verified; no execution')
if __name__=='__main__':main()
