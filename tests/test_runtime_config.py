import pytest
from wcomr.runtime_config import core_only_importer, install_core_inference_registration


def test_only_unrelated_example_root_is_excluded():
    calls = []
    def original(package, **kwargs):
        calls.append((package, kwargs))
        return 'registered'
    wrapped = core_only_importer(original)
    assert wrapped('cosmos_predict2.experiments', reload=True) is None
    for package in ('cosmos_predict2._src.predict2.configs.video2world.experiment',
                    'cosmos_predict2.experiments.internal', 'unrelated'):
        assert wrapped(package, reload=True) == 'registered'
    assert len(calls) == 3
    assert all(kwargs == {'reload': True} for _, kwargs in calls)


def test_adapter_refuses_unreviewed_models_before_importing_runtime():
    with pytest.raises(ValueError, match='only validated'):
        install_core_inference_registration('14B/post-trained', 'any')
