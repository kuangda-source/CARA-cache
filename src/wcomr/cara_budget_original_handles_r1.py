"""Read-only Linux identity witnesses for original search processes.

A missing PID is meaningful only in the original boot and PID namespace. These
witnesses grant no dispatch, billing, release or scientific acceptance.
"""
import hashlib
from pathlib import Path
import time
from uuid import UUID

from .gpu_budget_pool_v2 import process_identity

ROLES=('guardian','container_cli','supervisor','runner')


def host_view():
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if str(UUID(boot))!=boot:
        raise ValueError('Canonical Linux boot identity required')
    return dict(boot_id=boot,pid_namespace_inode=Path('/proc/self/ns/pid').stat().st_ino)


def bind_original_process(pid):
    if type(pid) is not int or pid<=0:
        raise ValueError('Positive original PID required')
    view=host_view();identity=process_identity(pid)
    if identity['state'] in (None,'Z','X') or type(identity['start_ticks']) is not int or identity['start_ticks']<=0:
        raise ValueError('Bind the live original process before work begins')
    return dict(pid=pid,start_ticks=identity['start_ticks'],host_view=view,
        original_command_sha256=hashlib.sha256(identity['command'].encode()).hexdigest())


def observe_original_process(handle):
    if (not isinstance(handle,dict) or type(handle.get('pid')) is not int or handle['pid']<=0
            or type(handle.get('start_ticks')) is not int or handle['start_ticks']<=0
            or not isinstance(handle.get('host_view'),dict)
            or set(handle['host_view'])!={'boot_id','pid_namespace_inode'}
            or type(handle['host_view']['pid_namespace_inode']) is not int
            or handle['host_view']['pid_namespace_inode']<=0):
        raise ValueError('Original boot/namespace/PID/start-tick binding required')
    if str(UUID(handle['host_view']['boot_id']))!=handle['host_view']['boot_id']:
        raise ValueError('Canonical original boot identity required')
    result=dict(observed_unix=time.time(),original_pid=handle['pid'],original_start_ticks=handle['start_ticks'],
        original_live=None,status='UNKNOWN',reason=None,dispatch_allowed=False,
        financial_settlement_allowed=False,scientific_read_allowed=False)
    try:
        view=host_view();result['observed_host_view']=view
        if view!=handle['host_view']:
            result['reason']='ORIGINAL_BOOT_OR_PID_NAMESPACE_UNAVAILABLE'
            return result
        current=process_identity(handle['pid'])
    except (OSError,ValueError,IndexError,UnicodeError) as error:
        result.update(reason='ORIGINAL_PROCESS_OBSERVATION_UNAVAILABLE',error_type=type(error).__name__)
        return result
    result['observed_process']={k:current[k] for k in ('pid','state','start_ticks')}
    if current['state'] is None and current['start_ticks'] is None:
        live,reason=False,'ORIGINAL_PROC_ABSENT'
    elif type(current['start_ticks']) is not int or current['start_ticks']<=0 or current['state'] is None:
        result['reason']='INCOMPLETE_PROC_IDENTITY'
        return result
    elif current['start_ticks']!=handle['start_ticks']:
        live,reason=False,'PID_REUSED_ORIGINAL_PROCESS_EXITED'
    elif current['state'] in ('Z','X'):
        live,reason=False,'ORIGINAL_PROCESS_ZOMBIE_OR_DEAD'
    else:
        live,reason=True,'ORIGINAL_PID_START_TICKS_LIVE'
    result.update(original_live=live,status='ORIGINAL_LIVE' if live else 'ORIGINAL_NOT_LIVE',reason=reason)
    return result


def observe_original_handles(handles):
    if set(handles)!=set(ROLES):
        raise ValueError('All four original process roles must be represented')
    known=[(v['pid'],v['start_ticks']) for v in handles.values() if v is not None]
    if len(set(known))!=len(known):
        raise ValueError('One original identity cannot replace multiple process roles')
    rows={role:(observe_original_process(handles[role]) if handles[role] is not None else
        dict(status='UNKNOWN',original_live=None,reason='ORIGINAL_HANDLE_NOT_RECORDED',
             dispatch_allowed=False,financial_settlement_allowed=False,scientific_read_allowed=False)) for role in ROLES}
    return dict(status='ORIGINAL_HANDLE_OBSERVATION_ONLY',handles=rows,
        all_original_handles_not_live=all(r['original_live'] is False for r in rows.values()),
        any_original_handle_live=any(r['original_live'] is True for r in rows.values()),
        unresolved_handles=[role for role,r in rows.items() if r['original_live'] is None],
        dispatch_allowed=False,financial_settlement_allowed=False,scientific_read_allowed=False,
        GPU_submissions=0,ledger_written=False)
