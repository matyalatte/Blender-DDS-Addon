"""Tests for import_dds.py and export_dds.py"""
import os
import pytest

from blender_dds_addon.ui import import_dds
from blender_dds_addon.ui import export_dds
from blender_dds_addon.ui import custom_properties

import bpy
bpy.utils.register_class(custom_properties.DDSCustomProperties)
custom_properties.add_custom_props_for_dds()


def get_test_dds():
    test_file = os.path.join("tests", "test.dds")
    return test_file


@pytest.mark.parametrize('export_format', ["BC4_UNORM", "B8G8R8A8_UNORM_SRGB", "R16G16B16A16_FLOAT"])
def test_io(export_format):
    """Cehck if the addon can import and export dds."""
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
    tex = export_dds.save_dds(tex, "saved.dds", "BC1_UNORM", export_as_cubemap=True)
    os.remove("saved.dds")
