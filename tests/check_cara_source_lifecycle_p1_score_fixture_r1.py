"""Fresh pure metadata fixture for new P1 release/score readers; no real metrics."""
import copy
import math

import test_cara_source_lifecycle_p1_collection_r1 as collection_fixture
from wcomr.cara_source_lifecycle_p1_inventory_r1 import read_inventory
from wcomr.cara_source_lifecycle_p1_artifacts_r1 import quality_positions,SOURCE
from wcomr.cara_source_lifecycle_p1_scores_r1 import pair_key,PROTOCOL
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]


def metric(pair,decoded):
    curve=[.2]*93;ssim=[.8]*93
    return dict(status='COMPLETE',member=pair['member'],candidate=copy.deepcopy(pair['candidate']),
        reference=copy.deepcopy(pair['reference']),frames=93,temporal_frame_pairs=92,PTS_equal=True,
        decoded_RGB_sha256=[decoded[pair[s]['proof_sha256']]['RGB_sha256'] for s in ('candidate','reference')],
        Alex_frames=curve,SSIM_frames=ssim,Alex=sum(curve)/93,SSIM=sum(ssim)/93,Alex_worst=.2,
        Alex_q95_higher=.2,Alex_first_worst_frame_zero_based=0,MSE_video=.01,PSNR_video_dB=20.,PSNR_is_infinite=False,
        reference_temporal_L1=.01,reference_gradient_L1=.02,candidate_gradient_energy=.03,
        reference_gradient_energy=.02,gradient_energy_ratio=1.5,gradient_ratio_status='FINITE')


def packet():
    fixture=collection_fixture.P1CollectionTests('runTest');fixture.setUp()
    try:
        collection,runtime=fixture.collection('new-final-reader-fixture')
        execute=runtime.execute
        def off_clock(slot,output):
            proof=execute(slot,output)
            if slot['timing']=='OFF':proof['T_DD']=None
            return proof
        collection.execute=off_clock
        result=collection.run(allow_new=True)
        assert result.get('failure') is None
        index=read_inventory(collection.root,fixture.card,fixture.context,[1.]*36,
            dict(path_seconds=10.,FIT_score_seconds=2.,overhead_seconds=.1),
            cpu_validation=True,maximum_elapsed_seconds=runtime.clock+1)
        positions=quality_positions(index,fixture.card)
        decoded={v['value']['proof_sha256']:dict(RGB_sha256=v['value']['proof']['pre_encode_RGB']['sha256'],
            shape=[93,64,64,3],frames=93,fps=16,PTS=[[i,16] for i in range(93)]) for v in index['physical'].values()}
        internal={};new={}
        for position in positions:
            if (position['member'] in fixture.card['FIT'] and position['role'].startswith(('V1-','LPIPS_SEARCH-','UNIFORM'))):
                key=position['pair_key'];pair={k:position[k] for k in ('member','candidate','reference')}
                row=metric(pair,decoded)
                internal[key]=dict(pair=pair,metrics=row,metrics_sha256=digest(row),
                    original_response_path='/EXPLICIT_CPU_FIXTURE/response.json',original_response_sha256='d'*64,
                    original_execution_sha256='e'*64)
        for position in positions:
            key=position['pair_key']
            if key not in internal and key not in new:
                new[key]=dict(id='P1_NEW_'+key,**{k:position[k] for k in ('member','candidate','reference')},
                    expected_decoded_RGB_sha256=[decoded[position[s]['proof_sha256']]['RGB_sha256'] for s in ('candidate','reference')])
        manifest=dict(schema='CARA_V1_P1_RELEASED_SCORE_MANIFEST_R1',run_id='cara-source-lifecycle-V1-P1-full146-r1-20261102',
            launch_id=fixture.context['launch_id'],scope_sha256=fixture.card['scope_sha256'],FIT=fixture.card['FIT'],CHECK=fixture.card['CHECK'],
            CPU_fixture_only=True,semantic_denominator=146,physical_paths=index['physical_paths'],physical_model_pairs=index['physical_model_pairs'],
            source_label_count=64,identity_controls=[dict(id=str(i),passed=True) for i in range(12)],identity_controls_passed=12,
            quality_positions=positions,internal_rows=internal,new_pairs=list(new.values()),GPU_released=True,cost_settled=True,
            original_launch_sha256='a'*64,algorithm_summary_sha256=index['summary_sha256'],
            protocol_sha256=digest(json.loads((ROOT/PROTOCOL).read_bytes())),internal_scores_recomputed=0,old_RGB_MSE_search_reselected=False)
        value=dict(status='P1_RELEASED_FULL146_ARTIFACTS_INTERNAL_SCORES_REUSED_PENDING_NEW_PAIRS',manifest=manifest,
            decoded=decoded,physical_artifacts={},all_internal_cohorts=[],release=dict(GPU_released=True,cost_settled=True,
            original_launch_sha256='a'*64),CPU_fixture_only=True,reader_sha256=file_sha(ROOT/SOURCE),
            scientific_accepted=False,GPU_submissions=0,ledger_written=False)
        return fixture,value
    except BaseException:
        fixture.doCleanups()
        raise
