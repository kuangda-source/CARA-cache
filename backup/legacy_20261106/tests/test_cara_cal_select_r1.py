import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from select_cara_cal_select_r1 import exclusion_closure,choose


class Selection(unittest.TestCase):
    def records(self):
        names=['av_a','av_a_long','human_1','human_2','robot_1','misc_1']
        return [dict(name=n,category=n.split('_')[0],group_members=[n],prompt_sha256=str(i)*64) for i,n in enumerate(names)]

    def test_suffix_and_longest_name_resolve_without_prefix_collision(self):
        rows=self.records()
        self.assertEqual(exclusion_closure(rows,['av_a_long_PG_SELECT_seed0'],[]),{'av_a_long'})

    def test_exposure_includes_any_dataset_category(self):
        rows=self.records()+[dict(name='industry_057',category='industry',group_members=['industry_057'],prompt_sha256='f'*64)]
        self.assertEqual(exclusion_closure(rows,['industry_057_seed0'],[]),{'industry_057'})

    def test_hash_matches_all_aliases_and_transitive_group_members(self):
        rows=self.records();rows[2]['prompt_sha256']=rows[3]['prompt_sha256']
        rows[3]['group_members']=['human_2','robot_1'];rows[4]['group_members']=['robot_1','misc_1']
        self.assertEqual(exclusion_closure(rows,[rows[2]['prompt_sha256']],[]),{'human_1','human_2','robot_1','misc_1'})

    def test_engineering_exclusion_closes_group(self):
        rows=self.records();rows[2]['group_members']=['human_1','human_2']
        self.assertEqual(exclusion_closure(rows,[],['human_2']),{'human_1','human_2'})

    def test_selection_is_deterministic_under_input_order(self):
        rows=self.records();p=dict(salt='fixed',strata={'av':1,'non_av':1},count=2)
        a,_=choose(rows,{'av_a'},p);b,_=choose(rows[::-1],{'av_a'},p)
        self.assertEqual(a,b);self.assertEqual(a[0]['name'],'av_a_long')
        self.assertNotEqual(a[1]['category'],'av')

    def test_no_silent_replacement_of_missing_stratum(self):
        with self.assertRaises(ValueError):choose(self.records(),{'av_a','av_a_long'},dict(salt='fixed',strata={'av':1,'non_av':1},count=2))


if __name__=='__main__':unittest.main()
