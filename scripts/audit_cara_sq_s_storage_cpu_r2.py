"""Accept source-bound tiny CPU storage composition, never real F19 assets."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from audit_cara_sq_s_collection_cpu_r1 import accept
from audit_cara_sq_s_owner_cpu_r1 import result_sha

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_COLLECTION_STORAGE_CPU_R2.json'
CRITICAL=('src/wcomr/sq_s_collection_r1.py','src/wcomr/sq_s_storage_r1.py',
    'src/wcomr/sq_s_owner_roundtrip_r1.py','src/wcomr/sq_s_sources_r1.py','src/wcomr/sq_risk_r1.py',
    'src/wcomr/scout_parent_v22.py','tests/check_sq_s_collection_cpu_r1.py',
    'tests/check_sq_s_collection_storage_cpu_r2.py','tests/test_sq_s_storage_r1.py',
    'scripts/check_cara_sq_s_collection_cpu_r1.py',SCOPE)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S CPU storage acceptance')
    capture=json.loads(args.capture.read_text());scope=json.loads((ROOT/SCOPE).read_text())
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    accepted=accept(capture,scope,revision,storage=True);negative=[]
    for case in ('running','missing_parent','missing_raw','current_D_source','wrong_Dense_count',
            'incomplete_reloads','storage_unit_skip','wrong_unit_load_count','storage_cap',
            'CUDA_claim','real_storage_claim'):
        bad=copy.deepcopy(capture)
        if case=='running':bad['container_state'].update(Status='running',Running=True)
        elif case=='missing_parent':bad['result']['rows'][-1]['OFF_ON_controls'].pop()
        elif case=='missing_raw':bad['result']['rows'][-1]['raw_CPU_states'].pop()
        elif case=='current_D_source':
            raw=bad['result']['rows'][-1]['raw_CPU_states'][-1];raw['past_steps'][-1]=raw['step']
        elif case=='wrong_Dense_count':bad['result']['rows'][-1]['extra_Dense_teacher_pairs']=55
        elif case=='incomplete_reloads':bad['result']['rows'][-1]['storage']['reload_audit']['files_SHA_and_bytes_reloaded']=139
        elif case=='storage_unit_skip':bad['result']['storage_unit_controls']['skipped']=1
        elif case=='wrong_unit_load_count':bad['result']['storage_unit_controls']['tiny_tensor_reloads']=5
        elif case=='storage_cap':bad['result']['rows'][-1]['storage']['actual_stored_bytes']=16*2**20+1
        elif case=='CUDA_claim':bad['result']['CUDA_initialized']=True
        elif case=='real_storage_claim':bad['result']['streaming_raw_storage_accepted']=True
        bad['result_sha256']=result_sha(bad['result'])
        try:accept(bad,scope,revision,storage=True)
        except ValueError as error:negative.append(dict(case=case,rejected=True,reason=str(error)))
        else:raise AssertionError('S CPU storage acceptance admitted '+case)
    value=dict(status='S_FOUR_CARD_STREAMING_CPU_COMPOSITION_ACCEPTED_NOT_REAL_MODEL_ASSETS',
        passed=True,host='four_card',dual_host_CPU_accepted=False,source_revision=revision,
        critical_source_sha256={name:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)).hexdigest()
                               for name in CRITICAL},
        capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        result_sha256=capture['result_sha256'],accepted=accepted,negative_controls=negative,
        CPU_streaming_storage_accepted=True,streaming_raw_storage_accepted=False,
        complete_S_card_accepted=False,S_labels_collected=0,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(value['accepted']))


if __name__=='__main__':main()
