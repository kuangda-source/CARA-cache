"""CPU installer/capture derivations and full source-packet closure controls."""
import ast
import gzip
import json
import shlex
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_repair_cpu_staging_r2 import derive,namespace,EXTRA_ENTRIES,EXTRA_FILES
from wcomr.frozen_repair180_r2 import CONFIG,original
from wcomr.immutable_stage_payload_r1 import plan

ROOT=Path(__file__).resolve().parents[1]


class RepairCPUStaging(unittest.TestCase):
    def test_three_tools_preserve_exact_base_source_and_inverse(self):
        for kind in ('deploy','capture','accept'):
            source,proof=derive(ROOT,kind)
            self.assertTrue(proof['inverse_bytes_and_AST_equal'])
            self.assertFalse(proof['original_stage_written'])
            self.assertEqual(proof['GPU_submissions'],0)
            if kind=='capture':
                self.assertIn("CONFIG = 'configs/wc_paper_N07_refusal_repair180_r2_20261016.json'",source)
            else:self.assertIn('frozen_repair',source)
        source,_=derive(ROOT,'deploy')
        self.assertIn('expected_CPU_commands=9',source)
        self.assertIn('run_wc_paper_N07_repair_production_cpu_bundle_r2.py',source)
        self.assertIn('validate_repair_proof(ROOT, config)',source)
        self.assertIn('validate_all_entries(ROOT)',source)

    def test_full_packet_includes_dynamic_entries_all_refusal_sources_and_numeric99(self):
        values,_=namespace(ROOT,'deploy')
        self.assertTrue(set(EXTRA_ENTRIES).issubset(values['ENTRIES']))
        self.assertTrue(set(EXTRA_FILES).issubset(values['TESTS']))
        numeric=original.sampling_source_closure(ROOT)
        packet=plan(ROOT,config_roots=[CONFIG],python_entrypoints=values['ENTRIES'],extra_files=values['TESTS'],
            base_registration_sha256='a'*64,base_source_revision='SYNTHETIC_PACKET_CLOSURE_NOT_DEPLOYED',numeric_sources=numeric)
        files=packet['overlay_sha256'];self.assertEqual(packet['numerical_sources_verified'],99)
        for name in EXTRA_ENTRIES+EXTRA_FILES:
            self.assertIn(name,files)
        for name in ('src/wcomr/automatic_quality_r1.py','tests/test_frozen_shared_production_r1.py',
                     'src/wcomr/frozen_repair_entry_r2.py','src/wcomr/frozen_repair_cpu_staging_r2.py'):
            self.assertIn(name,files)
        self.assertEqual(files[CONFIG],original.sha(ROOT/CONFIG))

    def test_original_tool_tampering_refuses_derivation(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);path=root/'scripts/capture_wc_paper_N07_production_cpu_r1.py';path.parent.mkdir()
            path.write_text('raise RuntimeError("ALTERED ORIGINAL")\n')
            with self.assertRaises(ValueError):derive(root,'capture')

    def test_remote_observer_does_not_import_the_Torch_production_contract(self):
        values,_=namespace(ROOT,'capture');seen=[]
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);launch=folder/'launch.json';output=folder/'capture.json.gz'
            launch.write_text(json.dumps({'launch':dict(first_collection_not_before_unix=0,
                stage='/synthetic/stage',pid=999,source_revision='SYNTHETIC_NO_SSH',registration_sha256='a'*64)}))
            reply=dict(process=dict(pid=999,state=None),payload_verified={},
                files=dict(bundle=dict(data=None),proof=dict(exists=False)))
            def fake(command,**kwargs):
                self.assertEqual(command[-2],'gkd_minchen')
                remote=shlex.split(command[-1]);self.assertEqual(remote[:2],['python3','-c'])
                source=remote[2];ast.parse(source);seen.append(source)
                self.assertNotIn('from wcomr.frozen_repair180_r2 import',source)
                self.assertIn("CONFIG = 'configs/wc_paper_N07_refusal_repair180_r2_20261016.json'",source)
                return subprocess.CompletedProcess(command,0,stdout=gzip.compress(json.dumps(reply).encode()),stderr=b'')
            args=type('Args',(),dict(launch_ref=launch,output=output))()
            with patch('argparse.ArgumentParser.parse_args',return_value=args),patch.object(values['subprocess'],'run',side_effect=fake):
                values['main']()
            self.assertEqual(len(seen),1);self.assertTrue(output.is_file())


if __name__=='__main__':unittest.main()
