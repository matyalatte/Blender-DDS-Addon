import ctypes
from enum import IntEnum


class ASTCENC_ERROR(IntEnum):
    """Enum for error codes in Astcenc."""
    SUCCESS = 0
    ERR_OUT_OF_MEM = 1
    ERR_BAD_CPU_FLOAT = 2
    ERR_BAD_PARAM = 3
    ERR_BAD_BLOCK_SIZE = 4
    ERR_BAD_PROFILE = 5
    ERR_BAD_QUALITY = 6
    ERR_BAD_SWIZZLE = 7
    ERR_BAD_FLAGS = 8
    ERR_BAD_CONTEXT = 9
    ERR_NOT_IMPLEMENTED = 10
    ERR_BAD_DECODE_MODE = 11


class ASTCENC_PRF(IntEnum):
    """Enum for profile in AstcencConfig."""
    LDR_SRGB = 0
    LDR = 1
    HDR_RGB_LDR_A = 2
    HDR = 3


class ASTCENC_QUALITY:
    """Encoding quality for Astcenc."""
    FASTEST = 0.0
    FAST = 10.0
    MEDIUM = 60.0
    THOROUGH = 98.0
    VERYTHOROUGH = 99.0
    EXHAUSTIVE = 100.0


class ASTCENC_FLG(IntEnum):
    """Flags for AstcencConfig."""
    NONE = 0
    MAP_NORMAL = 1 << 0
    USE_DECODE_UNORM8 = 1 << 1
    USE_ALPHA_WEIGHT = 1 << 2
    USE_PERCEPTUAL = 1 << 3
    DECOMPRESS_ONLY = 1 << 4
    SELF_DECOMPRESS_ONLY = 1 << 5
    MAP_RGBM = 1 << 6
    ALL_FLAGS = 1 << 7 - 1


class AstcencConfig(ctypes.Structure):
    _fields_ = [
        ('profile', ctypes.c_int),
        ('flags', ctypes.c_uint),
        ('block_x', ctypes.c_uint),
        ('block_y', ctypes.c_uint),
        ('block_z', ctypes.c_uint),
        ('cw_r_weight', ctypes.c_float),
        ('cw_g_weight', ctypes.c_float),
        ('cw_b_weight', ctypes.c_float),
        ('cw_a_weight', ctypes.c_float),
        ('a_scale_radius', ctypes.c_uint),
        ('rgbm_m_scale', ctypes.c_float),
        ('tune_partition_count_limit', ctypes.c_uint),
        ('tune_2partition_index_limit', ctypes.c_uint),
        ('tune_3partition_index_limit', ctypes.c_uint),
        ('tune_4partition_index_limit', ctypes.c_uint),
        ('tune_block_mode_limit', ctypes.c_uint),
        ('tune_refinement_limit', ctypes.c_uint),
        ('tune_candidate_limit', ctypes.c_uint),
        ('tune_2partitioning_candidate_limit', ctypes.c_uint),
        ('tune_3partitioning_candidate_limit', ctypes.c_uint),
        ('tune_4partitioning_candidate_limit', ctypes.c_uint),
        ('tune_db_limit', ctypes.c_float),
        ('tune_mse_overshoot', ctypes.c_float),
        ('tune_2partition_early_out_limit_factor', ctypes.c_float),
        ('tune_3partition_early_out_limit_factor', ctypes.c_float),
        ('tune_2plane_early_out_limit_correlation', ctypes.c_float),
        ('tune_search_mode0_enable', ctypes.c_float),
        ('progress_callback', ctypes.c_void_p),
    ]


class ASTCENC_SWZ(IntEnum):
    """Enum for members of AstcencSwizzle."""
    R = 0,
    G = 1,
    B = 2,
    A = 3,
    ZERO = 4,
    ONE = 5,
    Z = 6,


class AstcencSwizzle(ctypes.Structure):
    """A texel component swizzle."""
    _fields_ = [
        ('r', ctypes.c_int),
        ('g', ctypes.c_int),
        ('b', ctypes.c_int),
        ('a', ctypes.c_int),
    ]


def get_bgra_swizzle():
    swizzle = AstcencSwizzle()
    swizzle.r = ASTCENC_SWZ.B
    swizzle.g = ASTCENC_SWZ.G
    swizzle.b = ASTCENC_SWZ.R
    swizzle.a = ASTCENC_SWZ.A
    return swizzle


class ASTCENC_TYPE(IntEnum):
    """Enum for data_type in AstcencImage."""
    U8 = 0
    F16 = 1
    F32 = 2


PointerToPointer = ctypes.POINTER(ctypes.c_void_p)


class AstcencImage(ctypes.Structure):
    """Uncompressed image."""
    _fields_ = [
        ('dim_x', ctypes.c_uint),
        ('dim_y', ctypes.c_uint),
        ('dim_z', ctypes.c_uint),
        ('data_type', ctypes.c_int),
        ('data', PointerToPointer),
    ]
