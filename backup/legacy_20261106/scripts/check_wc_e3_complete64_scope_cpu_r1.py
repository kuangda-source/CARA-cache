"""Check completeness and refusal cases before any E3 model work."""
import copy
import json
from pathlib import Path
import sys


def check(scope):
    from wcomr.e3_complete64_block_scope_r1 import validate_scope,validate_block
    verdict=validate_scope(scope)
    for block in scope['blocks']:validate_block(block,scope)
    refusals=[]
    def refuse(name,edit):
        bad=copy.deepcopy(scope);edit(bad)
        try:validate_scope(bad)
        except (ValueError,KeyError):refusals.append(name)
        else:raise AssertionError('Incomplete or altered E3 card admitted: '+name)
    refuse('missing_scientific_control',lambda s:s['all64_slots'].pop())
    refuse('duplicate_scientific_key',lambda s:s['all64_slots'].__setitem__(1,s['all64_slots'][0]))
    refuse('missing_execution_path',lambda s:s['blocks'][-1]['paths'].pop())
    refuse('missing_model_block',lambda s:s['blocks'].pop())
    refuse('changed_block_order',lambda s:s['blocks'].reverse())
    refuse('changed_source_strategy',lambda s:s['blocks'][0].update(strategy='FOREIGN'))
    refuse('unqualified_reuse',lambda s:next(r for r in s['all64_slots'] if r['disposition']=='GENERATE_COMPLETE_PATH').update(disposition='REUSE_QUALIFIED_DEV_OUTPUT'))
    refuse('reused_artifact_identity_missing',lambda s:s['all64_slots'][0]['reuse_binding']['video_artifact'].pop('sha256'))
    refuse('budget_evasion_as_independent_cards',lambda s:s.update(one_complete_GPU_card_not20_independent_cards=False))
    block=copy.deepcopy(scope['blocks'][0]);block['paths'].append(block['paths'][0])
    try:validate_block(block,scope)
    except ValueError:refusals.append('foreign_or_overfull_block')
    else:raise AssertionError('Altered run block admitted')
    assert len(refusals)==10
    return {'scope':verdict,'all20_blocks_checked':True,'scope_refusals':refusals,'Torch_imported':'torch' in sys.modules}


def main():
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
    scope=json.loads((root/'manifests/wc_e3_complete64_reuse10_fresh54_blocks_r1_20261011.json').read_text())
    value=check(scope);assert not value['Torch_imported']
    print(json.dumps(value))


if __name__=='__main__':main()
