"""Accept only the new R2 original CPU; the failed R1 remains immutable."""
from accept_cara_source_lifecycle_linux_cpu_r1 import accept as original_accept, main
from cara_source_lifecycle_linux_cpu_r2 import OVERLAY,STAGE


def accept(launch,capture):
    return original_accept(launch,capture,stage=STAGE,overlay_names=OVERLAY)


if __name__=='__main__':main(acceptor=accept)
