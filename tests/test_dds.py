"""Tests for import_dds.py and export_dds.py"""
import os
import pytest

from blender_dds_addon.ui import (import_dds,
                                  export_dds,
                                  texture_list,
                                  custom_properties)
from blender_dds_addon.directx.dds import DDS
from blender_dds_addon.directx.texconv import Texconv, unload_texconv
from blender_dds_addon.astcenc.astcenc import Astcenc, unload_astcenc
import bpy
import numpy as np

bpy.utils.register_class(texture_list.DDSTextureListItem)
bpy.utils.register_class(custom_properties.DDSCustomProperties)
custom_properties.add_custom_props_for_dds()

texconv = Texconv()
texconv.dll.init_com()
astcenc = Astcenc()


def get_test_dds():
    test_file = os.path.join("tests", "2d.dds")
    return test_file


def test_unload_empty_dll():
    unload_texconv()
    unload_astcenc()


def test_unload_dll():
    import_dds.load_dds(get_test_dds())
    unload_texconv()
    unload_astcenc()


@pytest.mark.parametrize("export_format", ["BC4_UNORM", "B8G8R8A8_UNORM_SRGB", "R16G16B16A16_FLOAT"])
def test_io(export_format):
    """Check if the addon can import and export dds."""
    tex = import_dds.load_dds(get_test_dds())
    tex = export_dds.save_dds(tex, "saved.dds", export_format)
    os.remove("saved.dds")


def test_io_nomip():
    """Test no mip option."""
    tex = import_dds.load_dds(get_test_dds())
    tex = export_dds.save_dds(tex, "saved.dds", "BC1_UNORM", no_mip=True)
    os.remove("saved.dds")


def test_io_invert_y():
    """Test invert y option."""
    tex = import_dds.load_dds(get_test_dds())
    tex = export_dds.save_dds(tex, "saved.dds", "BC5_UNORM", invert_normals=True)
    tex = import_dds.load_dds("saved.dds", invert_normals=True)
    os.remove("saved.dds")


def test_io_cubemap():
    """Test with cubemap."""
    tex = import_dds.load_dds(os.path.join("tests", "cube.dds"))
    tex = export_dds.save_dds(tex, "saved.dds", "BC1_UNORM", texture_type="cube")
    os.remove("saved.dds")


@pytest.mark.parametrize("texture_type", ["2d_array", "volume", "cube_array"])
def test_io_array(texture_type):
    """Test with texture arrays."""
    tex = import_dds.load_dds(os.path.join("tests", texture_type + ".dds"))
    assert tex.dds_props.texture_type == texture_type
    extra_texture_list = tex.dds_props.texture_list
    extra_texture_list = [t.texture for t in extra_texture_list]
    tex = export_dds.save_dds(tex, "saved.dds", "BC1_UNORM", texture_type=texture_type,
                              extra_texture_list=extra_texture_list)
    os.remove("saved.dds")


def test_io_array_with_mips():
    """Test with 2d array that has mipmaps."""
    tex = import_dds.load_dds(os.path.join("tests", "2d_array_mips.dds"))
    tex = export_dds.save_dds(tex, "saved.dds", "BC1_UNORM", texture_type="2d_array")
    os.remove("saved.dds")


def test_io_bc7():
    """Test with BC7 textures."""
    tex = import_dds.load_dds(os.path.join("tests", "bc7.dds"))
    tex = export_dds.save_dds(tex, "saved.dds", "BC7_UNORM",
                              texture_type="2d", allow_slow_codec=True)
    os.remove("saved.dds")


def test_io_astc():
    """Test with ASTC textures."""
    tex = import_dds.load_dds(os.path.join("tests", "astc.dds"))
    tex = export_dds.save_dds(tex, "saved.dds", "ASTC_6X6_UNORM",
                              texture_type="2d")
    os.remove("saved.dds")


def test_io_snorm():
    """Test with SNORM textures."""
    tex = import_dds.load_dds(os.path.join("tests", "snorm.dds"))
    tex = export_dds.save_dds(tex, "saved.dds", "R8G8B8A8_SNORM",
                              texture_type="2d")
    os.remove("saved.dds")


def get_first_pixel(tex):
    width, height = tex.size
    return np.array(tex.pixels[(height - 1) * width * 4: (height - 1) * width * 4 + 4], dtype=np.float16)


def pixel_comp(pixel, expected, tol=1e-03):
    return np.isclose(pixel, expected, rtol=tol, atol=tol).all()


def test_float_alpha():
    """Test if the addon preserve alpha for HDR textures."""
    tex = import_dds.load_dds(os.path.join("tests", "rgba16_float.dds"))
    raw_pixel = get_first_pixel(tex)
    assert pixel_comp(raw_pixel, [0.098, 0.4353, 0.0353, 0.502])
    tex = export_dds.save_dds(tex, "saved.dds", "R16G16B16A16_FLOAT",
                              texture_type="2d")
    dds = DDS.load("saved.dds")
    assert dds.header.has_mips()
    buffer = dds.slice_bin_list[0]
    pixel = np.frombuffer(buffer[:8], dtype=np.float16)
    assert pixel_comp(pixel, [0.098, 0.4353, 0.0353, 0.502])
    os.remove("saved.dds")


def test_float_premultiplied_alpha():
    """Test if the addon handle premultiplied alpha for HDR textures."""
    # Check the default RGBA
    dds = DDS.load(os.path.join("tests", "rgba16_float.dds"))
    buffer = dds.slice_bin_list[0]
    pixel = np.frombuffer(buffer[:8], dtype=np.float16)
    expected = np.array([0.098, 0.4353, 0.0353, 0.502], dtype=np.float16)
    assert pixel_comp(pixel, expected)

    # RGB should be divided by alpha when importing
    tex = import_dds.load_dds(os.path.join("tests", "rgba16_float.dds"), premultiplied_alpha=True)
    fixed_pixel = get_first_pixel(tex)
    expected[:3] /= expected[3]
    assert pixel_comp(fixed_pixel, expected)

    # RGB should be multiplied by alpha when exporting
    tex = export_dds.save_dds(tex, "saved.dds", "R16G16B16A16_FLOAT",
                              texture_type="2d", premultiplied_alpha=True)
    dds = DDS.load("saved.dds")
    buffer = dds.slice_bin_list[0]
    pixel = np.frombuffer(buffer[:8], dtype=np.float16)
    expected[:3] *= expected[3]
    assert pixel_comp(pixel, expected)

    os.remove("saved.dds")


def test_bc3_premultiplied_alpha():
    """Test if the addon handle premultiplied alpha for LDR textures."""
    # Check the default RGBA
    tex = import_dds.load_dds(os.path.join("tests", "premultiplied_alpha.dds"))
    raw_pixel = get_first_pixel(tex)
    expected = np.array([0.0627, 0.3176, 0.0314, 0.7490], dtype=np.float16)
    assert pixel_comp(raw_pixel, expected)

    # RGB should be divided by alpha when importing
    tex = import_dds.load_dds(os.path.join("tests", "premultiplied_alpha.dds"), premultiplied_alpha=True)
    fixed_pixel = get_first_pixel(tex)
    raw_pixel[:3] /= raw_pixel[3]
    assert pixel_comp(fixed_pixel, raw_pixel, tol=1/255)

    # RGB should be multiplied by alpha when exporting
    tex = export_dds.save_dds(tex, "saved.dds", "BC3_UNORM",
                              texture_type="2d", premultiplied_alpha=True)
    tex = import_dds.load_dds("saved.dds")
    raw_pixel = get_first_pixel(tex)
    assert pixel_comp(raw_pixel, expected)

    os.remove("saved.dds")


@pytest.mark.parametrize("image_filter", ["POINT", "CUBIC"])
def test_io_filter(image_filter):
    """Test filter options."""
    tex = import_dds.load_dds(get_test_dds())
    tex = export_dds.save_dds(tex, "saved.dds", "BC1_UNORM", image_filter=image_filter)
    os.remove("saved.dds")
