"""Texture converter.

Notes:
    You need to build dll from https://github.com/matyalatte/Texconv-Custom-DLL.
    And put the dll in the same directory as texconv.py.
"""
import ctypes
import os
import tempfile

from .dds import DDSHeader, is_hdr
from .dxgi_format import DXGI_FORMAT
from . import util

DLL = None


def get_dll_close():
    """Get dll function to unload DLL."""
    try:
        if util.is_windows():
            return ctypes.windll.kernel32.FreeLibrary
        elif util.is_mac():
            try:
                # macOS 11 or later
                stdlib = ctypes.CDLL("libc.dylib")
            except OSError:
                stdlib = ctypes.CDLL("libSystem")
        elif util.is_linux():
            try:
                stdlib = ctypes.CDLL("")
            except OSError:
                # Alpine Linux
                stdlib = ctypes.CDLL("libc.so")
            return stdlib.dlclose

    except OSError:
        # Failed to get the lib.
        return None


def unload_texconv():
    global DLL
    if DLL is None:
        return

    dll_close = get_dll_close()
    if dll_close is None:
        raise RuntimeError("Failed to unload DLL. Restart Blender if you will remove the addon.")

    handle = DLL._handle
    dll_close.argtypes = [ctypes.c_void_p]
    dll_close(handle)
    DLL = None


class Texconv:
    """Texture converter."""
    def __init__(self, dll_path=None):
        self.load_dll(dll_path=dll_path)

    def load_dll(self, dll_path=None):
        global DLL
        if DLL is not None:
            self.dll = DLL
            return

        if dll_path is None:
            file_path = os.path.realpath(__file__)
            if util.is_windows():
                dll_name = "texconv.dll"
            elif util.is_mac():
                dll_name = "libtexconv.dylib"
            elif util.is_linux():
                dll_name = "libtexconv.so"
            else:
                raise RuntimeError(f'This OS ({util.get_os_name()}) is unsupported.')
            dirname = os.path.dirname(file_path)
            dll_path = os.path.join(dirname, dll_name)
            dll_path2 = os.path.join(os.path.dirname(dirname), dll_name)  # allow ../texconv.dll

        if not os.path.exists(dll_path):
            if os.path.exists(dll_path2):
                dll_path = dll_path2
            else:
                raise RuntimeError(f'texconv not found. ({dll_path})')

        self.dll = ctypes.cdll.LoadLibrary(dll_path)
        DLL = self.dll

    def unload_dll(self):
        unload_texconv()
        self.dll = None

    def convert_to_tga(self, file, out=None, cubemap_layout="h-cross", invert_normals=False, verbose=True):
        """Convert dds to tga."""
        if self.dll is None:
            raise RuntimeError("texconv is unloaded.")

        dds_header = DDSHeader.read_from_file(file)

        if dds_header.is_3d():
            raise RuntimeError('Can not convert 3D textures with texconv.')

        if verbose:
            print(f'DXGI_FORMAT: {dds_header.get_format_as_str()}')

        args = []

        if dds_header.is_hdr():
            fmt = 'hdr'
            if not dds_header.convertible_to_hdr():
                args += ['-f', 'fp32']
        else:
            fmt = 'tga'
            if not dds_header.convertible_to_tga():
                args += ['-f', 'rgba']

        if dds_header.is_int():
            msg = f'Int format detected. ({dds_header.get_format_as_str()})\n It might not be converted correctly.'
            print(msg)

        if not dds_header.is_cube():
            args += ['-ft', fmt]

            if dds_header.is_bc5():
                args += ['-reconstructz']
                if invert_normals:
                    args += ['-inverty']

            out = self.__texconv(file, args, out=out, verbose=verbose)

        name = os.path.join(out, os.path.basename(file))
        name = ".".join(name.split(".")[:-1] + [fmt])

        if dds_header.is_cube():
            self.__cube_to_image(file, name, args, cubemap_layout=cubemap_layout, verbose=verbose)

        return name

    def convert_to_dds(self, file, dds_fmt, out=None,
                       invert_normals=False, no_mip=False,
                       export_as_cubemap=False,
                       cubemap_layout="h-cross",
                       verbose=True, allow_slow_codec=False):
        """Convert texture to dds."""
        if self.dll is None:
            raise RuntimeError("texconv is unloaded.")

        ext = util.get_ext(file)

        if is_hdr(dds_fmt) and ext != 'hdr':
            raise RuntimeError(f'Use .hdr for HDR textures. ({file})')
        if ('BC6' in dds_fmt or 'BC7' in dds_fmt) and (not util.is_windows()) and (not allow_slow_codec):
            raise RuntimeError(f'Can NOT use CPU codec for {dds_fmt}. Or enable the "Allow Slow Codec" option.')

        if not DXGI_FORMAT.is_valid_format("DXGI_FORMAT_" + dds_fmt):
            raise RuntimeError(f'Not DXGI format. ({dds_fmt})')

        if verbose:
            print(f'DXGI_FORMAT: {dds_fmt}')

        base_name = os.path.basename(file)
        base_name = '.'.join(base_name.split('.')[:-1] + ['dds'])

        args = ['-f', dds_fmt]
        if no_mip:
            args += ['-m', '1']

        if ("BC5" in dds_fmt) and invert_normals:
            args += ['-inverty']

        if export_as_cubemap:
            if ext == "hdr":
                temp_args = ['-f', 'fp32']
            else:
                temp_args = ['-f', 'rgba']
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dds = os.path.join(temp_dir, base_name)
                self.__image_to_cube(file, temp_dds, temp_args, cubemap_layout=cubemap_layout, verbose=verbose)
                out = self.__texconv(temp_dds, args, out=out, verbose=verbose, allow_slow_codec=allow_slow_codec)
        else:
            out = self.__texconv(file, args, out=out, verbose=verbose, allow_slow_codec=allow_slow_codec)
        name = os.path.join(out, base_name)
        return name

    def __texconv(self, file, args, out=None, verbose=True, allow_slow_codec=False):
        """Run texconv."""
        if out is not None and isinstance(out, str):
            args += ['-o', out]
        else:
            out = '.'

        if out not in ['.', ''] and not os.path.exists(out):
            util.mkdir(out)

        args += ["-y"]
        args += [os.path.normpath(file)]

        args_p = [ctypes.c_wchar_p(arg) for arg in args]
        args_p = (ctypes.c_wchar_p*len(args_p))(*args_p)
        err_buf = ctypes.create_unicode_buffer(512)
        result = self.dll.texconv(len(args), args_p, verbose, False, allow_slow_codec, err_buf, 512)
        if result != 0:
            raise RuntimeError(err_buf.value)

        return out

    def __cube_to_image(self, file, new_file, args, cubemap_layout="h-cross", verbose=True):
        """Genarate an image from a cubemap with texassemble."""
        if cubemap_layout.endswith("-fnz"):
            cubemap_layout = cubemap_layout[:-4]
        args = [cubemap_layout] + args
        self.__texassemble(file, new_file, args, verbose=verbose)

    def __image_to_cube(self, file, new_file, args, cubemap_layout="h-cross", verbose=True):
        """Generate a cubemap from an image with texassemble."""
        cmd = "cube-from-" + cubemap_layout[0] + cubemap_layout[2]
        args = [cmd] + args
        self.__texassemble(file, new_file, args, verbose=verbose)

    def __texassemble(self, file, new_file, args, verbose=True):
        """Run texassemble."""
        out = os.path.dirname(new_file)
        if out not in ['.', ''] and not os.path.exists(out):
            util.mkdir(out)
        args += ["-y", "-o", new_file, file]

        args_p = [ctypes.c_wchar_p(arg) for arg in args]
        args_p = (ctypes.c_wchar_p*len(args_p))(*args_p)
        err_buf = ctypes.create_unicode_buffer(512)
        result = self.dll.texassemble(len(args), args_p, verbose, False, err_buf, 512)
        if result != 0:
            raise RuntimeError(err_buf.value)
