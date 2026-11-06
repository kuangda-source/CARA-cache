"""Reuse the GPU-hidden bounded R2 CPU worker with the affected F18 checks."""
from pathlib import Path
import sys
import types

STAGE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(STAGE/'src'), str(STAGE/'scripts'), str(STAGE/'tests')]


def run_f18(*args, **kwargs):
    # Import production modules only after the original worker installs its
    # no-CUDA/no-weights/offline guards and imports the real runtime modules.
    import check_cara_fast_f18_routes_r1
    return check_cara_fast_f18_routes_r1.run(*args, **kwargs)


if __name__ == '__main__':
    routes = types.ModuleType('check_cara_fast_binding_routes_r2')
    routes.run = run_f18
    sys.modules[routes.__name__] = routes
    from check_cara_fast_binding_cpu_r2 import main
    main()
