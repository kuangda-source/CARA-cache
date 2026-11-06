"""Real temporary staging and mocked Popen; never remote or model execution."""
import ast
import copy
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('metric_cpu_staging_only',ROOT/'scripts/launch_wc_N10_models_cpu_r1.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


def fixture(root):
    (root/'reports').mkdir();(root/'.sync').mkdir()
    (root/'reports/gpu-budget-v2.json').write_text(json.dumps(dict(jobs={'old':dict(status='SETTLED')})))
    dino=root/'original_DINO';dino.mkdir();(dino/'hubconf.py').write_bytes(b'# SYNTHETIC_ONLY\n')
    files={'upstream/vbench/__init__.py':b'# SYNTHETIC_ONLY\n',
           'scripts/evaluate_wc_N10_models_cpu_bundle_r1.py':b'# NO MODEL OR REAL CHILD EXECUTION\n'}
    metadata=dict(stage='.sync/wc-N10-models-cpu-synthetic',source_revision='SYNTHETIC_NOT_REAL_DISPATCH',
        roles=['DINO','AMT_S','RAFT_THINGS','ViCLIP','MUSIQ_SPAQ'],official_VBench_commit='SYNTHETIC',
        resource_capture_sha256='a'*64,payload_sha256={n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
        DINO_source_root=str(dino),DINO_source_records=[dict(relative='hubconf.py',bytes=17,
            sha256=hashlib.sha256((dino/'hubconf.py').read_bytes()).hexdigest())])
    metadata['DINO_source_records'][0]['bytes']=(dino/'hubconf.py').stat().st_size
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for n,raw in files.items():
            info=tarfile.TarInfo(n);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
    return metadata,stream.getvalue(),dino


def bootstrap(root,metadata,archive):
    tree=ast.parse(M.BOOT)
    class RootFixture(ast.NodeTransformer):
        def visit_Constant(self,node):
            if node.value=='/home/gaokuangda/data/gkd/worldcache_omr':return ast.copy_location(ast.Constant(str(root)),node)
            return node
    tree=ast.fix_missing_locations(RootFixture().visit(tree))
    stdin=SimpleNamespace(buffer=io.BytesIO(json.dumps(metadata).encode()+b'\n'+archive));out=io.StringIO()
    original=Path.read_text
    def read(path,*args,**kwargs):
        if str(path)=='/proc/123/stat':return '123 (SYNTHETIC) '+' '.join(['R']+['0']*18+['12345'])
        return original(path,*args,**kwargs)
    with patch.object(sys,'stdin',stdin),patch.object(Path,'read_text',read), \
         patch('subprocess.Popen',return_value=SimpleNamespace(pid=123)) as child, \
         patch('os.nice') as nice,redirect_stdout(out):
        try:exec(compile(tree,'SYNTHETIC_LOCAL_CPU_BOOT_ONLY','exec'),{})
        except SystemExit as stop:
            if stop.code!=0:raise
    return json.loads(out.getvalue()),child,nice


class ModelCPUStagingControls(unittest.TestCase):
    def test_full_fresh_stage_preserves_original_DINO_and_single_cpu_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);metadata,archive,dino=fixture(root);original=(dino/'hubconf.py').read_bytes()
            result,child,nice=bootstrap(root,metadata,archive);stage=root/metadata['stage']
            reg=json.loads((stage/'registration.json').read_text())
            self.assertEqual(reg['roles'],metadata['roles']);self.assertEqual(child.call_count,1)
            self.assertEqual((stage/'external/dino/hubconf.py').read_bytes(),original)
            self.assertEqual((dino/'hubconf.py').read_bytes(),original)
            self.assertEqual(child.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'],'')
            self.assertEqual(result['GPU_submissions'],0);self.assertEqual(nice.call_args.args,(10,))

    def test_registered_gpu_mainline_defers_before_stage_or_child(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);metadata,archive,_=fixture(root)
            (root/'reports/gpu-budget-v2.json').write_text(json.dumps(dict(jobs={'MAIN':dict(status='RESERVED_OR_RUNNING')})))
            result,child,nice=bootstrap(root,metadata,archive)
            self.assertFalse(result['stage_created']);self.assertEqual(child.call_count,0)
            self.assertEqual(nice.call_count,0);self.assertFalse((root/metadata['stage']).exists())

    def test_changed_archive_is_refused_without_any_cpu_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);metadata,archive,_=fixture(root)
            metadata['payload_sha256'][next(iter(metadata['payload_sha256']))]='0'*64
            with self.assertRaises(AssertionError):bootstrap(root,metadata,archive)
            self.assertFalse((root/metadata['stage']).exists())

    def test_existing_stage_is_not_overwritten_or_redispatched(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);metadata,archive,_=fixture(root);stage=root/metadata['stage'];stage.mkdir()
            marker=stage/'original.txt';marker.write_text('PRESERVE')
            with self.assertRaises(AssertionError):bootstrap(root,metadata,archive)
            self.assertEqual(marker.read_text(),'PRESERVE')

    def test_unreceived_resource_refuses_before_git_or_ssh(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'not_accepted_resource.json'
            path.write_text(json.dumps(dict(status='N10_ORIGINAL_RESOURCE_ONCE_CAPTURE',original_process_alive=True,
                                             launch={},result={})))
            with patch.object(M.subprocess,'check_output') as git,self.assertRaises(ValueError):
                M.packet(path,'.sync/wc-N10-models-cpu-synthetic')
            git.assert_not_called()


if __name__=='__main__':unittest.main()
