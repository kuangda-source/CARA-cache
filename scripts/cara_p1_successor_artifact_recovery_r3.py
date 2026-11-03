"""Correct the released-artifact reader's host inspection boundary only.

The failed R2 reader stays ended. This distinct validation uses the exact same
scientific worker, original data and sealed metrics. Docker is used by the
original Host.reader only to inspect its old score containers; no scorer runs.
"""
import cara_p1_successor_acceptance_transport_r2 as original

original.CPU_NAME = 'cara-P1-successor-artifact-host-inspect-CPU-r3-20261103'

source = original.REMOTE
anchor = "command.extend(['--entrypoint',python,reg['container_image'],str(cpu/'worker.py'),str(cpu)])"
replacement = """docker_cli=pathlib.Path('/usr/bin/docker');docker_socket=pathlib.Path('/var/run/docker.sock')
 assert docker_cli.is_file() and docker_socket.is_socket()
 original_output=root/'outputs'/binding['run_id']
 command.extend(['-v',str(docker_cli)+':'+str(docker_cli)+':ro',
                 '-v',str(docker_socket)+':'+str(docker_socket)+':ro',
                 '-v',str(original_output)+':'+str(original_output)+':rw'])
 command.extend(['--entrypoint',python,reg['container_image'],str(cpu/'worker.py'),str(cpu)])"""
assert source.count(anchor) == 1
source = source.replace(anchor, replacement)
anchor = "worker_sha256=p['worker_sha256'],capture_sha256="
assert source.count(anchor) == 1
source = source.replace(anchor, "worker_sha256=p['worker_sha256'],docker_inspect_cli_sha256=sha(docker_cli),host_inspection_only=True,capture_sha256=")
anchor = "assert existing['Image']==reg['container_image'] and existing['Config']['Labels']['wcomr.original-launch']==binding['launch_id']"
replacement = anchor + """
  assert sha('/usr/bin/docker')==plan['docker_inspect_cli_sha256'] and plan['host_inspection_only'] is True
  mounts=[(m['Source'],m['Destination'],m['RW']) for m in existing['Mounts'] if m['Type']=='bind']
  expected=[(str(root),str(root),False),(str(cpu),str(cpu),True),
            ('/usr/bin/docker','/usr/bin/docker',False),('/var/run/docker.sock','/var/run/docker.sock',False),
            (str(root/'outputs'/binding['run_id']),str(root/'outputs'/binding['run_id']),True)]
  assert sorted(mounts)==sorted(expected)
"""
assert source.count(anchor) == 1
original.REMOTE = source.replace(anchor, replacement)
original.__file__ = __file__

if __name__ == '__main__':
    original.main()
