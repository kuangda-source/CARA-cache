"""Registered phase execution and immutable selection; no resource dispatch."""
import hashlib,json,math
from pathlib import Path
from .wc_time_card_r1 import digest,select_tau

def atomic(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)

def collect_phase(adapter, phase, output, *, before_request, save, after_diagnostics):
    if phase not in ('A','B'):raise ValueError('Exact phase required')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    slots=[s for s in adapter.card['physical_matrix'] if s['section'].startswith(phase+'_')]
    state=dict(phase=phase,status='RUNNING',scope_sha256=adapter.card['scope_sha256'],rows=[dict(slot=s,status='NOT_REACHED') for s in slots])
    save(state)
    for row in state['rows']:
        slot=row['slot'];row['status']='RUNNING';save(state)
        try:
            before_request(slot)
            from .wc_time_diagnostics_r1 import capture
            with capture(adapter.inference,slot['section']=='A_DIAGNOSTIC') as witness:
                result=adapter(slot,output/slot['id'].replace(':','_'))
            if witness:row['diagnostic_inputs']=witness
            # CPU transfers below are outside all request timing, but inside billed job.
            import torch
            tensors={k:result.pop(k) for k in ('final_latent','guided') if k in result}
            path=output/(slot['id'].replace(':','_')+'.pt')
            if tensors:
                torch.save(tensors,path)
                row['tensor_artifact']=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
            row.update(status=result['status'],result=result);save(state)
            diagnostics=[r for r in state['rows'] if r['slot']['section']=='A_DIAGNOSTIC']
            if slot['section']=='A_DIAGNOSTIC' and slot['id']==diagnostics[-1]['slot']['id']:
                gate=after_diagnostics(diagnostics)
                if gate.get('passed') is not True:raise ValueError('Numerical gate failed; calibration stopped')
                state['diagnostic_gate']=gate;save(state)
        except BaseException as error:
            row.update(status='TECH_FAILED',error_type=type(error).__name__,error=str(error));state['status']='FAILED_NO_REPLAY';save(state);raise
    state['status']='TERMINAL';save(state);return state

def freeze_selection(card, phase_state, release, score_rows, destination):
    """Release identity and four scores bind one immutable parameter decision."""
    dest=Path(destination)
    if dest.exists():raise ValueError('Frozen selection already exists')
    if phase_state.get('phase')!='A' or phase_state.get('scope_sha256')!=card['scope_sha256'] or phase_state.get('status')!='TERMINAL':raise ValueError('Complete bound phase A required')
    if release.get('phase')!='A' or release.get('scope_sha256')!=card['scope_sha256'] or not all(release.get(k) is True for k in ('GPU_released','cost_settled','original_process_exited')):raise ValueError('Verified settled release required')
    rows={r['slot']['id']:r for r in phase_state['rows']}
    if set(rows)!={s['id'] for s in card['physical_matrix'] if s['section'].startswith('A_')} or any(r['status']!='COMPLETE' for r in rows.values()):raise ValueError('Phase A incomplete; no selection')
    if not release.get('numerical_GPU_equivalence_passed'):raise ValueError('Real three-arm GPU gate required')
    candidates=[]
    for s in [s for s in card['physical_matrix'] if s['section']=='A_CALIBRATION']:
        matches=[x for x in score_rows if x['slot_id']==s['id']]
        if len(matches)!=1:raise ValueError('Exactly one accepted Alex score per candidate required')
        x=matches[0];anchor=next(r for r in rows.values() if r['slot']['section']=='A_ANCHOR' and r['slot']['role']=='CARA_SHARED25_C_U36' and r['slot']['scene']==s['scene'])
        native=next(r for r in rows.values() if r['slot']['section']=='A_ANCHOR' and r['slot']['role']=='NATIVE_U36' and r['slot']['scene']==s['scene'])
        if x.get('reference_slot_id')!=native['slot']['id'] or x.get('status')!='SCORED' or x.get('frames')!=93:raise ValueError('Native pair/score identity differs')
        candidates.append(dict(scene=s['scene'],tau=s['tau'],status='COMPLETE',T_DD=rows[s['id']]['result']['T_DD'],CARA_T_DD=anchor['result']['T_DD'],Alex=x['Alex']))
    result=select_tau(candidates,card['selection']['CAL'])
    result.update(scope_sha256=card['scope_sha256'],phase_A_GPU_released=True,release_sha256=digest(release),phase_state_sha256=digest(phase_state),scores_sha256=digest(score_rows))
    with dest.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    return result
