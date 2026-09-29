"""Avoid unrelated example-training checkpoint downloads in the pinned runtime.

The selected 2B post-trained experiment and its defaults remain registered by
Cosmos's official internal experiment package. Both F1 arms apply this adapter.
"""
import hashlib
import importlib
from pathlib import Path

CONFIG_SHA256 = '0ccb2fbdf4d997a680c50cfe3a52b22e85c285464884177ce7822b969ad2ddd9'
MODEL = '2B/post-trained'
EXPERIMENT = 'Stage-c_pt_4-Index-2-Size-2B-Res-720-Fps-16-Note-rf_with_edm_ckpt'


def core_only_importer(original):
    def filtered(package, *args, **kwargs):
        if package == 'cosmos_predict2.experiments':
            return None
        return original(package, *args, **kwargs)
    return filtered


def install_core_inference_registration(model, experiment):
    if (model, experiment) != (MODEL, EXPERIMENT):
        raise ValueError('Runtime registration adapter only validated for frozen 2B/post-trained profile')
    module = importlib.import_module('cosmos_predict2._src.predict2.configs.video2world.config')
    if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != CONFIG_SHA256:
        raise RuntimeError('Config source changed; audit registration before adapting it')
    if not getattr(module, '_wcomr_registration_installed', False):
        module.import_all_modules_from_package = core_only_importer(module.import_all_modules_from_package)
        module._wcomr_registration_installed = True
    return {'config_sha256': CONFIG_SHA256, 'excluded_package': 'cosmos_predict2.experiments',
            'selected_experiment': experiment, 'scope': 'exclude unrelated example training registration only'}
