"""CPU probe assembly keeps52 positions while only two new pairs are scored."""
import copy
from pathlib import Path
import tempfile
import unittest

import check_cara_source_lifecycle_p1_score_fixture_r1 as fixture
from check_cara_source_lifecycle_p1_post_host_cpu_r1 import prepared_packet
from wcomr.cara_source_lifecycle_p1_scores_r1 import bind_post_scorer
from wcomr.cara_fast_spec_r1 import digest


class P1PostProbePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f,cls.packet=fixture.packet()

    @classmethod
    def tearDownClass(cls):cls.f.doCleanups()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.stage=Path(self.temp.name)/'.sync/cara-source-lifecycle-P1-post-CPU-assembly';self.stage.mkdir(parents=True)
        self.media={}
        for i in range(2):
            for side in ('candidate','reference'):
                name=side+'-'+str(i)+'.mp4'
                self.media[name]=dict(video=dict(path=str(self.stage/name),sha256=digest(name)),
                    decoded=dict(RGB_sha256=digest('RGB'+name),frames=93,shape=[93,64,64,3],fps=16,PTS=[[j,16] for j in range(93)]))
        self.media['bad-1.mp4']=dict(video=dict(path=str(self.stage/'bad-1.mp4'),sha256=digest('bad')),
                                     decoded=self.media['candidate-1.mp4']['decoded'])

    def test_two_new_plus50_simulated_rows_preserve52_quality_positions(self):
        packet=prepared_packet(self.packet,self.stage,self.media)
        config=bind_post_scorer(packet,dict(torch_home='/CPU/torch',piq_site='/CPU/piq',weights_sha256={}),cpu_validation=True)
        self.assertEqual(len(config['manifest']['quality_positions']),52)
        self.assertEqual(len(config['manifest']['new_pairs']),2)
        self.assertEqual(len(config['manifest']['internal_rows']),50)

    def test_failed_packet_only_changes_the_second_new_candidate(self):
        packet=prepared_packet(self.packet,self.stage,self.media,failed=True)
        self.assertEqual(packet['manifest']['new_pairs'][1]['candidate']['path'],self.media['bad-1.mp4']['video']['path'])
        self.assertEqual(len(packet['manifest']['new_pairs']),2)
        self.assertEqual(packet['manifest']['new_pairs'][0]['candidate']['path'],self.media['candidate-0.mp4']['video']['path'])

    def test_original_fixture_packet_is_never_modified(self):
        before=copy.deepcopy(self.packet);prepared_packet(self.packet,self.stage,self.media)
        self.assertEqual(self.packet,before)


if __name__=='__main__':unittest.main()
