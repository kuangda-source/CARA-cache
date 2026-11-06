"""Run affected endpoint routes under the original bounded GPU-hidden worker."""
from pathlib import Path
import sys
import types

STAGE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(STAGE/'src'),str(STAGE/'scripts'),str(STAGE/'tests')]


def run_endpoint(*args,**kwargs):
    import unittest
    suite=unittest.TestSuite()
    for pattern in ('test_cara_budget_search_r1.py','test_cara_budget_search_journal_r1.py','test_cara_budget_rgb_objective_r1.py'):
        suite.addTests(unittest.defaultTestLoader.discover(str(STAGE/'tests'),pattern=pattern))
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful() or tested.testsRun!=31:
        raise ValueError('All31 component controls required in this host runtime')
    import check_cara_budget_endpoint_routes_r1
    result=check_cara_budget_endpoint_routes_r1.run(*args,**kwargs)
    result['budget_component_unit_controls']=tested.testsRun
    return result


if __name__=='__main__':
    routes=types.ModuleType('check_cara_fast_binding_routes_r2')
    routes.run=run_endpoint
    sys.modules[routes.__name__]=routes
    from check_cara_fast_binding_cpu_r2 import main
    main()
