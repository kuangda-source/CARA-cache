"""Actual R1 metadata and strict local-version exception, never new model scores."""
from contextlib import ExitStack
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('actual_CPU_repair_source',ROOT/'scripts/evaluate_wc_N10_metric_model_cpu_r1.py')
B=load('actual_CPU_bundle_repair',ROOT/'scripts/evaluate_wc_N10_models_cpu_bundle_r1.py')


def original():
    return json.loads(gzip.decompress((ROOT/'reports/wc_paper_N10_full_five_model_CPU_R1_collection_20261018_0207.json.gz').read_bytes()))


class ActualCPURepairs(unittest.TestCase):
    def test_exact_local_git_version_only(self):
        for argv in (['git','version'],['git','--version'],['/usr/bin/git','version']):
            self.assertTrue(M.read_only_git_version(argv))
        for argv in (['git','clone','https://invalid.example/repo'],['git','fetch'],['git','config','--list'],['git','version','--extra'],['/tmp/git','version'],'git --version'):
            self.assertFalse(M.read_only_git_version(argv))
        self.assertFalse(M.read_only_git_version(['git','version'],shell=True))
        self.assertFalse(M.read_only_git_version(['git','version'],executable='/usr/bin/curl'))

    def test_original_downloads_sockets_and_other_git_still_blocked(self):
        events=[];permitted=[]
        with ExitStack() as stack:
            run=stack.enter_context(patch.object(M.subprocess,'run'))
            popen=stack.enter_context(patch.object(M.subprocess,'Popen'))
            for obj,name in ((M.socket,'create_connection'),(M.socket.socket,'connect'),(M.socket.socket,'connect_ex'),(M.urllib.request,'urlopen')):
                stack.enter_context(patch.object(obj,name))
            M.deny_external_access(events,permitted)
            M.subprocess.run(['git','version']);M.subprocess.Popen(['/usr/bin/git','--version'])
            self.assertEqual(events,[]);self.assertEqual(len(permitted),2)
            self.assertEqual(run.call_count,1);self.assertEqual(popen.call_count,1)
            for argv,kw in ((['git','clone','https://invalid.example/repo'],{}),(['wget','https://invalid.example/file'],{}),(['curl','https://invalid.example/file'],{}),(['git','version'],{'shell':True}),(['git','version'],{'executable':'/usr/bin/curl'})):
                with self.assertRaises(RuntimeError):M.subprocess.run(argv,**kw)
            with self.assertRaises(RuntimeError):M.socket.create_connection(('invalid.example',443))
        self.assertEqual(len(events),6)
        self.assertTrue(all(v['kind']=='NETWORK_OR_DOWNLOAD_BLOCKED' and v['guard_stack'] for v in events))

    def test_actual_DINO_aspect_preserving_interface_and_original_AMT_identity(self):
        v=original();reg=v['registration'];resources=v['files']['model-resources.json']['data']['resources']
        for role in ('DINO','AMT_S','RAFT_THINGS'):
            raw=v['files']['CPU-model-'+role+'.json']['data']
            result=B.accept_role(role,raw,reg,v['registration_sha256'],resources)
            self.assertEqual(result['status'],'REAL_MODEL_CPU_ROLE_ACCEPTED_NOT_QUALITY')
        d=v['files']['CPU-model-DINO.json']['data']
        self.assertEqual(d['actual']['actual_model_input_shape'],[2,3,224,398])

    def test_fake_square_DINO_or_AMT_escape_and_hash_rejected(self):
        v=original();reg=v['registration'];resources=v['files']['model-resources.json']['data']['resources']
        for case in ('square','escape','hash'):
            role='DINO' if case=='square' else 'AMT_S';raw=copy.deepcopy(v['files']['CPU-model-'+role+'.json']['data'])
            if case=='square':raw['actual']['actual_model_input_shape']=[2,3,224,224]
            elif case=='escape':raw['actual']['model_source']=reg['stage']+'/../outside/AMT-S.py'
            else:raw['actual']['model_source_sha256']='0'*64
            with self.subTest(case=case),self.assertRaises(ValueError):B.accept_role(role,raw,reg,v['registration_sha256'],resources)


if __name__=='__main__':unittest.main()
