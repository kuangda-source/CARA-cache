"""Synthetic mutations of a saved original proof, never new host acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from accept_cara_budget_endpoint_cpu_r2 import accept
from cara_budget_endpoint_cpu_hosts_r2 import STAGES, PARENTS, HOST_CONFIG


def rebind(capture):
    reg=capture['registration'];proof=capture['CPU_proof']
    reg_sha=hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()
    capture['registration_sha256']=reg_sha
    capture['launch']['registration_sha256']=reg_sha
    proof['registration_sha256']=reg_sha
    capture['CPU_proof_sha256']=hashlib.sha256((json.dumps(proof,indent=2,allow_nan=False)+'\n').encode()).hexdigest()


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        original=json.loads((ROOT/'reports/cara_budget_endpoint_four_card_CPU_original_capture_r3_20261030.json').read_text())
        self.captures=[]
        for host in ('four_card','two_card'):
            c=copy.deepcopy(original);c['host_config']=HOST_CONFIG.copy()
            c['launch']['host']=host;c['launch']['stage']='/CPU-FIXTURE/'+STAGES[host]
            c['CPU_proof']['host']=host
            c['registration']['host']=host;c['registration']['stage']=c['launch']['stage']
            c['registration']['base_registration_sha256']=json.loads((ROOT/PARENTS[host]).read_text())['registration_sha256']
            c['registration']['expected_host_config']=HOST_CONFIG.copy()
            rebind(c);self.captures.append(c)

    def run_accept(self):
        paths=[]
        for i,c in enumerate(self.captures):
            p=Path(self.tmp.name)/f'{i}.json';p.write_text(json.dumps(c));paths.append(p)
        return accept(paths)

    def test_complete_synthetic_pair(self):
        self.assertEqual(self.run_accept()['successful_tiny_paths_per_host'],54)

    def test_resource_contract_and_gpu_refused(self):
        for field,value in [('MemorySwap',8*2**30),('CpusetCpus','26'),('DeviceRequests',[{'Count':1}])]:
            with self.subTest(field=field):
                original=copy.deepcopy(self.captures[0]);self.captures[0]['host_config'][field]=value
                with self.assertRaises(ValueError):self.run_accept()
                self.captures[0]=original
        self.captures[0]['registration'].pop('expected_host_config');rebind(self.captures[0])
        with self.assertRaises(ValueError):self.run_accept()

    def test_partial_or_changed_proof_refused(self):
        self.captures[0]['CPU_proof']['numeric']['checks'].pop();rebind(self.captures[0])
        with self.assertRaises(ValueError):self.run_accept()

    def test_live_and_wrong_host_refused(self):
        self.captures[0]['container_state']['Running']=True
        with self.assertRaises(ValueError):self.run_accept()
        self.captures[0]['container_state']['Running']=False
        self.captures[0]['launch']['host']='two_card'
        with self.assertRaises(ValueError):self.run_accept()

    def test_tampered_hash_refused(self):
        self.captures[0]['CPU_proof']['numeric']['budget_component_unit_controls']=30
        with self.assertRaises(ValueError):self.run_accept()


if __name__=='__main__':unittest.main()
