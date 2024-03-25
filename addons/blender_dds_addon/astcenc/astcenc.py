"""Texture converter for ASTC formats.

Notes:
    You need to build dll from https://github.com/ARM-software/astc-encoder.
    And put the dll in the same directory as astcenc.py.
"""

import ctypes
import math
import multiprocessing
import os
from ..directx import util
from .structures import (ASTCENC_ERROR, ASTCENC_PRF,
                         ASTCENC_QUALITY, ASTCENC_FLG,
                         AstcencConfig, get_bgra_swizzle,
                         ASTCENC_TYPE, PointerToPointer,
                         AstcencImage)

DLL = None


def unload_astcenc():
    global DLL
    if DLL is None:
        return

    dll_close = util.get_dll_close()
    if dll_close is None:
        raise RuntimeError("Failed to unload DLL.")

    handle = DLL._handle
    dll_close.argtypes = [ctypes.c_void_p]
    dll_close(handle)
    DLL = None


class Astcenc:
    """ASTC Encoder."""

    def __init__(self, dll_path=None, thread_count=-1):
        self.load_dll(dll_path=dll_path)
        self.config = AstcencConfig()
        if (thread_count == -1):
            self.thread_count = multiprocessing.cpu_count()
        else:
            self.thread_count = thread_count

    def load_dll(self, dll_path=None):
        global DLL
        if DLL is not None:
            self.dll = DLL
            return

        if dll_path is None:
            dirname = os.path.dirname(os.path.realpath(__file__))
            dll_path = util.find_local_library(dirname, "astcenc")

        if (dll_path is None) or (not os.path.exists(dll_path)):
            raise RuntimeError('astcenc not found.')

        self.dll = ctypes.cdll.LoadLibrary(dll_path)
        DLL = self.dll

    def unload_dll(self):
        unload_astcenc()
        self.dll = None

    def config_init(self, block_x, block_y, block_z=1,
                    profile=ASTCENC_PRF.LDR,
                    quality=ASTCENC_QUALITY.MEDIUM,
                    flags=ASTCENC_FLG.NONE):
        self.config.block_x = block_x
        self.config.block_y = block_y
        self.config.profile = profile
        error = self.dll.astcenc_config_init(
            profile,
            ctypes.c_uint(block_x),
            ctypes.c_uint(block_y),
            ctypes.c_uint(block_z),
            ctypes.c_float(quality),
            ctypes.c_uint(flags),
            ctypes.byref(self.config)
        )
        if (error):
            raise RuntimeError(f"Failed to initialize AstcencConfig ({self.get_error_string(error)})")

    def context_alloc(self):
        self.pcontext = ctypes.c_void_p()
        error = self.dll.astcenc_context_alloc(
            ctypes.byref(self.config),
            ctypes.c_uint(self.thread_count),
            ctypes.byref(self.pcontext)
        )
        if (error):
            raise RuntimeError(f"Failed to allocate AstcencContext ({self.get_error_string(error)})")

    def context_free(self):
        self.dll.astcenc_context_free(self.pcontext)

    def get_error_string(self, error):
        if (error not in [err.value for err in ASTCENC_ERROR]):
            return "UNDEFINED"
        return ASTCENC_ERROR(error).name

    def compress_image(self, size_x, size_y, data, size_z=1):
        self.context_alloc()

        image = AstcencImage()
        image.dim_x = size_x
        image.dim_y = size_y
        image.dim_z = size_z
        image.data_type = ASTCENC_TYPE.U8
        data_buf = ctypes.create_string_buffer(data, len(data))
        data_pbuf = (ctypes.c_void_p*1)(*[ctypes.cast(data_buf, ctypes.c_void_p)])
        image.data = ctypes.cast(data_pbuf, PointerToPointer)

        data_len = self.calc_compressed_buffer_size(size_x, size_y, size_z)
        data_out = ctypes.create_string_buffer(data_len)

        swizzle = get_bgra_swizzle()

        for thread_index in range(self.thread_count):
            error = self.dll.astcenc_compress_image(
                self.pcontext,
                ctypes.byref(image),
                ctypes.byref(swizzle),
                data_out,
                data_len,
                thread_index
            )
            if (error):
                raise RuntimeError(f"Failed to compress an image as ASTC ({self.get_error_string(error)})")

        error = self.dll.astcenc_compress_reset(self.pcontext)
        if (error):
            raise RuntimeError(f"Failed to reset AstcencContext ({self.get_error_string(error)})")

        compressed = bytes(data_out)
        self.context_free()
        return compressed

    def calc_compressed_buffer_size(self, size_x, size_y, size_z=1):
        block_count_x = math.ceil(size_x / self.config.block_x)
        block_count_y = math.ceil(size_y / self.config.block_y)
        block_count_z = math.ceil(size_z / self.config.block_z)
        block_count = block_count_x * block_count_y * block_count_z
        return block_count * 16

    def decompress_image(self, size_x, size_y, data, size_z=1):
        self.context_alloc()

        image = AstcencImage()
        image.dim_x = size_x
        image.dim_y = size_y
        image.dim_z = size_z
        image.data_type = ASTCENC_TYPE.U8
        size = size_x * size_y * size_z * 4
        buffer = ctypes.create_string_buffer(size)
        pbuffer = (ctypes.c_void_p*1)(*[ctypes.cast(buffer, ctypes.c_void_p)])
        image.data = ctypes.cast(pbuffer, PointerToPointer)

        data_len = len(data)
        data_in = ctypes.create_string_buffer(data, data_len)

        swizzle = get_bgra_swizzle()

        for thread_index in range(self.thread_count):
            error = self.dll.astcenc_decompress_image(
                self.pcontext,
                data_in,
                data_len,
                ctypes.byref(image),
                ctypes.byref(swizzle),
                thread_index
            )
            if (error):
                raise RuntimeError(f"Failed to decompress an ASTC image ({self.get_error_string(error)})")

        error = self.dll.astcenc_decompress_reset(self.pcontext)
        if (error):
            raise RuntimeError(f"Failed to reset AstcencContext ({self.get_error_string(error)})")

        decompressed = bytes(buffer)
        self.context_free()
        return decompressed
