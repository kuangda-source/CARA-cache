"""Joint-swap sign, complete coverage and artifact/frame binding controls."""
import argparse
import copy
import json
from pathlib import Path

from wcomr.rv0_placement_scores import signed_placement_diagnostics


def run(root):
    config=json.loads((root/'configs/wc_w3_placement_scope_r1_draft.json').read_text())
    pairs=[]
    for scene in config['scope']['scenes']:
        for label,value,slot in [('BASE1',.4,None),('SWAP0_first',.3,0),('SWAP1_first',.5,1)]:
            reference=config['references'][scene['scene']]['Native35']
            candidate={'sha256':('1' if slot is None else str(slot+2))*64}
            pairs.append({'scene':scene['scene'],'label':label,'CFG_slot':slot,
                'reference':reference,'candidate':candidate,
                'score':{'frames':93,'pts':[[i,'1/16'] for i in range(93)],'frame_distances':[value]*93,
                         'mean_LPIPS':sum([value]*93)/93,'reference_sha256':reference['sha256'],
                         'candidate_sha256':candidate['sha256']}})
    result=signed_placement_diagnostics(pairs,config)
    assert len(result)==4 and [r['LPIPS_BASE_minus_SWAP']>0 for r in result]==[True,False,True,False]
    assert all(r['signed_negative_retained'] and not r['formal_RV_training_label'] for r in result)
    refusals=[]
    for mutation in ('missing','duplicate','order','CFG','frames','pts','reference','candidate','nonfinite','mean','subsample'):
        damaged=copy.deepcopy(pairs); p=damaged[1]; score=p['score']
        if mutation=='missing': damaged.pop()
        elif mutation=='duplicate': damaged[1]=copy.deepcopy(damaged[0])
        elif mutation=='order': damaged[0],damaged[1]=damaged[1],damaged[0]
        elif mutation=='CFG': p['CFG_slot']=1
        elif mutation=='frames': score['frames']=92
        elif mutation=='pts': score['pts'][0][0]=1
        elif mutation=='reference': score['reference_sha256']='0'*64
        elif mutation=='candidate': score['candidate_sha256']='0'*64
        elif mutation=='nonfinite': score['frame_distances'][0]=float('nan')
        elif mutation=='mean': score['mean_LPIPS']+=.1
        elif mutation=='subsample': score['frame_distances'].pop()
        try: signed_placement_diagnostics(damaged,config)
        except ValueError: refusals.append(mutation)
        else: raise AssertionError('Invalid signed placement aggregation accepted: '+mutation)
    return {'status':'PLACEMENT_SIX_LOSS_FOUR_SIGNED_JOINT_SWAP_CPU_CONTRACT_PASS_NOT_VIDEO',
        'signed_positive_and_negative_cases':4,'refusals':refusals,'GPU_submissions':0,'true_video_scores':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args(); print(json.dumps(run(args.root),allow_nan=False))
