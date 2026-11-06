import unittest
from wcomr.stage_refresh_policy import StageRefreshPolicy


class StagePolicyTests(unittest.TestCase):
    def test_current_window_and_branch_cadence(self):
        p=StageRefreshPolicy((2,3,4));q=StageRefreshPolicy((2,3,4),2)
        self.assertEqual([n for n in range(1,37) if p.in_window(n)],[23,24,25,26,27])
        self.assertEqual([n for n in range(1,6) if q.select(n,cfg=0)],[1,3,5])
        self.assertEqual(q.to_dict()['first_solver_step'],23)
        self.assertFalse(q.to_dict()['requires_future_mask'])
        self.assertFalse(q.to_dict()['changes_official_cache_predicate'])

    def test_invalid_policy(self):
        for args in (((),),(list((2,3)),),((3,2),),((2,2),),((True,),),((2,),0),((2,),True),
                     ((2,),1,0,27),((2,),1,28,27),((2,),1,23,36),((2,),1,True,27),((2,),1,23,27.)):
            with self.subTest(args=args),self.assertRaises(ValueError):StageRefreshPolicy(*args)

    def test_invalid_current_step_and_ordinal(self):
        p=StageRefreshPolicy((2,3))
        for n in (0,37,True,23.,None):
            with self.subTest(step=n),self.assertRaises(ValueError):p.in_window(n)
        for n,cfg in ((0,0),(True,0),(1,2),(1,True)):
            with self.subTest(ordinal=n,cfg=cfg),self.assertRaises(ValueError):p.select(n,cfg=cfg)

    def test_invalid_layer_geometry(self):
        for layers in ((1,),(6,),(28,)):
            with self.subTest(layers=layers),self.assertRaises(ValueError):
                StageRefreshPolicy(layers).validate_geometry(2,28,(6,23,27))
        StageRefreshPolicy(tuple(v for v in range(2,28) if v not in (6,23,27))).validate_geometry(2,28,(6,23,27))


if __name__=='__main__':unittest.main()
