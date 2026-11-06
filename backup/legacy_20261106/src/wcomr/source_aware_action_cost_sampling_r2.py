"""The unchanged full four-scene OFF/ON sampler with six cost arms."""
import ast
import hashlib
import inspect
from textwrap import dedent
import types

from . import partial_mlp_sampling as base
from .source_aware_action_cost_collection_r2 import (
    ActionCostCollector,compile_action_cost_collection,MODES,METHODS,READOUT_MODES)


def derive_verifier():
    original=dedent(inspect.getsource(base.verify_partial_batch))
    begin=original.index('                    n=tokens if mode.startswith')
    end=original.index('                count+=1',begin)
    old=original[begin:end]
    new='''                    records=observed['projection_records']
                    if mode in READOUT_MODES:
                        if observed['Linear_inputs'] or records:
                            raise ValueError('C/A cost arm secretly ran deep MLP')
                        if not o['C_recomputed_direct_equal'] or not o['cached_readout_source_proof']['cached_body_inverse_AST_equal']:
                            raise ValueError('Source-exact C readout or parity missing')
                        heads=o['warmup_actual_output_head_calls'][mode]
                        if mode=='C':
                            if heads!=2:raise ValueError('Actual two C heads missing')
                        else:
                            a=o['warmup_A_readouts'][mode]
                            if (a['step']!=o['step'] or a['action']!='CC'
                                    or a['shared_alpha']!=(.5 if o['step']>=25 else 1)
                                    or heads!=2+a['extra_heads'] or a['extra_heads'] not in (0,1,2)
                                    or a['teacher_calls'] or a['extra_deep_blocks']
                                    or a['C_readout_updates_D_anchor']
                                    or any(not v or v[-1]!=(7 if o['step']==12 else 25) for v in a['past_D_steps'])):
                                raise ValueError('Actual A heads, strength or true-D provenance missing')
                    else:
                        n=tokens if mode.startswith('DENSE') else max(1,math.floor((tokens//128)*.5))*128
                        if len(observed['Linear_inputs'])!=16 or any(v['rows']!=n for v in observed['Linear_inputs']):
                            raise ValueError('Both actual Linear quotas differ')
                        if mode!='DENSE_REFERENCE' and (len(records)!=8 or any(r['actual_MLP_rows']!=n or r['fallback'] for r in records)):
                            raise ValueError('Actual P0 projection rows or source missing')
                        if o['warmup_actual_output_head_calls'][mode]!=2:
                            raise ValueError('Deep action head costs missing')
                    if not o['incremental_post_probe_cost_not_full_pair_or_clean_pipeline']:
                        raise ValueError('Action cost boundary was mislabeled')
'''
    changed=original[:begin]+new+original[end:]
    inverse=changed.replace(new,old)
    assert inverse==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original))
    ns={**base.verify_partial_batch.__globals__,'MODES':MODES,'METHODS':METHODS,'READOUT_MODES':READOUT_MODES}
    exec(compile(changed,__file__+'#cost-verifier','exec'),ns)
    return ns['verify_partial_batch'],{'inverse_AST_and_original_bytes_equal':True,
        'original_verifier_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'original_full_eight_parent_eight_origin_112_branch_scope_preserved':True}


verify_batch,VERIFIER_PROOF=derive_verifier()


def bind(original,replacements):
    if original.__closure__:raise ValueError('Closure-free original entry required')
    assert all(k in original.__globals__ for k in replacements)
    value=types.FunctionType(original.__code__,{**original.__globals__,**replacements},
        original.__name__,original.__defaults__)
    value.__kwdefaults__=original.__kwdefaults__
    assert value.__code__ is original.__code__
    return value


compiler=bind(base._compile_batch,{'PartialGroupCollector':ActionCostCollector,
    'compile_partial_collection':compile_action_cost_collection,'verify_partial_batch':verify_batch})
run_batch,SAMPLING_PROOF=compiler()
audit_vectors=bind(base.audit_partial_vectors,{'verify_partial_batch':verify_batch,'METHODS':METHODS,'MODES':MODES})
