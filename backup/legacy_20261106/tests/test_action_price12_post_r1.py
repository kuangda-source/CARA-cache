"""Full12 post audit on small real CPU tensors; video/old-parent doubles.

Metadata shape comes from the accepted local32 fixture, not new real videos.
Every source/phase position and all formal orders survive the fixture.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import torch

from wcomr import action_price12_post_r1 as M
from wcomr.frozen_shared_post_r1 import artifact_path
from wcomr.mid_coverage import tree_digest

ROOT=Path(__file__).resolve().parents[1]
CAPTURE='reports/wc_paper_N09_action12_full32_local_CPU_R7_original_20261016.json.gz'
SHAPE=(1,1,1,1,1)


def fixture(folder):
    root=Path(folder).resolve();value=json.loads(gzip.decompress((ROOT/CAPTURE).read_bytes()))
    runner=copy.deepcopy(value['checks'][0]['runner']);rows=runner['runs'];plan=runner['matrix']
    names=[r['scene'] for r in rows if r['mode']=='BASELINE'];states=[];bindings={}
    def save(path,payload,point=False):
        path.parent.mkdir(parents=True,exist_ok=True);torch.save(payload,path)
        asset=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
        if point:asset['tensor_sha256']=tree_digest(payload)
        return asset
    for row in rows:
        index=names.index(row['scene']);directory=root/row['id']
        final=torch.full(SHAPE,index+.5);guided=[torch.full(SHAPE,index+step/100) for step in range(36)]
        row.update(final_artifact=save(directory/'final-latent.pt',dict(final_latent=final)),
            guided_artifact=save(directory/'guided.pt',dict(guided=guided)),
            final_latent_sha256=tree_digest(final),guided_tree_sha256=tree_digest(guided))
        for point in row['diagnostic_points']:
            payload={a+'_'+b:torch.full(SHAPE,index+offset+(.01 if b=='conditional' else .02))
                for offset,a in enumerate(('C','A','P0','D')) for b in ('conditional','unconditional')}
            payload.update(actual_latent=torch.zeros(SHAPE),timestep=torch.tensor(float(point['point']['chosen']['step'])))
            point['artifact']=save(directory/('point-'+str(point['point']['chosen']['step'])+'.pt'),payload,True)
            for trial in point['trials']:
                a=trial['action'];trial['output_tree_sha256']=tree_digest((payload[a+'_conditional'],payload[a+'_unconditional']))
                if trial['round']=='WARMUP':trial['interval']['synchronized_wall_seconds']=1000.
            if row['mode']=='AUDIT':states.append(copy.deepcopy(point['point']))
        if row['mode']=='BASELINE':
            bindings[row['scene']]=dict(final_artifact=row['final_artifact'],
                final_latent_sha256=row['final_latent_sha256'],actions=copy.deepcopy(row['actions']),
                decoded_video=dict(frames=93,RGB_sha256=hashlib.sha256(row['scene'].encode()).hexdigest()))
    scope=dict(requests=[dict(name=n) for n in names],complete_parent_matrix=plan,states=states,scope_counts=M.COUNTS)
    def loader(asset):return torch.load(artifact_path(root,asset),map_location='cpu',weights_only=True)
    def video(row):
        digest=bindings[row['scene']]['decoded_video']['RGB_sha256']
        return dict(decoded_video=dict(frames=93,RGB_sha256=digest),
            video_artifact=dict(decoded_rgb_sha256=[digest]*93))
    def old_raw(binding):return {k:copy.deepcopy(binding[k]) for k in ('final_artifact','final_latent_sha256','actions')}
    def old_video(binding):return dict(decoded_video=copy.deepcopy(binding['decoded_video']))
    return scope,rows,dict(bindings=bindings),loader,video,old_raw,old_video


def run(args,rows=None,video=None,exit_code=0):
    scope,original,baseline,loader,inspect,old_raw,old_video=args
    rows=original if rows is None else rows
    result=M.audit_rows(rows,scope,baseline,loader,video or inspect,old_raw,old_video,expected_shape=SHAPE)
    result.update(M.summarize(result,scope,observed_paths=len(rows),child_exit_code=exit_code))
    return result


class ActionPrice12PostControls(unittest.TestCase):
    def test_all12_files_full_guided_and_all512_intervals_modes_remain_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            result=run(fixture(folder))
            self.assertEqual(result['status'],M.COMPLETE_STATUS);self.assertTrue(result['all_requested_measurements_valid'])
            self.assertEqual(result['registered_total_parent_positions'],12);self.assertEqual(result['raw_model_pass_paths'],12)
            self.assertEqual(result['verified_parent_tensor_files'],24);self.assertEqual(result['verified_parent_tensors'],444)
            self.assertEqual(result['verified_price_point_files'],32);self.assertEqual(result['verified_price_point_tensors'],320)
            self.assertEqual(result['verified_trial_intervals'],512);self.assertEqual(result['verified_formal_intervals'],384)
            self.assertEqual(result['known_pair_computations'],944);self.assertEqual(len(result['separate_price_statistics']),32)
            for price in result['separate_price_statistics']:
                self.assertEqual(price['observed_scenes'],4);self.assertEqual(price['formal_intervals'],12)
                self.assertLess(price['scene_equal_mean_seconds'],1000.)
                self.assertFalse(price['warmup_intervals_included']);self.assertFalse(price['audit_lean_modes_combined'])

    def test_bad_video_retains_all_valid_raw_prices_but_never_full_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            args=fixture(folder);inspect=args[4];bad=args[1][5]['id']
            def video(row):
                if row['id']==bad:raise RuntimeError('SYNTHETIC_MISSING_MOOV_NOT_A_MODEL_FAILURE')
                return inspect(row)
            result=run(args,video=video)
            self.assertFalse(result['all_requested_measurements_valid']);self.assertEqual(len(result['rows']),12)
            self.assertEqual(result['raw_model_pass_paths'],12);self.assertEqual(result['accepted_93frame_videos'],11)
            self.assertEqual(result['verified_price_scenes'],4);self.assertEqual(result['verified_formal_intervals'],384)
            self.assertEqual(len(result['audit_failures']),1)
            self.assertTrue(any(s['video_gap_does_not_become_a_raw_teacher_failure'] for s in result['price_scenes']))

    def test_corrupt_point_file_and_missing_round_keep_full_scope_and_other_scene_prices(self):
        for mode in ('file','round'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                args=fixture(folder);point=args[1][1]['diagnostic_points'][0]
                if mode=='file':Path(point['artifact']['path']).write_bytes(b'SYNTHETIC_CORRUPT_ORIGINAL_PT')
                else:point['trials'].pop()
                result=run(args)
                self.assertFalse(result['all_requested_measurements_valid']);self.assertEqual(len(result['rows']),12)
                self.assertEqual(result['verified_price_scenes'],3);self.assertEqual(len(result['unavailable_price_scenes']),1)
                self.assertTrue(result['audit_failures']);self.assertTrue(all(p['observed_scenes']==3 for p in result['separate_price_statistics']))

    def test_trial_source_substitution_and_asset_alias_are_rejected(self):
        for mode in ('point','alias','teacher'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                args=fixture(folder);row=args[1][1]
                if mode=='point':row['diagnostic_points'][0]['point']['chosen']['source_birth']-=1
                elif mode=='alias':row['diagnostic_points'][1]['artifact']=copy.deepcopy(row['diagnostic_points'][0]['artifact'])
                else:row['online_teacher_calls']=1
                result=run(args)
                self.assertFalse(result['all_requested_measurements_valid']);self.assertEqual(result['rows'][1]['status'],'COMPLETE')
                self.assertEqual(result['rows'][1]['raw_model_audit'],'AUDIT_FAILURE_RETAINED')
                self.assertEqual(result['verified_price_scenes'],3);self.assertEqual(len(result['rows']),12)

    def test_original_partial_prefix_is_not_completed_or_filled_with_zero_prices(self):
        with tempfile.TemporaryDirectory() as folder:
            args=fixture(folder);result=run(args,rows=args[1][:3],exit_code=1)
            self.assertEqual(result['original_runner_paths'],3);self.assertEqual(len(result['rows']),12)
            self.assertEqual(result['original_parent_outcomes'],dict(COMPLETE=3,NOT_REACHED=9))
            self.assertEqual(result['verified_price_scenes'],1);self.assertEqual(result['known_pair_computations'],236)
            self.assertFalse(result['all_requested_measurements_valid'])
            self.assertTrue(all(not p['complete_scene_support'] for p in result['separate_price_statistics']))

    def test_text_and_video_rejections_remain_distinct_and_raw_video_rejection_prices_survive(self):
        for mode in ('TEXT_REJECTED','VIDEO_REJECTED'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                args=fixture(folder)
                for row in args[1][3:6]:
                    row['status']=mode;row.pop('video_path',None)
                    if mode=='TEXT_REJECTED':
                        row.update(solver_steps=0,guided_pairs=0,actual_pair_computations=0,
                            actions=[],A_history=[],source_history=[],diagnostic_points=[])
                        for key in ('final_artifact','guided_artifact','final_latent_sha256','guided_tree_sha256','guided_outputs'):row.pop(key,None)
                result=run(args)
                self.assertFalse(result['all_requested_measurements_valid']);self.assertEqual(len(result['rows']),12)
                self.assertEqual(result['original_parent_outcomes'][mode],3)
                self.assertEqual(result['verified_price_scenes'],3 if mode=='TEXT_REJECTED' else 4)
                self.assertFalse(result['audit_failures'])


if __name__=='__main__':unittest.main()
