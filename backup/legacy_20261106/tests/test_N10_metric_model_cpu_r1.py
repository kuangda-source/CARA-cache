"""Tiny pre-import and network-boundary fixtures; no model proof or GPU work."""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'scripts/evaluate_wc_N10_metric_model_cpu_r1.py'
SPEC=importlib.util.spec_from_file_location('metric_cpu_source_only',SOURCE)
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
BPE=ROOT/'.sync/wc-N10-official-tokenizer-pinned-r1-20261016/bpe_simple_vocab_16e6.txt.gz'


def fixture(root):
    stage=root/'stage';stage.mkdir();resources={};weights={}
    for role in M.ROLES:
        target=root/(role+'.pth');raw=('SYNTHETIC_NOT_MODEL_'+role).encode();target.write_bytes(raw)
        digest=hashlib.sha256(raw).hexdigest();weights[role]=(len(raw),digest)
        resources[role]=dict(path=str(target),bytes=len(raw),sha256=digest)
    bpe=stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz';bpe.parent.mkdir(parents=True);shutil.copyfile(BPE,bpe)
    manifest=stage/'model-resources.json';manifest.write_text(json.dumps(dict(resources=resources)))
    registration=dict(purpose='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING',roles=list(M.ROLES),
        payload_sha256={'model-resources.json':M.sha(manifest),str(bpe.relative_to(stage)):M.sha(bpe)})
    (stage/'registration.json').write_text(json.dumps(registration))
    return stage,resources,weights,registration


class MetricCPUBoundaries(unittest.TestCase):
    def test_all_five_resources_and_real_tokenizer_verified_before_torch_import(self):
        with tempfile.TemporaryDirectory() as folder:
            stage,resources,weights,_=fixture(Path(folder));before='torch' in sys.modules
            with patch.object(M,'WEIGHTS',weights):
                reg,manifest,current=M.preflight(stage,'DINO')
            self.assertEqual(reg['roles'],list(M.ROLES));self.assertEqual(str(current),resources['DINO']['path'])
            self.assertEqual('torch' in sys.modules,before)

    def test_missing_later_role_does_not_silently_become_four_model_cpu(self):
        with tempfile.TemporaryDirectory() as folder:
            stage,resources,weights,_=fixture(Path(folder));Path(resources['ViCLIP']['path']).unlink()
            with patch.object(M,'WEIGHTS',weights),self.assertRaises(ValueError):M.preflight(stage,'DINO')

    def test_changed_checkpoint_or_source_is_refused_before_import(self):
        for kind in ('checkpoint','source','bpe'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as folder:
                stage,resources,weights,registration=fixture(Path(folder))
                if kind=='checkpoint':
                    p=Path(resources['DINO']['path']);p.write_bytes(b'X'*p.stat().st_size)
                elif kind=='source':(stage/'model-resources.json').write_text('{}')
                else:
                    p=stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz';p.write_bytes(b'INVALID_TOKENIZER')
                    registration['payload_sha256'][str(p.relative_to(stage))]=M.sha(p)
                    (stage/'registration.json').write_text(json.dumps(registration))
                with patch.object(M,'WEIGHTS',weights),self.assertRaises(ValueError):M.preflight(stage,'DINO')

    def test_payload_cannot_execute_source_through_parent_symlink_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);stage,_,weights,registration=fixture(root)
            outside=root/'outside';outside.mkdir();p=outside/'unexpected.py';p.write_text('pass\n')
            (stage/'upstream').symlink_to(outside,target_is_directory=True)
            registration['payload_sha256']['upstream/unexpected.py']=M.sha(p)
            (stage/'registration.json').write_text(json.dumps(registration))
            with patch.object(M,'WEIGHTS',weights),self.assertRaises(ValueError):M.preflight(stage,'DINO')

    def test_network_and_download_processes_are_process_locally_blocked(self):
        events=[]
        with ExitStack() as stack:
            for obj,name in ((M.socket,'create_connection'),(M.socket.socket,'connect'),
                (M.socket.socket,'connect_ex'),(M.urllib.request,'urlopen'),
                (M.subprocess,'run'),(M.subprocess,'Popen')):
                stack.enter_context(patch.object(obj,name))
            M.deny_external_access(events)
            with self.assertRaises(RuntimeError):M.urllib.request.urlopen('https://invalid.example/SYNTHETIC')
            with self.assertRaises(RuntimeError):M.subprocess.run(['wget','SYNTHETIC'])
        self.assertEqual(len(events),2)


if __name__=='__main__':unittest.main()
