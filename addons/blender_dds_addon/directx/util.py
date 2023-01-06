"""Utils for I/O."""

import os
import platform


def mkdir(directory):
    """Make dirctory."""
    os.makedirs(directory, exist_ok=True)


def get_ext(file):
    """Get file extension."""
    return file.split('.')[-1]


def check(actual, expected, f=None, msg='Parse failed. This is unexpected error.'):
    """Check if actual and expected is the same."""
    if actual != expected:
        if f is not None:
            print(f'offset: {f.tell()}')
        print(f'actual: {actual}')
        print(f'expected: {expected}')
        raise RuntimeError(msg)


def read_uint32(f):
    """Read 4-byte as uint."""
    binary = f.read(4)
    return int.from_bytes(binary, "little")


def read_const_uint32(f, n, msg='Unexpected Value!'):
    """Read uint32 and check if it's the same as specified value."""
    const = read_uint32(f)
    check(const, n, f, msg)


def write_uint32(f, n):
    """Write int as uint32."""
    binary = n.to_bytes(4, byteorder="little")
    f.write(binary)


def get_os_name():
    return platform.system()


def is_windows():
    return get_os_name() == 'Windows'


def is_linux():
    return get_os_name() == 'Linux'


def is_mac():
    return get_os_name() == 'Darwin'
