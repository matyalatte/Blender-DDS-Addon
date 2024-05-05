"""Utils for I/O."""

import ctypes
from ctypes.util import find_library
import os
import platform


def mkdir(directory):
    """Make directory."""
    os.makedirs(directory, exist_ok=True)


def get_ext(file):
    """Get file extension."""
    return file.split('.')[-1].lower()


def get_size(f):
    pos = f.tell()
    f.seek(0, 2)
    size = f.tell()
    f.seek(pos)
    return size


def get_os_name():
    return platform.system()


def is_windows():
    return get_os_name() == 'Windows'


def is_linux():
    return get_os_name() == 'Linux'


def is_mac():
    return get_os_name() == 'Darwin'


def is_arm():
    return 'arm' in platform.machine().lower()


def get_dll_close_from_lib(lib_name):
    """Return dll function to unlaod DLL if the library has it."""
    dlpath = find_library(lib_name)
    if dlpath is None:
        # DLL not found.
        return None
    try:
        lib = ctypes.CDLL(dlpath)
        if hasattr(lib, "dlclose"):
            return lib.dlclose
    except OSError:
        pass
    # dlclose not found.
    return None


def get_dll_close():
    """Get dll function to unload DLL."""
    if is_windows():
        return ctypes.windll.kernel32.FreeLibrary
    else:
        # Search libc, libdl, and libSystem
        for lib_name in {"c", "dl", "System"}:
            dlclose = get_dll_close_from_lib(lib_name)
            if dlclose is not None:
                return dlclose
    # Failed to find dlclose
    return None


def find_local_library(dir, lib_name):
    for f in os.listdir(dir):
        name, ext = os.path.splitext(f)
        if ext not in {".dll", ".dylib", ".so"}:
            continue
        if name.startswith(lib_name) or name.startswith("lib" + lib_name):
            return os.path.join(dir, f)
    return None
