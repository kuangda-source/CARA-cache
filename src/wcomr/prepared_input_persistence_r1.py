"""Persist real prepare evidence before a later path can fail.

Only metadata is copied. Preparation, replay, RNG transition and the returned
batch remain the original implementation. Historical receipts are untouched.
"""
import copy
import json
import types


def bind_prepared_input_persistence(batch, *, state, save):
    if batch.__closure__ or 'PreparedInputReplay' not in batch.__globals__:
        raise ValueError('Closure-free ordinary batch with explicit replay binding required')
    if not isinstance(state, dict) or not callable(save):
        raise ValueError('Actual mutable receipt and its writer required')
    base = batch.__globals__['PreparedInputReplay']

    class PersistentPreparedInputReplay(base):
        def __init__(self, official):
            super().__init__(official)
            self._receipt_request = None

        def __call__(self, *args, **kwargs):
            requests = state.get('requests', [])
            if not requests or not requests[-1].get('paths'):
                raise ValueError('Actual active request and path required for prepare evidence')
            request = requests[-1]
            if request.get('status') != 'STARTED' or request['paths'][-1].get('status') != 'STARTED':
                raise ValueError('Prepare evidence requires a started actual path')
            if self._receipt_request is not None and self._receipt_request is not request:
                raise ValueError('One replay cannot write evidence into another request')
            result = super().__call__(*args, **kwargs)
            # Original replay has already checked actual input and RNG signatures.
            # These signatures contain scalars and containers, never prepared tensors.
            json.dumps(self.calls, allow_nan=False)
            self._receipt_request = request
            request['prepared_input_calls'] = copy.deepcopy(self.calls)
            save()
            return result

    derived = types.FunctionType(batch.__code__,
        {**batch.__globals__, 'PreparedInputReplay': PersistentPreparedInputReplay},
        batch.__name__, batch.__defaults__)
    derived.__kwdefaults__ = batch.__kwdefaults__
    if derived.__code__ is not batch.__code__:
        raise ValueError('Ordinary batch bytecode changed')
    return derived
