"""Class for DDS files."""

import ctypes as c
from enum import Enum

from . import util
from .dxgi_format import DXGI_FORMAT, FOURCC_TO_DXGI, BITMASK_TO_DXGI


class PF_FLAGS(Enum):
    '''dwFlags for DDS_PIXELFORMAT'''
    # DDS_ALPHAPIXELS = 0x00000001
    # DDS_ALPHA = 0x00000002
    DDS_FOURCC = 0x00000004
    # DDS_RGB = 0x00000040
    # DDS_LUMINANCE = 0x00020000
    DDS_BUMPDUDV = 0x00080000


UNCANONICAL_FOURCC = [
    # fourCC for uncanonical formats (ETC, PVRTC, ATITC, ASTC)
    b"ETC",
    b"ETC1",
    b"ETC2",
    b"ET2A",
    b"PTC2",
    b"PTC4",
    b"ATC",
    b"ATCA",
    b"ATCE",
    b"ATCI",
    b"AS44",
    b"AS55",
    b"AS66",
    b"AS85",
    b"AS86",
    b"AS:5"
]


HDR_SUPPORTED = [
    # Convertible as a decompressed format
    "BC6H_TYPELESS",
    "BC6H_UF16",
    "BC6H_SF16",

    # Directory convertible
    "R32G32B32A32_FLOAT",
    "R16G16B16A16_FLOAT",
    "R32G32B32_FLOAT"
]


TGA_SUPPORTED = [
    # Convertible as a decompressed format
    "BC1_TYPELESS",
    "BC1_UNORM",
    "BC1_UNORM_SRGB",
    "BC2_TYPELESS",
    "BC2_UNORM",
    "BC2_UNORM_SRGB",
    "BC3_TYPELESS",
    "BC3_UNORM",
    "BC3_UNORM_SRGB",
    "BC4_TYPELESS",
    "BC4_UNORM",
    "BC4_SNORM",
    "BC7_TYPELESS",
    "BC7_UNORM",
    "BC7_UNORM_SRGB",

    # Directory convertible
    "R8G8B8A8_UNORM",
    "R8G8B8A8_UNORM_SRGB",
    "B8G8R8A8_UNORM",
    "B8G8R8A8_UNORM_SRGB",
    "B8G8R8X8_UNORM",
    "B8G8R8X8_UNORM_SRGB",
    "R8_UNORM",
    "A8_UNORM",
    "B5G5R5A1_UNORM"
]


def is_hdr(name):
    return 'BC6' in name or 'FLOAT' in name


def convertible_to_tga(name):
    return name in TGA_SUPPORTED


def convertible_to_hdr(name):
    return name in HDR_SUPPORTED


class DDSHeader(c.LittleEndianStructure):
    MAGIC = b'DDS '
    _pack_ = 1
    _fields_ = [
        ("magic", c.c_char * 4),             # Magic == 'DDS '
        ("head_size", c.c_uint32),           # Size == 124
        ("flags", c.c_uint8 * 4),            # [7, 16, 8 + 2 * hasMips, 0]
        ("height", c.c_uint32),
        ("width", c.c_uint32),
        ("pitch_size", c.c_uint32),          # Data size of the largest mipmap
        ("depth", c.c_uint32),
        ("mipmap_num", c.c_uint32),
        ("reserved", c.c_uint32 * 9),        # Reserved1
        ("tool_name", c.c_char * 4),         # Reserved1
        ("null", c.c_uint32),                # Reserved1
        ("pfsize", c.c_uint32),              # PfSize == 32
        ("pfflags", c.c_uint32),             # PfFlags (if 4 then FourCC is used)
        ("fourCC", c.c_char * 4),            # FourCC
        ("bit_count", c.c_uint32),           # Bitcount
        ("bit_mask", c.c_uint32 * 4),        # Bitmask
        ("caps", c.c_uint8 * 4),             # [8 * hasMips, 16, 64 * hasMips, 0]
        ("caps2", c.c_uint8 * 4),            # [0, 254 * isCubeMap, 0, 0]
        ("reserved2", c.c_uint32 * 3),       # ReservedCpas, Reserved2
    ]

    def __init__(self):
        super().__init__()
        self.mipmap_num = 0
        self.dxgi_format = DXGI_FORMAT.DXGI_FORMAT_UNKNOWN

    @staticmethod
    def read(f):
        """Read dds header."""
        head = DDSHeader()
        f.readinto(head)
        util.check(head.magic, DDSHeader.MAGIC, msg='Not DDS.')
        util.check(head.head_size, 124, msg='Not DDS.')
        head.mipmap_num += head.mipmap_num == 0

        ERR_MSG = "Customized formats (e.g. ETC, PVRTC, ATITC, and ASTC) are unsupported."

        if not head.is_canonical():
            raise RuntimeError(f"Non-standard fourCC detected. ({head.fourCC.decode()})\n" + ERR_MSG)

        # DXT10 header
        if head.fourCC == b'DX10':
            fmt = util.read_uint32(f)
            if fmt > DXGI_FORMAT.get_max():
                raise RuntimeError(f"Unsupported DXGI format detected. ({fmt})\n" + ERR_MSG)

            head.dxgi_format = DXGI_FORMAT(fmt)  # dxgiFormat
            util.read_const_uint32(f, 3)         # resourceDimension == 3
            f.seek(4, 1)                         # miscFlag == 0 or 4 (0 for 2D textures, 4 for Cube maps)
            util.read_const_uint32(f, 1)         # arraySize == 1
            f.seek(4, 1)                         # miscFlag2
        else:
            head.dxgi_format = head.get_dxgi_from_header()
        return head

    @staticmethod
    def read_from_file(file_name):
        """Read dds header from a file."""
        with open(file_name, 'rb') as f:
            head = DDSHeader.read(f)
        return head

    def write(self, f):
        f.write(self)
        # DXT10 header
        if self.fourCC == b'DX10':
            util.write_uint32(f, self.dxgi_format.value)
            util.write_uint32(f, 3)
            util.write_uint32(f, 4 * self.is_cube())
            util.write_uint32(f, 1)
            util.write_uint32(f, 0)

    def is_bit_mask(self, bit_mask):
        for b1, b2 in zip(self.bit_mask, bit_mask):
            if b1 != b2:
                return False
        return True

    def get_dxgi_from_header(self):
        '''Similar method as GetDXGIFormat in DirectXTex/DDSTextureLoader/DDSTextureLoader12.cpp'''
        # Try to detect DXGI from fourCC.
        if self.pfflags & PF_FLAGS.DDS_FOURCC.value:
            for cc_list, dxgi in FOURCC_TO_DXGI:
                if self.fourCC in cc_list:
                    return dxgi

        # Try to detect DXGI from bit mask.
        detected_dxgi = None
        for bit_mask, dxgi in BITMASK_TO_DXGI:
            if self.is_bit_mask(bit_mask):
                detected_dxgi = dxgi

        if detected_dxgi is None:
            print("Failed to detect dxgi format. It'll be loaded as B8G8R8A8.")
            return DXGI_FORMAT.DXGI_FORMAT_B8G8R8A8_UNORM

        if self.pfflags & PF_FLAGS.DDS_BUMPDUDV.value:
            # DXGI format should be signed.
            return DXGI_FORMAT.get_signed(detected_dxgi)
        else:
            return detected_dxgi

    def is_cube(self):
        return self.caps2[1] == 254

    def is_3d(self):
        return self.depth > 1

    def is_hdr(self):
        return is_hdr(self.dxgi_format.name)

    def is_bc5(self):
        return 'BC5' in self.dxgi_format.name

    def get_format_as_str(self):
        return self.dxgi_format.name

    def is_srgb(self):
        return 'SRGB' in self.dxgi_format.name

    def is_int(self):
        return 'INT' in self.dxgi_format.name

    def is_canonical(self):
        return self.fourCC not in UNCANONICAL_FOURCC

    def convertible_to_tga(self):
        name = self.dxgi_format.name[12:]
        return convertible_to_tga(name)

    def convertible_to_hdr(self):
        name = self.dxgi_format.name[12:]
        return convertible_to_hdr(name)
