import unittest
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.policy_generator_r1.proposal_tables import Costs


class ProtectedPrices(unittest.TestCase):
    def fixture(self):
        p=Profile(5,(1,5),3,2,1,'explicit-asset-profile')
        return p,Costs((4.,)*5,(None,1.,1.,1.,None),
            {.5:(None,2.,2.,2.,None),1.:(None,3.,3.,3.,None)},
            1.,p.identity,'non-overlapping-actual-intervals','OBSERVED_COMPONENT_PROPOSAL_COSTS')

    def test_unavailable_mandatory_dense_readouts_are_not_fabricated_prices(self):
        p,c=self.fixture();self.assertIs(c.validate(p),c)

    def test_missing_legal_readout_or_any_dense_price_still_refused(self):
        p,c=self.fixture()
        for d,C in [((None,4.,4.,4.,4.),c.C_seconds),(c.dense_seconds,(None,None,1.,1.,None))]:
            with self.assertRaises(ValueError):Costs(d,C,c.A_seconds_by_alpha,1.,p.identity,c.measurement_protocol,c.evidence_kind).validate(p)


if __name__=='__main__':unittest.main()
