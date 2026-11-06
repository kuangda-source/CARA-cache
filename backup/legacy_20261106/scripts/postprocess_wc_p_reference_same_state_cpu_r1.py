"""Read all registered slots and available original artifacts after GPU release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    for name in ('project', 'stage'): parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(args.stage/'src'))
    from wcomr.p_reference_same_state_production_r1 import RUN, CONFIG, sha, validate_contract, validate_selected, write
    from wcomr.p_reference_same_state_execution_r1 import PROTOCOL, validate_execution, validate_post_proof
    from wcomr.p_reference_same_state_terminal_r1 import inventory, original_gone, pure_verifier
    c = json.loads((args.stage/CONFIG).read_text()); scope = validate_contract(c, args.stage)
    p = json.loads((args.stage/PROTOCOL).read_text()); validate_execution(c, p, args.stage)
    validate_selected(c, args.stage); validate_post_proof(c, p, args.stage)
    root = args.project/'outputs'/RUN
    launch = json.loads((args.stage/'GPU-launch.json').read_text())
    supervisor = json.loads((root/'supervisor.json').read_text())
    original_gone(supervisor, launch['gpu_supervisor_pid'], lambda pid: Path('/proc/'+str(pid)).exists())
    if sha(args.stage/CONFIG) != supervisor['config_sha256']: raise ValueError('Original selected config changed')
    before = sha(args.project/'reports/budget.json'); budget = json.loads((args.project/'reports/budget.json').read_text())
    if any('inflight' in k for k in budget): raise ValueError('Original GPU budget must be settled before CPU')
    if supervisor['budget_after']['used_gpu_hours'] != supervisor['budget_before']['used_gpu_hours']+supervisor['wall_seconds']/3600:
        raise ValueError('Original whole-card cost must settle once')
    receipts = {}
    for arm in supervisor['arms']:
        path = root/arm['id']/'receipt.json'
        if not path.exists(): continue
        if sha(path) != arm['receipt_sha256']: raise ValueError('Original runner receipt changed')
        receipts[arm['id']] = json.loads(path.read_text())
    value = inventory(scope, supervisor, receipts)
    import torch
    torch.set_num_threads(2)
    if torch.cuda.is_initialized(): raise ValueError('Independent post must not initialize CUDA')
    def forbidden(*a, **k): raise RuntimeError('P-reference CPU raw reader forbids CUDA/downloads')
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.p_reference_same_state_tensor_audit_r2 import audit, audit_point, READER_PROOF
    from wcomr.rv0_video_reader import probe_video, decoded_video
    parent = args.project/c['parent_stage']/'current-birth-full64-config.json'
    if sha(parent) != c['parent_config_sha256']: raise ValueError('Bound actual shape config changed')
    shape = json.loads(parent.read_text())['expected_real_shape']
    verify = pure_verifier(args.stage); complete = []; failures = []; vectors = []; videos = []
    for slot in value['point_slots']:
        if 'point' not in slot: continue
        try:
            point = slot['point']
            if point['source'] != slot['source'] or point['age'] != slot['age']:
                raise ValueError('Registered source/age slot differs')
            read = audit_point(point, root/slot['arm'], torch.load, shape)
            slot.update(status='RAW_VALID_ALL_FIVE_INDEPENDENTLY_REDUCED', point_audit=read,
                all_five_guided_MSE=read['all_five_guided_MSE'])
        except (ValueError, OSError, RuntimeError, IndexError, KeyError) as error:
            slot.update(status='WRITTEN_POINT_AUDIT_FAILED_RETAINED', error=str(error))
            failures.append({'arm': slot['arm'], 'event': slot['event_id'], 'source': slot['source'],
                'age': slot['age'], 'point_audit_error': str(error)})
    for process in supervisor['arms']:
        arm = process['id']; r = receipts.get(arm)
        if r is None: continue
        # Every available recorded artifact is still read when a later suffix
        # or parent failed. Only complete arms use the strict whole44 reader.
        seen = set()
        def read_artifact(art):
            path = Path(art['path']).resolve()
            if not path.is_relative_to((root/arm).resolve()) or path.suffix != '.pt':
                raise ValueError('Recorded tensor outside original arm')
            if str(path) in seen: return
            seen.add(str(path))
            if path.stat().st_size != art['bytes'] or sha(path) != art['sha256']:
                raise ValueError('Recorded partial tensor file changed')
            x = torch.load(path, map_location='cpu', weights_only=True)
            if {k: tree_digest(v) for k, v in x.items()} != art['tensor_sha256']:
                raise ValueError('Recorded partial tensor content changed')
            tensors = []
            def walk(v):
                if isinstance(v, torch.Tensor):
                    if v.device.type != 'cpu' or not torch.isfinite(v).all(): raise ValueError('Finite CPU tensor required')
                    tensors.append(v)
                elif isinstance(v, (list, tuple)):
                    for t in v: walk(t)
                else: raise ValueError('Unexpected partial tensor structure')
            for v in x.values(): walk(v)
            vectors.append({'arm': arm, 'path': str(path), 'sha256': art['sha256'], 'actual_tensors_read': len(tensors)})
        for request in r['batch'].get('requests', []):
            for row in request['paths']:
                artifacts = [row.get('vector_artifact')]
                for event in row.get('origins', []):
                    for branch in event['branches']:
                        artifacts.append(branch.get('vector_artifact'))
                        artifacts.extend(point.get('artifact') for point in branch['age_points'])
                for art in filter(None, artifacts):
                    try: read_artifact(art)
                    except (ValueError, OSError, RuntimeError, IndexError, KeyError) as error:
                        failures.append({'arm': arm, 'path': art['path'], 'error': str(error)})
                art = row.get('video_artifact')
                if art is None: continue
                try:
                    path = Path(art['path']).resolve()
                    if (not path.is_relative_to((root/arm).resolve()) or path.stat().st_size != art['bytes']
                            or sha(path) != art['sha256']): raise ValueError('Original video binding differs')
                    metadata = probe_video(path); count = 0
                    with decoded_video(path) as stream:
                        for frame, pts, base in stream:
                            if frame.shape != (432, 768, 3) or pts != metadata['pts'][count] or base != metadata['time_base']:
                                raise ValueError('Complete original video geometry/PTS differs')
                            count += 1
                    if count != 93: raise ValueError('All93 frames required')
                    videos.append({'arm': arm, 'sample': request['sample_name'], 'collect': row['collect'],
                        'path': str(path), 'sha256': art['sha256'], 'frames': count, 'all93_RGB_PTS_verified': True})
                except (ValueError, OSError, RuntimeError, IndexError, KeyError) as error:
                    failures.append({'arm': arm, 'path': art['path'], 'error': str(error)})
        if process.get('exit_code') == 0 and r['status'] == 'P_REFERENCE_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT':
            try:
                structure = verify(r['batch'], scope)
                raw = audit(r['batch'], root/arm, torch.load, shape)
                if (len(raw['files']), raw['actual_tensors_reloaded'], raw['actual_direct_tensor_comparisons']) != (44, 580, 210):
                    raise ValueError('Complete per-flow actual tensor denominator differs')
                complete.append({'arm': arm, 'flow': r['flow'], 'structure': structure, 'raw': raw})
                indexed = {(x['event'], x['source'], x['age']): x for x in raw['all_five_independent_error_records']}
                for slot in value['point_slots']:
                    if slot['arm'] != arm: continue
                    key = (slot['event_id'], slot['source'], slot['age'])
                    slot.update(status='RAW_VALID_ALL_FIVE_INDEPENDENTLY_REDUCED',
                        all_five_guided_MSE=indexed[key]['same_state_guided_MSE'])
            except (ValueError, OSError, RuntimeError, IndexError, KeyError) as error:
                failures.append({'arm': arm, 'whole_arm_audit_error': str(error)})
        bound = {v['path'] for v in vectors if v['arm'] == arm}
        unbound = sorted(str(x.resolve()) for x in (root/arm).rglob('*.pt') if str(x.resolve()) not in bound)
        if unbound: failures.append({'arm': arm, 'unbound_or_failed_written_files_retained': unbound})
    whole = len(complete) == 2 and len(videos) == 8 and not failures
    value.update(status='P_REFERENCE_COMPLETE_SCOPE_CPU_READ_NOT_METHOD_ACCEPTANCE',
        original_supervisor_pid=supervisor['pid'], original_source_revision=supervisor['source_revision'],
        original_terminal=supervisor, original_runner_receipt_sha256={a: sha(root/a/'receipt.json') for a in receipts},
        whole_scope_verified=whole, complete_flow_audits=complete, all_actual_vectors=vectors,
        all_actual_videos=videos, actual_audit_failures=failures, pure_reader_proof=READER_PROOF,
        endpoint_quality_or_clean_latency_claim=False, new_GPU_submissions=0,
        CUDA_initialized=torch.cuda.is_initialized(), ledger_written=False,
        actual_billed_GPUh=supervisor['wall_seconds']/3600)
    if sha(args.project/'reports/budget.json') != before or value['CUDA_initialized']:
        raise ValueError('CPU reader must not change the ledger or initialize CUDA')
    target = args.stage/'raw-audit.json'; assert not target.exists(); write(target, value)
    print(json.dumps({'status': value['status'], 'whole_scope_verified': whole,
        'registered_parents': 8, 'registered_suffixes': 32, 'registered_points': 48,
        'complete_flow_arms': len(complete), 'actual_videos_decoded': len(videos), 'audit_failures': len(failures)}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
