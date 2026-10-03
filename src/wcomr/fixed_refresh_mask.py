"""Immutable exposed-trace masks for offline diagnostics, never online routing."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FixedRefreshMask:
    sample_name: str
    model_id: str
    condition_id: str
    dense_calls: tuple
    source_receipt_sha256: str
    horizon: int = 70
    warm_calls: int = 14

    def __post_init__(self):
        if any(type(v) is not str or not v for v in
               (self.sample_name, self.model_id, self.condition_id)):
            raise ValueError('Explicit fixed-mask sample/model/condition identity required')
        if (type(self.dense_calls) is not tuple or len(self.dense_calls) != 72
                or any(type(v) is not bool for v in self.dense_calls)):
            raise ValueError('Fixed mask must declare exactly72 Boolean CFG decisions')
        if self.horizon != 70 or self.warm_calls != 14:
            raise ValueError('Fixed mask only supports frozen70 horizon and14 warm calls')
        if not all(self.dense_calls[:14] + self.dense_calls[70:]):
            raise ValueError('Fixed mask cannot skip warm start or dense solver tail')
        if (type(self.source_receipt_sha256) is not str
                or len(self.source_receipt_sha256) != 64
                or any(v not in '0123456789abcdef' for v in self.source_receipt_sha256)):
            raise ValueError('Fixed mask must bind its immutable source receipt SHA')

    def bind(self, context):
        if (type(context) is not tuple or len(context) != 3
                or context[1:] != (self.model_id, self.condition_id)
                or not context[0].endswith(':' + self.sample_name)):
            raise ValueError('Fixed mask sample/model/condition binding differs')

    def skip(self, call, branch):
        if type(call) is not int or not 1 <= call <= 72 or branch != (call - 1) % 2:
            raise ValueError('Fixed mask absolute CFG call or branch differs')
        return not self.dense_calls[call - 1]

    def to_dict(self):
        return {'sample_name': self.sample_name, 'model_id': self.model_id,
                'condition_id': self.condition_id, 'dense_calls': list(self.dense_calls),
                'source_receipt_sha256': self.source_receipt_sha256,
                'horizon': self.horizon, 'warm_calls': self.warm_calls,
                'role': 'OFFLINE_FIXED_EXPOSED_TRACE_DIAGNOSTIC_NOT_DEPLOYMENT_ROUTING'}
