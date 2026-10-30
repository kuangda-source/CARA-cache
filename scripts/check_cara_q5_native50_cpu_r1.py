"""Run the Q5 Native component using the existing bounded GPU-hidden worker."""
from pathlib import Path
import sys
import types

STAGE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(STAGE/'src'),str(STAGE/'scripts'),str(STAGE/'tests')]


def run_q5(*args,**kwargs):
    import check_cara_q5_native50_routes_r1
    return check_cara_q5_native50_routes_r1.run(*args,**kwargs)


if __name__=='__main__':
    routes=types.ModuleType('check_cara_fast_binding_routes_r2');routes.run=run_q5
    sys.modules[routes.__name__]=routes
    from check_cara_fast_binding_cpu_r2 import main
    main()
