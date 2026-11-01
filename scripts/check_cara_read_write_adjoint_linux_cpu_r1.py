"""Reuse the exact GPU-hidden import/resource boundary for the adjoint suite."""
from check_cara_read_write_transition_linux_cpu_r1 import main


if __name__ == '__main__':
    main(suite='adjoint')
