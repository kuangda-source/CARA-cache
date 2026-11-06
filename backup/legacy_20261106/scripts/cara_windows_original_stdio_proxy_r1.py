"""Task-only byte relay through the original authenticated Windows SSH session.

Use Windows' existing PowerShell/.NET TCP client instead of its intermittent
direct-tcpip channel. The outer and inner OpenSSH clients still verify their
original host keys and credentials. No remote files, routes, services or software
are changed. Only the two original registered SSH destinations are permitted.
"""
import base64
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    target,port=sys.argv[1],int(sys.argv[2])
    if (target,port) not in {('10.128.160.181',22),('10.156.160.3',22617)}:
        raise ValueError('Only the original two registered SSH endpoints are permitted')
    script = ("$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';"
        "$peer=New-Object System.Net.Sockets.TcpClient;"
        f"$peer.Connect('{target}',{port});"
        "try{$stream=$peer.GetStream();"
        "$inputBytes=[Console]::OpenStandardInput();$outputBytes=[Console]::OpenStandardOutput();"
        "$download=$stream.CopyToAsync($outputBytes);$upload=$inputBytes.CopyToAsync($stream);"
        "[void][System.Threading.Tasks.Task]::WaitAny([System.Threading.Tasks.Task[]]@($upload,$download));"
        "$outputBytes.Flush()}finally{$peer.Dispose()}")
    encoded=base64.b64encode(script.encode('utf-16le')).decode()
    arguments=['ssh','-T','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'),
        '-o','BatchMode=yes','-o','ConnectTimeout=30','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',
        'office_tailscale','powershell -NoProfile -NonInteractive -EncodedCommand '+encoded]
    os.execvp(arguments[0],arguments)


if __name__=='__main__':
    main()
