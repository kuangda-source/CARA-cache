"""Exercise the pinned official request reset body with a CPU-only stand-in."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from wcomr.mid_scope import request_wc_gate


def test_official_reset_initial35_request70_before_first_forward():
    source=Path(os.environ.get('WC_LIFECYCLE_SOURCE',str(Path(__file__).resolve().parents[1]/
        'vendor/WorldCache/Models/Cosmos-Predict2.5/cosmos_predict2/_src/predict2/inference/video2world.py')))
    nodes=[n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.If)
        and ast.unparse(n.test)=='self.worldcache_enabled'
        and any(isinstance(a,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='target_steps' for t in a.targets)
                for a in n.body)]
    assert len(nodes)==1,'Pinned request-reset block missing/ambiguous'
    net=SimpleNamespace(worldcache_num_steps=35,probe_depth=2,cnt=29)
    with TestCase().assertRaises(ValueError):request_wc_gate(net,35,2)
    namespace={'self':SimpleNamespace(worldcache_enabled=True,model=SimpleNamespace(net=net)),'num_steps':35}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
    request_wc_gate(net,35,2)
    assert net.worldcache_num_steps==70 and net.cnt==0 and net.residual_cache==[None,None]
    with TestCase().assertRaises(ValueError):request_wc_gate(net,36,2)
    with TestCase().assertRaises(ValueError):request_wc_gate(net,35,3)
