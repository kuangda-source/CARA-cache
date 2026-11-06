"""Capture the original terminal audit; do not rerun generation or tensor tests."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    code = r'''import base64,gzip,hashlib,json,time
from pathlib import Path
project=Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=project/'.sync/wc-e4c-source-age-selected-r1-20261011'
reader=project/'.sync/wc-e4c-readonly-reader-cpu-r1-20261011'
output=project/'outputs/wc-e4c-matched-p-d-age124-offon4-suffix16-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sup=json.loads((output/'supervisor.json').read_text())
terminal=json.loads((reader/'terminal-CPU-supervisor.json').read_text())
assert sup['pid']==4075406 and sup['arms'][0]['pid']==4075494
assert terminal['pid']==4079033 and terminal['child_exit_code']==terminal['exit_code']==0
pids=[sup['pid'],sup['arms'][0]['pid'],terminal['pid'],terminal['child_pid']]
assert not any(Path('/proc/'+str(p)).exists() for p in pids)
config=json.loads((stage/'e4c-source-age-config.json').read_text())
files=config['payload_sha256']
assert len(files)==399 and {n:sha(stage/n) for n in files}==files
assert sha(reader/'scripts/postprocess_wc_e4c_source_age_cpu_r1.py')==terminal['postprocessor_sha256']
assert sha(reader/'real-GPU-audit.json')==terminal['result_sha256']
value=json.loads((reader/'real-GPU-audit.json').read_text())
assert value['status']=='E4C_WHOLE_TRUE_MODEL_SOURCE_AGE_CPU_AUDITED_NOT_ENDPOINT_QUALITY'
assert value['original_gpu_terminal']==sup
assert sha(output/'model/receipt.json')==sup['arms'][0]['receipt_sha256']==value['original_runner_receipt_sha256']
raw=value['whole_actual_tensor_audit'];structural=value['whole_structural_audit']
assert structural['full_parent_paths']==4 and structural['events']==4 and structural['suffixes']==16
assert structural['same_state_age_points']==24
assert len(raw['files'])==44 and raw['actual_tensors_reloaded']==388
assert raw['actual_direct_tensor_comparisons']==162 and len(raw['actual_age_points_reduced'])==24
assert raw['complete_artifact_set']
assert len(value['all_actual_videos'])==4 and all(v['all93_RGB_frames_decoded'] for v in value['all_actual_videos'])
summary=value['matched_source_age_summary'];points=summary['points'];pairs=summary['matched_birth_age_comparisons']
assert len(points)==24 and len(pairs)==12
for pair in pairs:
    p,d=[next(v for v in points if (v['event'],v['source'],v['age'])==(pair['event'],s,pair['age'])) for s in ('P','D')]
    assert pair['P_own_state_guided_MSE']==p['guided_MSE'] and pair['D_own_state_guided_MSE']==d['guided_MSE']
    assert pair['ratio_P_over_D']==p['guided_MSE']/d['guided_MSE']
    assert pair['difference_P_minus_D']==p['guided_MSE']-d['guided_MSE']
ledger=json.loads((project/'reports/budget.json').read_text())
assert ledger==sup['budget_after']==value['current_ledger']
assert sup['budget_after']['used_gpu_hours']==sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600
assert not any('inflight' in k for k in ledger) and not value['CUDA_initialized']
names={'GPU-supervisor':output/'supervisor.json','GPU-receipt':output/'model/receipt.json',
    'GPU-registration':stage/'registration.json','CPU-supervisor':reader/'terminal-CPU-supervisor.json',
    'CPU-audit':reader/'real-GPU-audit.json','CPU-log':reader/'terminal-CPU.log','budget':project/'reports/budget.json'}
originals={n:{'sha256':sha(p),'gzip_base64':base64.b64encode(gzip.compress(p.read_bytes(),mtime=0)).decode()} for n,p in names.items()}
proof={'status':'E4C_COMPLETE_ORIGINAL_TERMINAL_CAPTURE_AND_SCALAR_RECONSTRUCTION_PASS',
    'original_GPU_source_revision':sup['source_revision'],'original_CPU_source_revision':terminal['source_revision'],
    'original_PIDs_absent':pids,'source_files_unchanged':len(files),'full_parent_paths':4,'all93_frame_videos':4,
    'suffixes':16,'age_points':24,'actual_tensor_reader_files':44,'actual_tensor_reader_tensors':388,
    'actual_tensor_reader_comparisons':162,'all12_pairs_independently_reconstructed_from_actual_reader':True,
    'matched_age_pairs':pairs,'billed_GPUh':sup['wall_seconds']/3600,'ledger':ledger,
    'remaining_GPUh':ledger['cap_gpu_hours']-ledger['used_gpu_hours'],'observed_unix':time.time(),
    'new_GPU_submissions':0,'terminal_reader_was_not_rerun':True,'endpoint_quality_or_clean_latency_claim':False,
    'subsequent_P_D_states_are_different':True,'events_are_not_independent_scenes':True}
print(json.dumps({'capture':proof,'original_files':originals}))
'''
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code,text=True,capture_output=True)
    if call.returncode:
        raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout);proof=value['capture'];refs={}
    for name,row in value['original_files'].items():
        zipped=base64.b64decode(row.pop('gzip_base64'));raw=gzip.decompress(zipped)
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        p=root/'reports'/('wc_e4c_terminal_20261011_'+name+'.native.gz')
        assert not p.exists();p.write_bytes(zipped)
        row['local_ref']=str(p.relative_to(root));refs[name]=row
        if name=='budget':(root/'reports/budget.json').write_bytes(raw)
    proof['original_files']=refs
    p=root/'reports/wc_e4c_terminal_20261011_capture.json';assert not p.exists()
    p.write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('ledger','matched_age_pairs','original_files')}))


if __name__=='__main__':main()
