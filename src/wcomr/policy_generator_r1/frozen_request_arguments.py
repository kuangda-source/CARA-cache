"""Revalidate request variants without mutating frozen Cosmos arguments."""
import copy


def request_variant(sample, *, seed, num_steps):
    if type(seed) is not int or type(num_steps) is not int or num_steps <= 0:
        raise ValueError('Integer seed and positive integer step count required')
    cls = type(sample)
    if not callable(getattr(sample, 'model_dump', None)) or not callable(getattr(cls, 'model_validate', None)):
        raise TypeError('Validated immutable request model required; mutable fixtures are not production evidence')
    if getattr(cls, 'model_config', {}).get('frozen') is not True:
        raise TypeError('Frozen request contract required')
    original = sample.model_dump(mode='python', round_trip=True)
    expected = copy.deepcopy(original)
    expected.update(seed=seed, num_steps=num_steps)
    # model_copy(update=...) bypasses validation. Reconstruct using the real
    # class so validators, field constraints and frozen semantics remain active.
    result = cls.model_validate(copy.deepcopy(expected))
    if type(result) is not cls or result is sample:
        raise ValueError('Independent original request class required')
    if result.model_dump(mode='python', round_trip=True) != expected:
        raise ValueError('Request reconstruction changed fields outside the registered override')
    if sample.model_dump(mode='python', round_trip=True) != original:
        raise ValueError('Original request mutated')
    return result
