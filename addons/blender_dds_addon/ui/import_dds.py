"""UI panel and operator to import DDS files."""

import os
import time
import shutil
import tempfile
import traceback

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import numpy as np

from ..directx.dds import DDSHeader
from ..directx.texconv import Texconv
from .bpy_util import get_image_editor_space, load_texture, dds_properties_exist
from .export_dds import DDS_FMT_NAMES


def load_dds(file, invert_normals=False, cubemap_layout='h-cross', texconv=None):
    """Import a texture form .dds file.

    Args:
        file (string): file path to .dds file
        invert_normals (bool): Flip y axis if the texture is normal map.
        cubemap_layout (string): Layout for cubemap faces.
        texconv (Texconv): Texture converter for dds.

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    tex = None
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = os.path.join(temp_dir, os.path.basename(file))
            shutil.copyfile(file, temp)
            if texconv is None:
                texconv = Texconv()

            temp_tga = texconv.convert_to_tga(temp, out=temp_dir, cubemap_layout=cubemap_layout,
                                              invert_normals=invert_normals)
            if temp_tga is None:  # if texconv doesn't exist
                raise RuntimeError('Failed to convert texture.')

            # Check dxgi_format
            dds_header = DDSHeader.read_from_file(temp)
            if dds_header.is_srgb():
                color_space = 'sRGB'
            else:
                color_space = 'Non-Color'

            tex = load_texture(temp_tga, name=os.path.basename(temp_tga)[:-4], color_space=color_space)

            dxgi = dds_header.get_format_as_str()
            if dds_properties_exist():
                props = tex.dds_props
                if dxgi in DDS_FMT_NAMES:
                    props.dxgi_format = dds_header.get_format_as_str()
                props.no_mip = dds_header.mipmap_num <= 1
                props.is_cube = dds_header.is_cube()
                if props.is_cube:
                    props.cubemap_layout = cubemap_layout

    except Exception as e:
        if tex is not None:
            bpy.data.images.remove(tex)
        raise e

    if cubemap_layout.endswith("-fnz"):
        w, h = tex.size
        pix = np.array(tex.pixels).reshape((h, w, -1))
        if cubemap_layout[0] == "v":
            pix[h//4 * 0: h//4 * 1, w//3 * 1: w//3 * 2] = (pix[h//4 * 0: h//4 * 1, w//3 * 1: w//3 * 2])[::-1, ::-1]
        else:
            pix[h//3 * 1: h//3 * 2, w//4 * 3: w//4 * 4] = (pix[h//3 * 1: h//3 * 2, w//4 * 3: w//4 * 4])[::-1, ::-1]
        pix = pix.flatten()
        tex.pixels = list(pix)
    tex.update()
    return tex


class DDS_OT_import_dds(Operator, ImportHelper):
    """Operator to import .dds files."""
    bl_idname = 'dds.import_dds'
    bl_label = 'Import DDS'
    bl_description = 'Import .dds files'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default='*.dds; *.DDS', options={'HIDDEN'})

    filepath: StringProperty(subtype='FILE_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    def draw(self, context):
        """Draw options for file picker."""
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.
        dds_options = context.scene.dds_options
        layout.prop(dds_options, 'invert_normals')
        layout.prop(dds_options, 'cubemap_layout')

    def invoke(self, context, event):
        """Invoke."""
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        """Run the operator."""
        if not self.directory:
            raise RuntimeError('"self.directory" is not specified. This is unexpected.')
        for _, file in enumerate(self.files):
            ret = self.import_dds(context, os.path.join(self.directory, file.name))
            if ret != {'FINISHED'}:
                return ret
        return ret

    def import_dds(self, context, file):
        """Import a file."""
        try:
            start_time = time.time()
            space = get_image_editor_space(context)
            dds_options = context.scene.dds_options
            tex = load_dds(file, invert_normals=dds_options.invert_normals,
                           cubemap_layout=dds_options.cubemap_layout)
            space.image = tex
            elapsed_s = f'{(time.time() - start_time):.2f}s'
            m = f'Success! Imported DDS in {elapsed_s}'
            print(m)
            self.report({'INFO'}, m)
            ret = {'FINISHED'}

        except Exception as e:
            print(traceback.format_exc())
            self.report({'ERROR'}, e.args[0])
            ret = {'CANCELLED'}
        return ret


class DDS_PT_import_panel(bpy.types.Panel):
    """UI panel for improt function."""
    bl_label = "Import DDS"
    bl_idname = 'DDS_PT_import_panel'
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "DDS"

    def draw(self, context):
        """Draw UI panel."""
        layout = self.layout
        layout.operator(DDS_OT_import_dds.bl_idname, icon='TEXTURE_DATA')
        dds_options = context.scene.dds_options
        layout.prop(dds_options, 'invert_normals')
        layout.prop(dds_options, 'cubemap_layout')


classes = (
    DDS_OT_import_dds,
    DDS_PT_import_panel,
)


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
