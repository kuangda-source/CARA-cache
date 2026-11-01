"""Host-entry ordering with simulated allocation; never runs a GPU guardian."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock

from check_cara_source_lifecycle_p1_outer_fixture_r1 import Fixture
import cara_source_lifecycle_p1_host_entry_r1 as entry
from wcomr import cara_source_lifecycle_p1_dispatch_r1 as dispatch
from wcomr import cara_source_lifecycle_p1_service_r1 as service
from wcomr import cara_s_endpoint_host_guardian_r1 as guardian
from wcomr.gpu_budget_pool_v2 import atomic_json


class P1HostEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.f=Fixture(self.temp.name)

    def invoke(self,value):
        return patch.multiple(sys,argv=['entry','--project',str(self.f.project),'--stage',str(self.f.stage)],
                              stdin=io.StringIO(json.dumps(value)))

    def test_original_publication_then_one_service_inside_the_same_guardian(self):
        token=object();events=[]
        def published(*args):events.append('publish');return self.f.launch,self.f.storage
        def held(*args):events.append('service');return token
        def allocated(*args,**kwargs):events.append('allocate');self.assertIs(kwargs['fit_service'],token)
        with self.invoke({'sudo_password':'EXPLICIT_CPU_TEST_CREDENTIAL'}),\
                patch.object(dispatch,'publish_launch',side_effect=published),\
                patch.object(service,'HeldFITService',side_effect=held),patch.object(guardian,'allocate',side_effect=allocated):entry.main()
        self.assertEqual(events,['publish','service','allocate'])

    def test_missing_or_malformed_private_credential_cannot_publish(self):
        for value in ({},{'sudo_password':''},{'sudo_password':None},{'sudo_password':5},{'sudo_password':'CPU','other':True}):
            with self.invoke(value),patch.object(dispatch,'publish_launch') as publish:
                with self.subTest(value=value),self.assertRaises(ValueError):entry.main()
                publish.assert_not_called()

    def test_unregistered_host_entry_cannot_publish(self):
        reg=self.f.reg.copy();reg['payload_sha256']=dict(reg['payload_sha256'],**{dispatch.GUARDIAN:'f'*64})
        atomic_json(self.f.stage/'registration.json',reg)
        with self.invoke({'sudo_password':'CPU'}),patch.object(dispatch,'publish_launch') as publish:
            with self.assertRaisesRegex(ValueError,'source differs'):entry.main()
            publish.assert_not_called()


if __name__=='__main__':unittest.main()
