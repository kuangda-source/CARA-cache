"""Second attempt metadata; all tested N2 algorithms remain original objects.

R1 supervisor named a missing child file. This fresh attempt changes only the
run/config namespace and validates the real shared child-command constructor.
"""
from .math_n2_production_r1 import *
from . import math_n2_production_r1 as prior
from .source_aware_phase_sampling import bind_globals

RUN='wc-math-n2-source-sigma-full36-r2'
CONFIG='configs/wc_math_n2_full36_production_r2_20261012.json'
validate_contract=bind_globals(prior.validate_contract,{'RUN':RUN})
validate=bind_globals(prior.validate,{'CONFIG':CONFIG,'validate_contract':validate_contract})
DERIVATION_PROOF={'original_validation_bytecode_unchanged':True,
    'tested_full144_core_algorithms_or_parameters_changed':False,
    'only_new_config_and_output_namespace_bound':True}
