"""New-host dependency recovery and guard-boundary controls; no model fixture."""
import copy
import io
import json
from pathlib import Path
import sys
import tarfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from four_card_bank24_host_contract_r1 import archive_members, digest, legacy_bindings, quote_inventory, read
from check_wc_four_card_bank24_host_cpu_r1 import integration_source


def packed(items):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as archive:
        for name,body,kind in items:
            item=tarfile.TarInfo(name);item.size=len(body);item.type=kind
            if kind!=tarfile.REGTYPE:item.linkname='outside'
            archive.addfile(item,io.BytesIO(body) if kind==tarfile.REGTYPE else None)
    return stream.getvalue()


class ArchiveContract(unittest.TestCase):
    def setUp(self):self.expected={'a.json':digest(b'{}')}

    def test_exact_member(self):
        self.assertEqual(archive_members(packed([('a.json',b'{}',tarfile.REGTYPE)]),self.expected),{'a.json':b'{}'})

    def test_traversal(self):
        with self.assertRaises(ValueError):archive_members(packed([('../a',b'{}',tarfile.REGTYPE)]),{'../a':digest(b'{}')})

    def test_absolute(self):
        with self.assertRaises(ValueError):archive_members(packed([('/a',b'{}',tarfile.REGTYPE)]),{'/a':digest(b'{}')})

    def test_symlink(self):
        with self.assertRaises(ValueError):archive_members(packed([('a.json',b'',tarfile.SYMTYPE)]),self.expected)

    def test_hardlink(self):
        with self.assertRaises(ValueError):archive_members(packed([('a.json',b'',tarfile.LNKTYPE)]),self.expected)

    def test_duplicate(self):
        with self.assertRaises(ValueError):archive_members(packed([('a.json',b'{}',tarfile.REGTYPE)]*2),self.expected)

    def test_missing_and_extra(self):
        for items in [[],[('b.json',b'{}',tarfile.REGTYPE)]]:
            with self.assertRaises(ValueError):archive_members(packed(items),self.expected)

    def test_changed_and_oversized(self):
        with self.assertRaises(ValueError):archive_members(packed([('a.json',b'[]',tarfile.REGTYPE)]),self.expected)
        with self.assertRaises(ValueError):archive_members(packed([('a.json',b'{}',tarfile.REGTYPE)]),self.expected,limit=1)


class FrozenCardContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cap=read(ROOT/'reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_collection_20261019.json.gz')
        cls.old=read(ROOT/'reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_independent_acceptance_20261019.json')
        cls.entry=read(ROOT/'reports/wc_scout_BANK24_real_entry_CPU_R1_collection_20261018.json.gz')
        cls.gate=read(ROOT/'reports/wc_scout_CAL12_fourCAL_frozen_gate_20261019.json')
        cls.config=read(ROOT/'configs/wc_scout_bank24_production_entry_r1_20261018.json')
        cls.quote=read(ROOT/'reports/wc_scout_BANK24_whole_quote_R1_20261018.json')
        cls.rows=cls.entry['files']['proof']['data']['matrix']

    def bind(self,**kw):
        args=dict(capture=self.cap,accepted=self.old,entry=self.entry,gate=self.gate,config=self.config)
        args.update(kw);return legacy_bindings(**args)

    def test_original_whole_dependency(self):
        self.assertEqual(self.bind()['lifecycle_files'],1789)

    def test_short_or_mutated_dependency(self):
        for kind in ['short','changed']:
            value=copy.deepcopy(self.cap)
            if kind=='short':value['registration']['payload_sha256'].pop(next(iter(value['registration']['payload_sha256'])))
            else:value['registration']['source_revision']='0'*40
            with self.assertRaises(ValueError):self.bind(capture=value)

    def test_entry_subset_bytes(self):
        value=copy.deepcopy(self.entry);name=next(iter(value['registration']['payload_sha256']))
        value['registration']['payload_sha256'][name]='0'*64
        with self.assertRaises(ValueError):self.bind(entry=value)

    def test_frozen_mean_rank_direction_and_DEV(self):
        for key,val in [('direction','SMALLER_Z_KEEP_D'),('DEV_used_for_fit',True),('mu_RMS',0.),('threshold',0.)]:
            value=copy.deepcopy(self.gate);value[key]=val
            with self.assertRaises(ValueError):self.bind(gate=value)

    def test_request_Cfg_change(self):
        value=copy.deepcopy(self.config);value['requests'][0]['guidance']=8
        with self.assertRaises(ValueError):self.bind(config=value)

    def test_whole_inventory_is_not_new_host_price(self):
        value=quote_inventory(self.config,self.rows,self.quote)
        self.assertEqual(value['observer_paths'],14);self.assertEqual(value['A_positions'],8)
        self.assertIsNone(value['forecast_complete_GPUh']);self.assertFalse(value['quote_complete'])
        self.assertTrue(all(x is None for x in value['new_host_terms_seconds'].values()))

    def test_missing_warmup_or_native_is_refused(self):
        for rows in [self.rows[:-1],[r for r in self.rows if r['method']!='NATIVE35']]:
            with self.assertRaises(ValueError):quote_inventory(self.config,rows,self.quote)

    def test_new_probe_is_cpu_frontend_only(self):
        source=integration_source(Path('/tmp/owned-bank24-CPU-job'),guarded='import torch\n')
        compile(source,'<registered-front-end-CPU>','exec')
        self.assertIn('new_host_scope_production_CPU_accepted=False',source)
        self.assertIn('Ordinary guardrails required',source)
        self.assertIn('torch.cuda.get_device_capability()==(8,6)',source)
        self.assertNotIn('torch.compile=',source)

    def test_frozen_container_recipe_has_no_network_or_cache_mutation(self):
        value=read(ROOT/'manifests/wc_four_card_bank24_host_cpu_boundary_r1_20261022.json')
        self.assertTrue(value['offline_only'])
        self.assertTrue(value['torch_cache_readonly'])
        self.assertEqual(value['network'],'none')
        self.assertFalse(value['full_new_host_scope_production_CPU_accepted'])
        self.assertFalse(value['GPU_dispatch_ready'])


if __name__=='__main__':unittest.main()
