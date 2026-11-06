"""Reject incomplete or altered actual CPU captures without rerunning the server."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_cara_pg_p1_production_cpu_r1 import accept

class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads((ROOT/'reports/cara_PG_P1_production_CPU_terminal_r2_20261023.json').read_text())
    def test_original_complete_accepts(self):
        self.assertTrue(accept(self.original)['production_entry_CPU_accepted'])
        self.assertFalse(accept(self.original)['GPU_dispatch_ready'])
    def test_running_or_failed_container_rejected(self):
        for key,value in [('Running',True),('ExitCode',1),('OOMKilled',True)]:
            v=copy.deepcopy(self.original);v['container']['state'][key]=value
            with self.assertRaises(ValueError):accept(v)
    def test_GPU_exposed_or_uncapped_container_rejected(self):
        for key,value in [('devices',[{'x':1}]),('device_requests',[{'x':1}]),('nano_cpus',2*10**9),('memory_bytes',0)]:
            v=copy.deepcopy(self.original);v['container'][key]=value
            with self.assertRaises(ValueError):accept(v)
    def test_source_change_and_missing_flow_rejected(self):
        v=copy.deepcopy(self.original);v['payload_actual_sha256']['changed']='x'
        with self.assertRaises(ValueError):accept(v)
        v=copy.deepcopy(self.original);v['proof']['data']['numeric']['checks'].pop()
        with self.assertRaises(ValueError):accept(v)
    def test_numerical_or_guard_codec_failure_rejected(self):
        for key in ('Native_allD_guided_final_RGB_equal','nonfinite_restored_fullD_equals_independent_policy','writer_failure_cleanup'):
            v=copy.deepcopy(self.original);v['proof']['data']['numeric']['checks'][0][key]=False
            with self.assertRaises(ValueError):accept(v)
        v=copy.deepcopy(self.original);v['proof']['data']['codec']['RGB_frames']=92
        with self.assertRaises(ValueError):accept(v)
if __name__=='__main__':unittest.main()
