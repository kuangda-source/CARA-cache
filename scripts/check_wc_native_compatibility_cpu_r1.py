#!/usr/bin/env python3
"""Read accepted complete32 inputs and reject actual metadata pairing changes."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    started=time.perf_counter();sys.path.insert(0,'src')
    from wcomr.native_video_compatibility_r1 import assess
    source=Path('reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json')
    proof=json.loads(source.read_text());assert proof['independent_checks']['success']
    item=proof['files']['runner'];raw=gzip.decompress(Path(item['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==item['sha256'] and len(raw)==item['bytes']
    value=json.loads(raw);batch=value['comparison']['batch'];refs=value['comparison']['references']
    methods=[r['method'] for r in batch['requests'][0]['paths']]
    result=assess(batch,refs,methods);assert (result['complete_pairing_slots'],result['compatible_pairs'])==(28,28)
    cases={
        'prefix':lambda b:b['requests'][0]['paths'][0]['guided_sha256'].__setitem__(0,'FOREIGN'),
        'prepared':lambda b:b['requests'][0]['prepared_input_calls'][0].__setitem__('prepared','FOREIGN'),
        'solver':lambda b:b['requests'][0]['paths'][0].__setitem__('actual_raw_solver_configuration',{}),
        'conditions':lambda b:b['requests'][0]['paths'][0].__setitem__('condition_fields_before',[]),
        'truncated_guided':lambda b:b['requests'][0]['paths'][0]['guided_sha256'].pop()}
    detected=[]
    for name,change in cases.items():
        bad=copy.deepcopy(batch);change(bad);check=assess(bad,refs,methods)
        assert check['complete_pairing_slots']==28 and check['incompatible_pairs']==1 and check['compatible_pairs']==27
        detected.append(name)
    denominator=[]
    for name in ('missing_method','different_scene','different_seed_reference'):
        bad=copy.deepcopy(batch);reference=copy.deepcopy(refs)
        if name=='missing_method':bad['requests'][0]['paths'].pop()
        elif name=='different_scene':bad['requests'][0]['sample_name']='FOREIGN'
        else:reference[0]['request']['seed']=4
        try:assess(bad,reference,methods)
        except ValueError:denominator.append(name)
        else:raise AssertionError('Incomplete Native denominator accepted')
    output={'status':'ACCEPTED32_NATIVE_COMPATIBILITY_CPU_PASS_NOT_NEW64_TRAJECTORY',
        'actual_accepted_video_metadata_pairs':28,'single_path_mismatch_detections':detected,
        'denominator_refusals':denominator,'CPU_wall_seconds':time.perf_counter()-started,
        'source_sha256':{str(source):hashlib.sha256(source.read_bytes()).hexdigest(),
            item['local_path']:hashlib.sha256(Path(item['local_path']).read_bytes()).hexdigest(),
            'src/wcomr/native_video_compatibility_r1.py':hashlib.sha256(Path('src/wcomr/native_video_compatibility_r1.py').read_bytes()).hexdigest(),
            'scripts/check_wc_native_compatibility_cpu_r1.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'GPU_submissions':0,'budget_written':False,'actual_new64_compatibility_claim':False}
    dest=Path('reports/wc_native_compatibility_cpu_r1_results_20261010.json');assert not dest.exists()
    dest.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='source_sha256'}))


if __name__=='__main__':main()
