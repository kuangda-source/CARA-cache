"""Frozen four-pair scope and canonical scoring topology, standard library."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from wcomr.rv0_placement_evaluation import validate_frozen_scope, evaluation_plan
from wcomr.rv0_placement_scope import ENCODED


def run(root):
    config=json.loads((root/'configs/wc_w3_placement_scope_r1_draft.json').read_text())
    validate_frozen_scope(config['scope'])
    refusals=[]
    for key,value in [('complete_suffix_controls',12),('new_encoded_outputs',8),('science_swap_pairs',3),
                      ('maximum_age_solver_steps',32),('GPU_execution_selected',True),('production_entry_ready',True)]:
        damaged=copy.deepcopy(config['scope']); damaged[key]=value
        try: validate_frozen_scope(damaged)
        except ValueError: refusals.append('scope:'+key)
        else: raise AssertionError('Changed frozen scientific scope accepted')
    for mutation in ('pair','parent','quota','encoding'):
        damaged=copy.deepcopy(config['scope'])
        if mutation=='pair': damaged['scenes'][0]['swaps'][0]['calls'][0]=45
        elif mutation=='parent': damaged['scenes'][0]['parent_action_mask'][0]='C'
        elif mutation=='quota': damaged['scenes'][0]['parent_full_counts_per_CFG'][0]+=1
        else: damaged['scenes'][0]['controls'][0]['encode']=False
        try: validate_frozen_scope(damaged)
        except ValueError: refusals.append('scope:'+mutation)
        else: raise AssertionError('Changed frozen placement point accepted')
    path_accepts=[]
    with tempfile.TemporaryDirectory(prefix='placement-paths-cpu-') as directory:
        base=Path(directory); real=base/'real'; real.mkdir(); alias=base/'alias'; alias.symlink_to(real,target_is_directory=True)
        output=real/'outputs'/config['scope']['run_id']/'diagnostic'; output.mkdir(parents=True)
        def artifact(path):
            path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b'CPU_PATH_FIXTURE_NOT_VIDEO')
            return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        config['expected_project_root']=str(alias)
        receipt={'status':'PLACEMENT_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT',
            'CUDA_initialized':True,'toy_fixture':False,'complete_video':True,
            'run_card':config['scope']['card'],'scope':config,'wc_settings':config['historical_wc_settings'],'requests':[]}
        for scene in config['scope']['scenes']:
            name=scene['scene']; parent=artifact(output/name/'parent.mp4')
            reference=config['references'][name]
            reference['official_WC']['sha256']=parent['sha256']
            reference['Native35']=artifact(real/'historical'/name/'native.mp4')
            receipt['requests'].append({'sample_name':name,'historical_WC_encoded_bridge_pass':True,
                'context':[config['scope']['run_id']+':'+name]+reference['model_and_condition_context'],
                'artifact':parent,'decoded_children':[{'label':label,'status':'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE',
                    'artifact':artifact(output/name/(label+'.mp4'))} for label in ENCODED]})
        for label,target in [('symlink_root',alias),('canonical_root',real)]:
            config['expected_project_root']=str(target)
            plan=evaluation_plan(receipt,config)
            assert (len(plan['files']),len(plan['references']),len(plan['pairs']),len(plan['bridges']))==(10,2,6,4)
            assert plan['signed_swap_diagnostics']==4 and not plan['equal_runtime']
            path_accepts.append(label)
        for mutation in ('escape','symlink_escape','duplicate','other_run','missing_file','missing_parent',
                         'missing_encoding','encoding_incomplete','historical_bridge','GPU_false'):
            damaged=copy.deepcopy(receipt)
            first=damaged['requests'][0]
            if mutation=='escape': first['artifact']=artifact(real/'outside.mp4')
            elif mutation=='symlink_escape':
                link=output/'escape.mp4'; link.symlink_to(real/'outside.mp4'); first['artifact']['path']=str(link)
            elif mutation=='duplicate': first['decoded_children'][0]['artifact']=first['artifact'].copy()
            elif mutation=='other_run': first['artifact']=artifact(real/'outputs'/'other'/'diagnostic'/'file.mp4')
            elif mutation=='missing_file': first['artifact']['path']=str(output/'absent.mp4')
            elif mutation=='missing_parent': damaged['requests'].pop()
            elif mutation=='missing_encoding': first['decoded_children'].pop()
            elif mutation=='encoding_incomplete': first['decoded_children'][0]['status']='TECH_BLOCKED'
            elif mutation=='historical_bridge': first['historical_WC_encoded_bridge_pass']=False
            elif mutation=='GPU_false': damaged['CUDA_initialized']=False
            try: evaluation_plan(damaged,damaged['scope'])
            except (ValueError,FileNotFoundError): refusals.append('scoring:'+mutation)
            else: raise AssertionError('Invalid placement scoring topology accepted: '+mutation)
    assert len(refusals)==20
    return {'status':'PLACEMENT_FROZEN_SCOPE_AND_SCORING_TOPOLOGY_CPU_PASS_NOT_GPU',
        'frozen_scope':[2,16,10,4],'Native_relative_losses':6,'signed_diagnostics':4,
        'canonical_path_accepts':path_accepts,'refusals':refusals,'GPU_submissions':0,
        'true_video_or_real_swap_legality':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args(); print(json.dumps(run(args.root),allow_nan=False))
