"""Pure CPU five-readout reader; no native model/owner import for postprocessing."""
import ast
from pathlib import Path


original = Path(__file__).with_name('p_reference_same_state_tensor_audit_r1.py')
source = original.read_text()
changes = [
    ('from . import e4c_source_age_tensor_audit_r1 as old',
     'from . import e4c_source_age_tensor_audit_r2 as old'),
    ('from .p_reference_same_state_owner_r1 import VARIANTS',
     "VARIANTS=('OFFICIAL_C','P_REFERENCE_SCALAR','D_REFERENCE_UNIT','P_REFERENCE_UNIT','D_REFERENCE_SCALAR')"),
    ("            out[name]=mse", "            branch=[v.double().square().mean().item() for v in (ec,eu)]\n            if (len(saved['diagnostics']['original_branch_MSE'])!=2 or any(\n                    not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-15)\n                    for a,b in zip(branch,saved['diagnostics']['original_branch_MSE']))):\n                raise ValueError('Independent five-way branch reduction differs')\n            out[name]=mse")]
changed = source
for before, after in changes:
    if changed.count(before) != 1: raise ValueError('Original five-way CPU reader site changed')
    changed = changed.replace(before, after)
inverse = changed
for before, after in reversed(changes):
    if inverse.count(after) != 1: raise ValueError('Five-way CPU reader inverse is ambiguous')
    inverse = inverse.replace(after, before)
if inverse != source or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(source)):
    raise ValueError('Unregistered independent CPU reader change')
exec(compile(changed, __file__+'#pure-five-readout-CPU', 'exec'), globals())
READER_PROOF = {'original_five_readout_reader_inverse_bytes_and_AST_equal': True,
    'native_owner_import_removed_without_readout_execution': True,
    'CPU_GPU_FP64_scalar_tolerance_only': {'rel_tol': 1e-12, 'abs_tol': 1e-15},
    'all_candidate_tensors_and_direct_equalities_unchanged': True,
    'all_five_branch_reductions_independently_verified': True}


def audit_point(point, root, loader, expected_shape):
    """A complete written point can be reduced even if its arm later failed."""
    import hashlib
    root = Path(root).resolve(); art = point['artifact']; path = Path(art['path']).resolve()
    if (not path.is_relative_to(root) or path.suffix != '.pt'
            or path.stat().st_size != art['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != art['sha256']):
        raise ValueError('Written point artifact binding differs')
    x = loader(path, weights_only=True, map_location='cpu')
    if set(x) != BASE_KEYS|EXTRA_KEYS or {k: tree_digest(v) for k, v in x.items()} != art['tensor_sha256']:
        raise ValueError('Complete14 written point tensor binding differs')
    rows = point['five_reference_readouts']
    if (tuple(r['variant'] for r in rows) != VARIANTS
            or not point['all_candidates_same_actual_input_and_full_source']
            or point['deployed_reference_unchanged'] != 'D_REFERENCE_SCALAR'
            or len(point['serial_restore_guards']) != 5
            or not point['teacher_state_restored_before_actual_C']
            or point['teacher_updates_final_deployment_anchors']
            or len(point['research_teacher_actual_head_events']) != 2
            or len({r['source_cache_sha256'] for r in rows}) != 1
            or len({r['true_D_full_state_sha256'] for r in rows}) != 1):
        raise ValueError('Original complete same-state and restoration proof differs')
    for pair in point['serial_restore_guards']:
        if ([g['stage'] for g in pair] != ['physical_restore', 'owned_restore']
                or not all(g['original_pre_snapshot_two_copy_gate_unchanged'] for g in pair)):
            raise ValueError('Physical/owned restoration capacity guards missing')
    h = point['actual_source_and_decision_history']
    if (point['source'] not in ('P', 'D') or h['true_D_before'] != h['true_D_after']
            or h['working_source_ages'] != [point['age']]*2
            or any(s['kind'] != point['source'] or s['created_step'] != point['step']-point['age']
                   for s in h['working_sources'])):
        raise ValueError('Actual source age and true-D protection differ')
    if (list(x['candidate_latent'].shape) != expected_shape
            or x['candidate_latent'].dtype != torch.float32
            or tree_digest(x['candidate_latent']) != point['candidate_latent_sha256']
            or x['timestep'].tolist() != point['timestep']):
        raise ValueError('Written own-state latent/timestep differs')
    errors = {}; branches = {}
    for index, (name, row) in enumerate(zip(VARIANTS, rows)):
        if (row['input_sha256'] != point['input_sha256'] or row['source'] != point['source']
                or row['age'] != point['age'] or row['step'] != point['step']
                or row['deployed_after_scoring'] != (index == 4)
                or row['readout']['shared_alpha'] != (0 if name == 'OFFICIAL_C' else .5 if point['step'] >= 25 else 1)
                or row['actual_head_calls'] != 2+row['readout']['extra_heads']
                or len(row['actual_head_events']) != row['actual_head_calls']):
            raise ValueError('Actual five-way coordinates/heads/phase differ')
        for proof in row['readout']['P_reference']:
            if proof is not None and (point['source'] != 'P' or not name.startswith('P_REFERENCE')
                    or proof['true_D_full_state_before_sha256'] != proof['true_D_full_state_after_sha256']):
                raise ValueError('P reference altered true-D calibration')
        pair = x['C'] if name == 'D_REFERENCE_SCALAR' else x[name]
        if len(pair) != 2 or any(t.device.type != 'cpu' or t.dtype != torch.float32
                or list(t.shape) != expected_shape or not torch.isfinite(t).all()
                for t in list(pair)+list(x['DENSE_SAME_STATE'])):
            raise ValueError('Finite full FP32 branch pairs required')
        ec, eu = [a-b for a, b in zip(pair, x['DENSE_SAME_STATE'])]
        mse = (8*ec-7*eu).double().square().mean().item()
        branch = [e.double().square().mean().item() for e in (ec, eu)]
        saved = row['guided_moments']
        if (not math.isclose(mse, saved['base_guided_MSE'], rel_tol=1e-12, abs_tol=1e-15)
                or len(saved['diagnostics']['original_branch_MSE']) != 2
                or any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)
                       for a, b in zip(branch, saved['diagnostics']['original_branch_MSE']))):
            raise ValueError('Independent complete point CFG/branch reduction differs')
        errors[name] = mse; branches[name] = branch
    controls = 0
    if point['source'] == 'D':
        for a, b in (('P_REFERENCE_SCALAR', 'C'), ('P_REFERENCE_UNIT', 'D_REFERENCE_UNIT')):
            if not all(torch.equal(u, v) for u, v in zip(x[a], x[b])):
                raise ValueError('D-source new/old reference equality differs')
            controls += 2
    return {'path': str(path), 'sha256': art['sha256'], 'actual_tensors_reloaded': 14,
        'all_five_guided_MSE': errors, 'all_five_branch_MSE': branches,
        'D_source_direct_equalities': controls, 'complete_written_point_not_whole_arm_acceptance': True}
