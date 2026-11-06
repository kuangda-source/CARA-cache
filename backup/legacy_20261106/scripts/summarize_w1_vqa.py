"""Recompute terminal small-judge scores from original bound questions/raw answers."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.development_vqa_run import load_bound,load_questions,sha256,summarize_receipt
from wcomr.replay_results import summarize


def main():
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();project=a.project.resolve();r=json.loads(a.receipt.read_text())
    protocol_path=project/'manifests/w1_development_vqa_protocol.json'
    protocol=load_bound(protocol_path,r['source_sha256']['manifests/w1_development_vqa_protocol.json'])
    reference=load_bound(project/protocol['reference_receipt'],protocol['reference_sha256'])
    candidate=load_bound(project/protocol['candidate_receipt'],protocol['candidate_sha256'])
    summarize(candidate,reference=reference)
    cases=[{'name':old['name'],'reference':old['off'],'candidate':new['scalar_off']}
           for old,new in zip(reference['cases'],candidate['cases'])]
    result=summarize_receipt(r,protocol,load_questions(project,protocol),cases)
    result['input_receipt_sha256']=sha256(a.receipt)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','planned_scenes','accepted_pairs','rejected_candidates','fully_parsed_pairs','equal_scene_mean_delta']}))


if __name__=='__main__':main()
