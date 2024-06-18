"""Class for DDS files.

Notes:
    - Official document for DDS header
      https://learn.microsoft.com/en-us/windows/win32/direct3ddds/dds-header
    - Official repo for DDS
      https://github.com/microsoft/DirectXTex
"""

import ctypes as c
from enum import IntEnum
import math
import os

from . import util
from .dxgi_format import DXGI_FORMAT, FOURCC_TO_DXGI, BITMASK_TO_DXGI


class PF_FLAGS(IntEnum):
    '''dwFlags for DDS_PIXELFORMAT'''
    # ALPHAPIXELS = 0x00000001
    # ALPHA = 0x00000002
    FOURCC = 0x00000004
    # RGB = 0x00000040
    # LUMINANCE = 0x00020000
    BUMPDUDV = 0x00080000


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
    b"AS:5"
]


class DDSPixelFormat(c.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c.c_uint32),              # PfSize == 32
        ("flags", c.c_uint32),             # PfFlags (if 4 then FourCC is used)
        ("fourCC", c.c_char * 4),            # FourCC
        ("bit_count", c.c_uint32),           # Bitcount
        ("bit_mask", c.c_uint32 * 4),        # Bitmask
    ]

    def __init__(self):
        super().__init__()
        self.size = 32
        self.flags = (c.c_uint32)(PF_FLAGS.FOURCC)
        self.fourCC = b"DX10"
        self.bit_count = (c.c_uint32)(0)
        self.bit_mask = (c.c_uint32 * 4)((0) * 4)

    def get_dxgi(self):
        '''Similar method as GetDXGIFormat in DirectXTex/DDSTextureLoader/DDSTextureLoader12.cpp'''

        if not self.is_canonical():
            raise RuntimeError(f"Non-standard fourCC detected. ({self.fourCC.decode()})")

        # Try to detect DXGI from fourCC.
        if self.flags & PF_FLAGS.FOURCC:
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
            return DXGI_FORMAT.B8G8R8A8_UNORM

        if self.flags & PF_FLAGS.BUMPDUDV:
            # DXGI format should be signed.
            return DXGI_FORMAT.get_signed(detected_dxgi)
        else:
            return detected_dxgi

    def is_bit_mask(self, bit_mask):
        for b1, b2 in zip(self.bit_mask, bit_mask):
            if b1 != b2:
                return False
        return True

    def is_canonical(self):
        return self.fourCC not in UNCANONICAL_FOURCC

    def is_dx10(self):
        return self.fourCC == b"DX10"


class DDS_FLAGS(IntEnum):
    CAPS = 0x1
    HEIGHT = 0x2
    WIDTH = 0x4
    PITCH = 0x8  # Use "w * bpp" for pitch_or_linear_size
    PIXELFORMAT = 0x1000
    MIPMAPCOUNT = 0x20000
    LINEARSIZE = 0x80000  # Use "w * h * bpp" for pitch_or_linear_size
    DEPTH = 0x800000  # For volume textures
    DEFAULT = CAPS | HEIGHT | WIDTH | PIXELFORMAT | MIPMAPCOUNT

    @staticmethod
    def get_flags(is_compressed, is_3d):
        flags = DDS_FLAGS.DEFAULT
        if is_compressed:
            flags |= DDS_FLAGS.LINEARSIZE
        else:
            flags |= DDS_FLAGS.PITCH
        if is_3d:
            flags |= DDS_FLAGS.DEPTH
        return flags

    @staticmethod
    def has_pitch(flags):
        return (flags & DDS_FLAGS.PITCH) > 0


class DDS_CAPS(IntEnum):
    CUBEMAP = 0x8      # DDSCAPS_COMPLEX
    MIPMAP = 0x400008  # DDSCAPS_COMPLEX | DDSCAPS_MIPMAP
    REQUIRED = 0x1000  # DDSCAPS_TEXTURE

    @staticmethod
    def get_caps(has_mips, is_cube):
        caps = DDS_CAPS.REQUIRED
        if has_mips:
            caps |= DDS_CAPS.MIPMAP
        if is_cube:
            caps |= DDS_CAPS.CUBEMAP
        return caps


class DDS_CAPS2(IntEnum):
    CUBEMAP = 0x200
    CUBEMAP_POSITIVEX = 0x400
    CUBEMAP_NEGATIVEX = 0x800
    CUBEMAP_POSITIVEY = 0x1000
    CUBEMAP_NEGATIVEY = 0x2000
    CUBEMAP_POSITIVEZ = 0x4000
    CUBEMAP_NEGATIVEZ = 0x8000
    CUBEMAP_FULL = 0xFE00  # for cubemap that have all faces
    VOLUME = 0x200000

    @staticmethod
    def get_caps2(is_cube, is_3d):
        caps2 = 0
        if is_cube:
            caps2 |= DDS_CAPS2.CUBEMAP_FULL
        if is_3d:
            caps2 |= DDS_CAPS2.VOLUME
        return caps2

    @staticmethod
    def is_cube(caps2):
        return (caps2 & DDS_CAPS2.CUBEMAP) > 0

    @staticmethod
    def is_3d(caps2):
        return (caps2 & DDS_CAPS2.VOLUME) > 0

    @staticmethod
    def is_partial_cube(caps2):
        return DDS_CAPS2.is_cube(caps2) and (caps2 != DDS_CAPS2.CUBEMAP_FULL)


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


class DX10Header(c.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("dxgi_format", c.c_uint32),
        ("resource_dimension", c.c_uint32),
        ("misc_flags", c.c_uint32),
        ("array_size", c.c_uint32),
        ("misc_flags2", c.c_uint32)
    ]

    def get_dxgi(self):
        if self.dxgi_format not in [fmt.value for fmt in DXGI_FORMAT]:
            raise RuntimeError(f"Unsupported DXGI format detected. ({self.dxgi_format})")
        return DXGI_FORMAT(self.dxgi_format)

    def update(self, dxgi_format, is_cube, is_3d, array_size):
        self.dxgi_format = int(dxgi_format)
        self.resource_dimension = 3 + is_3d
        self.misc_flags = 4 * is_cube
        self.array_size = array_size
        self.misc_flags2 = 0

    def is_array(self):
        return self.array_size > 1


def is_hdr(name: str):
    return 'BC6' in name or 'FLOAT' in name


def is_signed(name: str):
    return 'SNORM' in name or 'SF16' in name


def convertible_to_tga(name: str):
    return name in TGA_SUPPORTED


def convertible_to_hdr(name: str):
    return name in HDR_SUPPORTED


class DDSHeader(c.LittleEndianStructure):
    MAGIC = b'DDS '
    _pack_ = 1
    _fields_ = [
        ("magic", c.c_char * 4),               # Magic == 'DDS '
        ("head_size", c.c_uint32),             # Size == 124
        ("flags", c.c_uint32),                 # DDS_FLAGS
        ("height", c.c_uint32),
        ("width", c.c_uint32),
        ("pitch_or_linear_size", c.c_uint32),  # w * h * bpp for compressed, w * bpp for uncompressed
        ("depth", c.c_uint32),
        ("mipmap_num", c.c_uint32),
        ("reserved", c.c_uint32 * 9),          # Reserved1
        ("tool_name", c.c_char * 4),           # Reserved1
        ("null", c.c_uint32),                  # Reserved1
        ("pixel_format", DDSPixelFormat),
        ("caps", c.c_uint32),                  # DDS_CAPS
        ("caps2", c.c_uint32),                 # DDS_CAPS2
        ("reserved2", c.c_uint32 * 3),         # ReservedCpas, Reserved2
    ]

    def __init__(self):
        super().__init__()
        self.magic = DDSHeader.MAGIC
        self.head_size = 124
        self.mipmap_num = 1
        self.pixel_format = DDSPixelFormat()
        self.reserved = (c.c_uint32 * 9)((0) * 9)
        self.tool_name = b"BLND"
        self.null = 0
        self.reserved2 = (c.c_uint32*3)(0, 0, 0)
        self.dx10_header = DX10Header()

        self.dxgi_format = DXGI_FORMAT.UNKNOWN
        self.byte_per_pixel = 0

    @staticmethod
    def read(f):
        """Read dds header."""
        head = DDSHeader()
        f.readinto(head)
        head.mipmap_num += head.mipmap_num == 0

        # DXT10 header
        if head.pixel_format.is_dx10():
            f.readinto(head.dx10_header)
            head.dxgi_format = head.dx10_header.get_dxgi()
        else:
            head.dxgi_format = head.pixel_format.get_dxgi()
            head.dx10_header.update(head.dxgi_format, head.is_cube(), head.is_3d(), 1)

        # Raise errors for unsupported files
        if head.magic != DDSHeader.MAGIC or head.head_size != 124:
            raise RuntimeError("Not DDS file.")
        if head.dx10_header.resource_dimension == 2:
            raise RuntimeError("1D textures are unsupported.")

        return head

    @staticmethod
    def read_from_file(file_name):
        """Read dds header from a file."""
        with open(file_name, 'rb') as f:
            head = DDSHeader.read(f)
        return head

    def write(self, f):
        f.write(self)
        if self.pixel_format.is_dx10():
            f.write(self.dx10_header)

    def update(self, depth, array_size):
        self.depth = depth

        has_mips = self.has_mips()
        is_3d = self.is_3d()
        is_cube = self.is_cube()
        bpp = self.get_bpp()

        self.flags = DDS_FLAGS.get_flags(self.is_compressed(), is_3d)
        if DDS_FLAGS.has_pitch(self.flags):
            self.pitch_or_linear_size = int(self.width * bpp)
        else:
            self.pitch_or_linear_size = int(self.width * self.height * bpp)
        self.caps = DDS_CAPS.get_caps(has_mips, is_cube)
        self.caps2 = DDS_CAPS2.get_caps2(is_cube, is_3d)

        self.dx10_header.update(self.dxgi_format, is_cube, is_3d, array_size)
        self.pixel_format = DDSPixelFormat()

    def get_bpp(self):
        bpp = self.pitch_or_linear_size // self.width
        if not DDS_FLAGS.has_pitch(self.flags):
            bpp = bpp // self.height
        return bpp

    def is_compressed(self):
        dxgi = self.get_format_as_str()
        return "BC" in dxgi or "ASTC" in dxgi

    def has_mips(self):
        return self.mipmap_num > 1

    def is_cube(self):
        return DDS_CAPS2.is_cube(self.caps2)

    def is_3d(self):
        return self.depth > 1

    def is_array(self):
        return self.dx10_header.is_array()

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

    def is_signed(self):
        return is_signed(self.dxgi_format.name)

    def is_canonical(self):
        return self.fourCC not in UNCANONICAL_FOURCC

    def is_official(self):
        if "ASTC" in self.get_format_as_str():
            return False
        return True

    def is_astc(self):
        return "ASTC" in self.get_format_as_str()

    def is_partial_cube(self):
        return DDS_CAPS2.is_partial_cube(self.caps2)

    def convertible_to_tga(self):
        name = self.get_format_as_str()
        return convertible_to_tga(name)

    def convertible_to_hdr(self):
        name = self.get_format_as_str()
        return convertible_to_hdr(name)

    def get_array_size(self):
        return self.dx10_header.array_size

    def get_num_slices(self):
        return self.get_array_size() * self.depth * (1 + (self.is_cube() * 5))

    def disassemble(self):
        self.update(1, 1)

    def assemble(self, is_array, size):
        if is_array:
            self.update(1, size)
        else:
            self.update(size, 1)

    def get_texture_type(self):
        if self.is_3d():
            return "volume"
        if self.is_cube():
            t = "cube"
        else:
            t = "2d"
        if self.is_array():
            t += "_array"
        return t

    def get_block_size(self):
        fmt = self.get_format_as_str()
        if ("ASTC" in fmt):
            parsed = fmt.split("_")[1].split("X")
            return (int(parsed[0]), int(parsed[1]))
        if ("BC" in fmt):
            return (4, 4)
        return (1, 1)

    def get_byte_per_block(self):
        fmt = self.get_format_as_str()
        if ("ASTC" in fmt):
            return 16
        if ("B8G8R8A8" in fmt):
            return 4
        if ("R16G16B16A16" in fmt):
            return 8
        if ("R32G32B32A32" in fmt):
            return 16
        raise RuntimeError(f"get_byte_per_block() does not support {fmt}.")

    def get_mip_sizes(self):
        """Calculate texture size and binary size of mipmaps"""
        mipmap_sizes = []
        width, height = self.width, self.height
        block_x, block_y = self.get_block_size()
        byte_per_block = self.get_byte_per_block()
        bin_pos = 0

        for i in range(self.mipmap_num):
            block_count_x = math.ceil(width / block_x)
            block_count_y = math.ceil(height / block_y)

            bin_size = block_count_x * block_count_y * byte_per_block
            mipmap_sizes.append([width, height, bin_pos, bin_size])
            bin_pos += bin_size
            width, height = width // 2, height // 2
            width, height = max(width, 1), max(height, 1)

        return mipmap_sizes

    def change_dxgi_format(self, dxgi_format):
        self.pixel_format = DDSPixelFormat()
        self.dxgi_format = dxgi_format
        self.update(self.depth, self.get_array_size())


class DDS:
    def __init__(self, header, slices=None):
        self.header = header
        self.slice_bin_list = slices

    @staticmethod
    def load(file, verbose=False):
        with open(file, 'rb') as f:
            header = DDSHeader.read(f)
            data_size = util.get_size(f) - f.tell()
            num_slices = header.get_num_slices()
            slice_size = data_size // num_slices
            slices = [f.read(slice_size) for i in range(num_slices)]
        return DDS(header, slices)

    def save(self, file):
        folder = os.path.dirname(file)
        if folder not in ['.', ''] and not os.path.exists(folder):
            util.mkdir(folder)

        with open(file, 'wb') as f:
            self.header.write(f)
            for d in self.slice_bin_list:
                f.write(d)

    def is_cube(self):
        return self.header.is_cube()

    def get_array_size(self):
        return self.header.get_array_size()

    def get_disassembled_dds_list(self):
        new_dds_num = self.header.depth * self.get_array_size()
        num_slices = 1 + (5 * self.is_cube())
        self.header.disassemble()
        dds_list = []
        for i in range(new_dds_num):
            dds = DDS(
                self.header,
                self.slice_bin_list[i * num_slices: (i + 1) * num_slices]
            )
            dds_list.append(dds)
        return dds_list

    @staticmethod
    def assemble(dds_list, is_array=True):
        header = dds_list[0].header
        header.assemble(is_array, len(dds_list))
        for dds in dds_list[1:]:
            if header.dxgi_format != dds.header.dxgi_format:
                raise RuntimeError("Failed to assemble dds files. DXGI formats should be the same")
            if header.width != dds.header.width or header.height != dds.header.height:
                raise RuntimeError("Failed to assemble dds files. Texture sizes should be the same")
        slice_bin_list = sum([dds.slice_bin_list for dds in dds_list], [])
        return DDS(header, slice_bin_list)

    def remove_mips(self):
        block_x, block_y = self.header.get_block_size()
        w, h = self.header.width, self.header.height
        bin_size = math.ceil(w / block_x) * math.ceil(h / block_y) * self.header.get_byte_per_block()
        self.header.mipmap_num = 1
        self.slice_bin_list = [b[:bin_size] for b in self.slice_bin_list]

    def decompress_astc(self, astcenc):
        block_x, block_y = self.header.get_block_size()
        astcenc.config_init(block_x, block_y)

        slices = self.slice_bin_list

        mipmap_sizes = self.header.get_mip_sizes()
        new_slices = []
        for b in slices:
            new_mips = [astcenc.decompress_image(w, h, b[pos: pos + size]) for w, h, pos, size in mipmap_sizes]
            new_bin = b''.join(new_mips)
            new_slices.append(new_bin)
        self.slice_bin_list = new_slices
        self.header.change_dxgi_format(DXGI_FORMAT.B8G8R8A8_UNORM)

    def compress_astc(self, astcenc, astc_fmt):
        block_parsed = astc_fmt.split("_")[1].split("X")
        block_x, block_y = [int(s) for s in block_parsed]
        astcenc.config_init(block_x, block_y)

        slices = self.slice_bin_list
        mipmap_sizes = self.header.get_mip_sizes()
        new_slices = []
        for b in slices:
            new_mips = [astcenc.compress_image(w, h, b[pos: pos + size]) for w, h, pos, size in mipmap_sizes]
            new_bin = b''.join(new_mips)
            new_slices.append(new_bin)
        self.slice_bin_list = new_slices
        dxgi_format = DXGI_FORMAT[astc_fmt]
        self.header.change_dxgi_format(dxgi_format)
