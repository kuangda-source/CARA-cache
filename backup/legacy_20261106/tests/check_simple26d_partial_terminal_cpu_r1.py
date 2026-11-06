"""Reject corrupted partial receipts and preserve strict full-card refusal."""
import argparse,copy,gzip,importlib.util,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();raw=json.loads(gzip.decompress(a.capture.read_bytes()))
    partial=load('analyze_wc_simple26d_partial_terminal_r1');strict=load('analyze_wc_simple26d_full36_r1')
    result=partial.analyze(raw);assert not result['whole_card_accepted'] and result['formal_denominator']==24
    rejected=[]
    def case(name,change):
        value=copy.deepcopy(raw);change(value)
        try:partial.analyze(value)
        except (AssertionError,KeyError,ValueError):rejected.append(name)
        else:raise AssertionError('Corruption accepted: '+name)
    case('missing_original_slot',lambda v:v['final']['rows'].pop())
    case('nonfinite_frame',lambda v:v['final']['rows'][12]['LPIPS']['frame_distances'].__setitem__(0,float('nan')))
    case('changed_frame_mean',lambda v:v['final']['rows'][12]['LPIPS'].__setitem__('mean_LPIPS',0.))
    case('changed_dense_quota',lambda v:v['final']['rows'][12]['counts'].__setitem__('DD',25))
    case('changed_actual_bill',lambda v:v['billing'].__setitem__('actual_GPUh',1.))
    case('invented_four_scene_mean',lambda v:v['final']['methods'][0].__setitem__('complete_four_scene_mean_LPIPS',0.))
    case('invented_completed_failed_path',lambda v:v['final']['rows'][28].__setitem__('status','COMPLETE'))
    case('changed_payload',lambda v:v['payload_verified'].__setitem__(next(iter(v['payload_verified'])),False))
    try:strict.analyze(raw)
    except AssertionError:rejected.append('original_strict_full_card_analyzer_refuses_child_exit1')
    else:raise AssertionError('Full card accidentally accepted')
    from wcomr.gpu_budget_pool_v2 import sha
    out=dict(status='SIMPLE26D_PARTIAL_RECEIPT_NINE_NEGATIVE_CONTROLS_CPU_PASS',capture_ref=str(a.capture),
        capture_sha256=sha(a.capture),controls=rejected,negative_controls=9,whole_card_accepted=False,GPU_submissions=0)
    with a.output.open('x') as handle:json.dump(out,handle,indent=2);handle.write('\n')
    print(json.dumps(out))

if __name__=='__main__':main()
