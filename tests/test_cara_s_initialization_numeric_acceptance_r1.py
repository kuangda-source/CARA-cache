"""Semantic rejection controls on the original numerical CPU capture."""
import ast
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from accept_cara_s_initialization_numeric_cpu_r1 import accept,encoded_sha
from cara_s_initialization_numeric_cpu_r3 import CONTRACT,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE


class SourceClosure(unittest.TestCase):
    def test_flow_axis_is_bound_in_card_and_scope(self):
        from wcomr.cara_fast_binding_r2 import load_card
        from wcomr.cara_fast_spec_r1 import digest,profile_from,policy_from_mask
        source=ast.parse((ROOT/'tests/check_cara_s_initialization_numeric_routes_r3.py').read_text())
        function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='cpu_fragment')
        ns=dict(ROOT=ROOT,CONTRACT=CONTRACT,json=json,load_card=load_card,digest=digest,
                profile_from=profile_from,policy_from_mask=policy_from_mask)
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<pure CPU fragment>','exec'),ns)
        scopes=[]
        for flow in (False,True):
            card,contract=ns['cpu_fragment'](flow)
            self.assertEqual(card['roles']['ALLD']['settings'],
                {**contract['base_execution_settings'],'worldcache_flow_enabled':flow})
            self.assertEqual(digest({k:v for k,v in card.items() if k!='scope_sha256'}),card['scope_sha256'])
            scopes.append(card['scope_sha256'])
        self.assertNotEqual(*scopes)

    def test_old_control_parameter_dependencies_registered(self):
        source=ROOT/'tests/check_cara_s_initialization_numeric_routes_r3.py'
        refs={CONTRACT}
        for node in ast.walk(ast.parse(source.read_text())):
            if (isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div)
                    and isinstance(node.left,ast.Name) and node.left.id=='ROOT'
                    and isinstance(node.right,ast.Constant) and isinstance(node.right.value,str)):
                refs.add(node.right.value)
        base=json.loads((ROOT/BASE_CAPTURE).read_text())['result']['registration']['payload_sha256']
        self.assertTrue(refs <= set(base)|set(OVERLAY),refs-(set(base)|set(OVERLAY)))
        self.assertIn('manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json',refs)
        self.assertIn('manifests/wc_math_n2_frozen_parameters_r1_20261012.json',refs)


class NumericalAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture=json.loads((ROOT/'reports/cara_s_initialization_numeric_CPU_R3_operational_r2_20261031.json').read_text())
        cls.launch=json.loads((ROOT/'reports/cara_s_initialization_numeric_CPU_launch_r3_20261031.json').read_text())

    def test_original(self):
        self.assertEqual(accept(self.capture,self.launch)['ordinary_pairs'],1728)

    def mutate(self,change,message):
        c=copy.deepcopy(self.capture)
        change(c['result'])
        c['result']['CPU_proof_sha256']=encoded_sha(c['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):
            accept(c,self.launch)

    def test_running(self):
        self.mutate(lambda c:c['container_state'].update(Running=True),'Exited zero')

    def test_changed_sources(self):
        self.mutate(lambda c:c.update(payload_intact=False),'source/runtime differs')

    def test_extra_swap(self):
        self.mutate(lambda c:c['host_config'].update(MemorySwap=8589934592),'resource boundary')

    def test_missing_flow(self):
        self.mutate(lambda c:c['CPU_proof']['numeric']['checks'].pop(),'Both flow modes')

    def test_unmatched_actual_flow(self):
        def change(c):
            row=c['CPU_proof']['numeric']['checks'][0]
            row['effective_settings']['worldcache_flow_enabled']=not row['flow']
        self.mutate(change,'Matched actual execution settings')

    def test_duplicate_policy_position(self):
        def duplicate(c):
            row=c['CPU_proof']['numeric']['checks'][0]
            row['comparisons'][1]=copy.deepcopy(row['comparisons'][0])
        self.mutate(duplicate,'Exact FIT/policy matrix')

    def test_trajectory_mismatch(self):
        self.mutate(lambda c:c['CPU_proof']['numeric']['checks'][0]['comparisons'][0].update(
            all36_guided_old_new_equal=False),'trajectory and output parity')

    def test_missing_failure(self):
        self.mutate(lambda c:c['CPU_proof']['numeric']['checks'][0]['failures'].pop(),'failure controls')

    def test_real_weights(self):
        self.mutate(lambda c:c['CPU_proof'].update(Cosmos_model_weights_loaded=True),'tiny CPU boundary')


if __name__=='__main__':
    unittest.main()
