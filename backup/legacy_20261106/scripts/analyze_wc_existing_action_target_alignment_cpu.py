#!/usr/bin/env python3
"""Bind all exposed Human paid signals to local labels, never to final rewards."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

MODES=('CC','DC','CD','DD')
ORIGINS=('S22','S23_after_CC','S23_after_DC','S23_after_CD','S23_after_DD')
PROXY=('call','cfg_slot','solver_step','epoch','paid_probe','native_skip',
       'age_solver_steps','paid_input_drift','paid_probe_drift','dynamic_threshold',
       'accumulator_before_action','native_cycle_reset')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--registration',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    reg=json.loads(a.registration.read_text());assert not a.output.exists()
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','show',source+':'+str(a.registration)])==a.registration.read_bytes()
    for name,value in reg['input_sha256'].items():assert sha(name)==value,name
    start=time.perf_counter();budget=sha('reports/budget.json');contexts=[];records=[];pairs=events=repeats=0
    for seed,item in zip((2,3),reg['complete_exposed_inputs']):
        capture=json.loads(Path(item['capture']).read_text())
        independent=json.loads(Path(item['independent_audit']).read_text())
        assert capture['status']=='TEACHER_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS'
        assert independent['status']=='TEACHER_TERMINAL_LOCAL_STDLIB_SCOPE_REPEAT_ENERGY_AND_FEE_RECONSTRUCTION_PASS'
        assert independent['tensor_hashes_verified']==120 and independent['strict_repeat_groups']==20 and independent['full_parent_parity']
        values={}
        for kind in ('runner','CPU_score'):
            raw=gzip.decompress(Path(item[kind]).read_bytes());entry=capture['files'][kind]
            assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
            values[kind]=json.loads(raw)
        runner,score=values['runner'],values['CPU_score']
        registered=runner['config']['preregistration']
        request=registered.get('confirmation_request',registered.get('same_existing_request'))
        assert request['seed']==seed and request['name']=='human_199_seed'+str(seed)
        assert runner['source_revision']==score['source_revision']==independent['source_revision']==capture['source_revision']
        assert (score['local_CFG_pairs'],score['raw_tensor_count'],score['strict_repeat_groups'])==(40,120,20)
        assert score['full_parent_parity'] and not score['CUDA_initialized'] and score['GPU_submissions']==0
        assert score['status']=='TEACHER_COMPLETE_TWO_VIDEO_FIVE_STATE_FOUR_CELL_TWO_REPEAT_RAW_AUDIT_AND_CPU_SCORES_NOT_ENDPOINT'
        assert not any(score[k] for k in ('endpoint_or_absolute_physics_quality_claim','formal_RV_labels','independent_CONF','clean_speed_measurement'))
        on=runner['teacher']['parents'][1]
        assert [o['label'] for o in on['origins']]==[o['label'] for o in score['origins']]==list(ORIGINS)
        for origin,scored in zip(on['origins'],score['origins']):
            rows=origin['pairs'];assert len(rows)==8
            assert [r['label'] for r in rows]==[m+'_'+rep for m in MODES for rep in ('first','second')]
            cells=scored['metrics']['cells'];loss={m:cells[m]['guided_velocity_MSE_to_DD'] for m in MODES}
            assert loss['DD']==0 and all(math.isfinite(v) and v>=0 for v in loss.values())
            paid_by_cell={};deep={};walls={}
            for row in rows:
                assert row['parent_restored'] and row['status']=='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT'
                ev=row['action_report']['events'];assert len(ev)==2
                assert [e['actual_action'] for e in ev]==list(row['mode'])
                assert all(e['paid_probe'] and not e['current_deep_truth_used'] for e in ev)
                assert row['deep']==[26 if x=='D' else 0 for x in row['mode']]
                paid_by_cell[row['label']]=[{k:e[k] for k in PROXY} for e in ev]
                assert all(type(e['native_skip']) is bool for e in ev)
                deep[row['mode']]=sum(row['deep']);walls[row['label']]=row['wall_seconds']
                pairs+=1;events+=2
            for mode in MODES:
                first,second=[r for r in rows if r['mode']==mode]
                assert first['artifact']['tensor_sha256']==second['artifact']['tensor_sha256']
                assert first['origin_components']==second['origin_components'];repeats+=1
            equal=all(v==paid_by_cell['CC_first'] for v in paid_by_cell.values())
            native_by_cell={key:''.join('C' if p['native_skip'] else 'D' for p in value) for key,value in paid_by_cell.items()}
            native=next(iter(native_by_cell.values())) if equal else None
            frontier=[mode for mode in MODES if not any(
                loss[other]<=loss[mode] and deep[other]<=deep[mode] and
                (loss[other]<loss[mode] or deep[other]<deep[mode]) for other in MODES)]
            context={'seed':seed,'origin':origin['label'],'same_paid_observation_across_all_cells_and_repeats':equal,
                     'native_suggestion_by_cell':native_by_cell,'common_native_two_slot_suggestion':native,
                     'native_suggestion_is_online_joint_decision':False,
                     'origin_own_full_history':rows[0]['origin_own_history'],
                     'latest_anchors_shared':rows[0]['origin_own_history'][0][-1]==rows[0]['origin_own_history'][1][-1],
                     'action_labels':{mode:{'guided_MSE':loss[mode],
                        'local_MSE_reduction_from_CC':loss['CC']-loss[mode],
                        'relative_local_MSE_reduction_percent':None if loss['CC']==0 else 100*(loss['CC']-loss[mode])/loss['CC'],
                        'current_deep_block_calls':deep[mode],
                        'extra_deep_calls_from_CC':deep[mode]-deep['CC'],
                        'final_video_distortion_reduction':None,'future_real_time_saved_seconds':None} for mode in MODES},
                     'local_MSE_current_deep_nondominated_actions':frontier,
                     'native_suggestion_local_nondominated':None if native is None else native in frontier,
                     'raw_pair_wall_seconds_not_clean_speed':walls,
                     'scored_tensor_provenance':item['CPU_score']}
            contexts.append(context)
            for repeat in ('first','second'):
                records.append({'seed':seed,'origin':origin['label'],'repeat':repeat,
                     'paid_by_cell':{mode:paid_by_cell[mode+'_'+repeat] for mode in MODES},
                     'origin_own_full_history':rows[0]['origin_own_history']})
    assert (len(contexts),len(records),pairs,events,repeats)==(10,20,80,160,40)
    assert budget==sha('reports/budget.json') and 'torch' not in sys.modules
    output={'status':'EXPOSED_HUMAN_COMPLETE_PAID_SIGNAL_LOCAL_TARGET_ALIGNMENT_NOT_ENDPOINT_OR_POLICY',
            'source_revision':source,'registration_sha256':sha(a.registration),'input_sha256':reg['input_sha256'],
            'contexts':contexts,'proxy_records':records,
            'scope':{'seed_identities':2,'correlated_contexts':10,'repeated_proxy_records':20,'CFG_pairs':80,'action_events':160,'strict_repeat_groups':40},
            'summary':{'same_paid_observations_contexts':sum(c['same_paid_observation_across_all_cells_and_repeats'] for c in contexts),
                       'common_native_suggestion_counts':{m:sum(c['common_native_two_slot_suggestion']==m for c in contexts) for m in MODES},
                       'native_suggestion_local_nondominated_contexts':sum(c['native_suggestion_local_nondominated'] is True for c in contexts),
                       'mixed_action_nondominated_contexts':[{'seed':c['seed'],'origin':c['origin'],'actions':[m for m in c['local_MSE_current_deep_nondominated_actions'] if m in ('DC','CD')]} for c in contexts if any(m in ('DC','CD') for m in c['local_MSE_current_deep_nondominated_actions'])]},
            'final_video_and_future_time_labels_missing_preserved':True,'DD_zero_is_teacher_definition':True,
            'not_independent_validation_or_predictor_fit':True,'no_current_Common_partial_data_used':True,
            'budget_before_sha256':budget,'budget_after_sha256':sha('reports/budget.json'),
            'Torch_imported':False,'GPU_submissions':0,'CPU_wall_seconds':time.perf_counter()-start}
    a.output.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('contexts','proxy_records','input_sha256')},allow_nan=False))


if __name__=='__main__':main()
