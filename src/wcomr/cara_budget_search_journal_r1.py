"""Durable local query records for the bounded search controller.

This supplies no GPU admission or physical-run terminal verification. A returned
callback value is recorded as RETURNED, not as an accepted experiment. Missing
returns require an original-handle reader; this module never retries them.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform

from . import cara_budget_search_r1 as controller
from . import cara_fast_spec_r1 as specification
from .policy_generator_r1 import interval_grammar
from .cara_fast_spec_r1 import digest


class OriginalQueryUnknown(RuntimeError):
    pass


class NewQueryNotAdmitted(RuntimeError):
    pass


class RecordedCallbackError(RuntimeError):
    pass


def create_record(path, value):
    """Exclusive write; a torn record remains visible and refuses recovery."""
    raw = json.dumps(value, sort_keys=True, allow_nan=False).encode() + b'\n'
    with path.open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    sync_directory(path.parent)


def sync_directory(path):
    directory = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def read_record(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Original regular query record required: '+path.name)
    return json.loads(path.read_bytes())


class QueryJournal:
    """One lock for the entire controller, one intent before each callback."""
    def __init__(self, directory, binding, *, create=False, allow_new_queries=False):
        self.root = Path(directory)
        self.binding = copy.deepcopy(binding)
        self.create = create
        self.allow_new = allow_new_queries
        self.lock = None
        self.visited = 0
        self.new_callbacks = self.reused_returns = 0
        self.stopped_reason = None
        self.original_error = None

    def __enter__(self):
        if self.create:
            self.root.mkdir(mode=0o700)
            sync_directory(self.root.parent)
            create_record(self.root/'binding.json', self.binding)
            create_record(self.root/'controller.lock', {})
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError('Original query directory required')
        read_record(self.root/'controller.lock')
        self.lock = open(self.root/'controller.lock', 'r+b')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if read_record(self.root/'binding.json') != self.binding:
                raise ValueError('Search source/config/context changed; recover the original binding')
            intents = sorted(self.root.glob('query-*.intent.json'))
            returns = sorted(self.root.glob('query-*.return.json'))
            if len(intents) > self.binding['config']['max_evaluations']:
                raise ValueError('Original intent count exceeds its registered query cap')
            for i, path in enumerate(intents, 1):
                if path.name != self.path(i, 'intent').name:
                    raise ValueError('Query journal has a sequence gap')
                request = read_record(path)
                if (request['query_id'] != i or request['context_sha256'] != self.binding['context_sha256']
                        or digest({k:v for k,v in request.items() if k != 'request_sha256'}) != request['request_sha256']):
                    raise ValueError('Original query identity changed')
                returned = self.path(i, 'return')
                if returned.exists():
                    payload = self.read_return(request)
                    if payload['kind'] == 'CALLBACK_ERROR' and i != len(intents):
                        raise ValueError('A later query exists after a recorded callback error')
                elif i != len(intents):
                    raise ValueError('A later query exists after an unresolved original intent')
            if any(not self.path(int(p.name.split('.')[0].split('-')[1]), 'intent').exists() for p in returns):
                raise ValueError('Query return without its original intent')
            self.persisted_intents = len(intents)
            return self
        except BaseException:
            self.lock.close()
            self.lock = None
            raise

    def __exit__(self, *unused):
        self.lock.close()
        self.lock = None

    def path(self, query_id, kind):
        return self.root/f'query-{query_id:06d}.{kind}.json'

    def read_return(self, request):
        record = read_record(self.path(request['query_id'], 'return'))
        payload = record['payload']
        if (record['request_sha256'] != request['request_sha256'] or digest(payload) != record['payload_sha256']
                or payload['kind'] not in ('RETURNED', 'CALLBACK_ERROR')):
            raise ValueError('Original callback return changed')
        return payload

    def persist_return(self, request, payload):
        try:
            create_record(self.path(request['query_id'], 'return'), dict(
                request_sha256=request['request_sha256'], payload=payload, payload_sha256=digest(payload)))
        except OSError:
            self.stopped_reason = 'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH'
            raise

    def evaluate(self, request, callback):
        if self.lock is None:
            raise RuntimeError('Query controller lock is not held')
        if request['query_id'] != self.visited+1 or request['query_id'] > self.binding['config']['max_evaluations']:
            raise ValueError('Sequential query within the original cap required')
        if (request['context_sha256'] != self.binding['context_sha256']
                or digest({k:v for k,v in request.items() if k != 'request_sha256'}) != request['request_sha256']):
            raise ValueError('Query does not match the bound context')
        self.visited += 1
        intent = self.path(request['query_id'], 'intent')
        if intent.exists():
            if read_record(intent) != request:
                raise ValueError('Deterministic replay differs from original query')
            if not self.path(request['query_id'], 'return').exists():
                self.stopped_reason = 'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH'
                raise OriginalQueryUnknown('Recover original query '+str(request['query_id'])+'; never repeat its callback')
            payload = self.read_return(request)
            if payload['kind'] == 'CALLBACK_ERROR':
                self.original_error = payload['error']
                raise RecordedCallbackError(json.dumps(self.original_error, sort_keys=True))
            self.reused_returns += 1
            return copy.deepcopy(payload['response'])
        if request['query_id'] != self.persisted_intents+1:
            raise ValueError('Original intent sequence differs')
        if not self.allow_new:
            self.stopped_reason = 'NEW_QUERY_NOT_ADMITTED'
            raise NewQueryNotAdmitted('Recovery only; no new query admitted')
        create_record(intent, request)
        self.persisted_intents += 1
        self.new_callbacks += 1
        try:
            response = callback(copy.deepcopy(request))
            payload = dict(kind='RETURNED', response=response)
            digest(payload)  # Invalid/nonfinite JSON becomes a recorded callback error.
        except Exception as error:
            self.original_error = dict(type=type(error).__name__, message=str(error))
            payload = dict(kind='CALLBACK_ERROR', error=self.original_error)
            self.persist_return(request, payload)
            raise
        # A write/fsync failure leaves an unresolved original intent. Do not try a
        # second write or reinterpret the missing durable return as permission.
        self.persist_return(request, payload)
        return response


def run_search(directory, schedule, profile, config, *, fit_members, context_sha256,
               evaluate, create=False, allow_new_queries=False):
    binding = dict(schema='CARA_BUDGET_SEARCH_QUERY_JOURNAL_R1', context_sha256=context_sha256,
        schedule_sha256=digest(schedule), profile_fingerprint=profile.fingerprint,
        FIT_members=list(fit_members), config=dict(vars(config)), python_version=platform.python_version(),
        source_sha256={name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in (
            ('controller', controller.__file__), ('journal', __file__),
            ('specification', specification.__file__), ('grammar', interval_grammar.__file__))})
    with QueryJournal(directory, binding, create=create, allow_new_queries=allow_new_queries) as journal:
        result = controller.search(schedule, profile, config, fit_members=fit_members,
            context_sha256=context_sha256, evaluate=lambda request: journal.evaluate(request, evaluate))
        if journal.stopped_reason:
            result['termination'] = journal.stopped_reason
            result['configured_search_finished'] = False
            result['queries'][-1]['status'] = ('UNKNOWN' if journal.stopped_reason ==
                'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH' else 'NOT_ADMITTED')
        if journal.visited < journal.persisted_intents:
            raise ValueError('Original journal contains queries beyond the replayed controller stop')
        result['journal'] = dict(binding_sha256=digest(binding),
            persisted_intents=journal.persisted_intents, new_callback_calls=journal.new_callbacks,
            reused_callback_returns=journal.reused_returns, original_callback_error=journal.original_error,
            physical_terminal_verified=False, production_GPU_admission_verified=False,
            unresolved_original_reader_implemented=False)
        return result
