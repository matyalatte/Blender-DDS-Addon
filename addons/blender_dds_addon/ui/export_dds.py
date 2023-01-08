"""UI panel and operator to export DDS files."""

import os
import time
import shutil
import tempfile
import traceback

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
import numpy as np

from ..directx.dds import is_hdr
from ..directx.texconv import Texconv
from .bpy_util import save_texture, dds_properties_exist, get_selected_tex


def save_dds(tex, file, dds_fmt, invert_normals=False, no_mip=False,
             allow_slow_codec=False,
             export_as_cubemap=False,
             cubemap_layout='h-cross',
             texconv=None):
    """Export a texture as DDS.

    Args:
        tex (bpy.types.Image): an image object
        file (string): file path to .dds file
        dds_fmt (string): DXGI format (e.g. BC1_UNORM)
        invert_normals (bool): Flip y axis for BC5 textures.
        no_mip (bool): Disable mipmap generation.
        allow_slow_codec (bool): Allow CPU codec for BC6 and BC7.
        export_as_cubemap (bool): Export textures as cubemap.
        cubemap_layout (string): Layout for cubemap faces.
        texconv (Texconv): Texture converter for dds.

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    # Check color space
    color_space = tex.colorspace_settings.name
    if 'SRGB' in dds_fmt and color_space != 'sRGB':
        print("Warning: Specified DXGI format uses sRGB as a color space,"
              f"but the texture uses {color_space} in Blender")
    elif 'SRGB' not in dds_fmt and color_space not in ['Non-Color', 'Raw']:
        print("Warning: Specified DXGI format does not use any color space conversion,"
              f"but the texture uses {color_space} in Blender")

    if is_hdr(dds_fmt):
        ext = '.hdr'
        fmt = 'HDR'
    else:
        ext = '.tga'
        fmt = 'TARGA_RAW'

    w, h = tex.size

    if export_as_cubemap:
        # Check aspect ratio
        def gcd(m, n):
            r = m % n
            return gcd(n, r) if r else n

        face_size = gcd(w, h)
        w_ratio = w // face_size
        h_ratio = h // face_size

        expected_ratio_dict = {
            "h-cross": [4, 3],
            "v-cross": [3, 4],
            "h-cross-fnz": [4, 3],
            "v-cross-fnz": [3, 4],
            "h-strip": [6, 1],
            "v-strip": [1, 6]
        }

        expected_ratio = expected_ratio_dict[cubemap_layout]

        if w_ratio != expected_ratio[0] or h_ratio != expected_ratio[1]:
            raise RuntimeError((
                f"{cubemap_layout} expects {expected_ratio[0]}:{expected_ratio[1]} aspect ratio "
                f"but the actual ratio is {w_ratio}:{h_ratio}."
            ))

    def get_z_flipped(tex):
        if cubemap_layout == "h-cross-fnz":
            offset = [3, 1]
        elif cubemap_layout == "v-cross-fnz":
            offset = [1, 0]
        temp_tex = tex.copy()
        pix = np.array(tex.pixels).reshape(h, w, -1)
        x, y = [c * face_size for c in offset]
        pix[y: y + face_size, x: x + face_size] = pix[y: y + face_size, x: x + face_size][::-1, ::-1]
        temp_tex.pixels = list(pix.flatten())
        return temp_tex

    def save_temp_dds(tex, temp_dir, ext, fmt, texconv, verbose=True):
        temp = os.path.join(temp_dir, tex.name + ext)

        save_texture(tex, temp, fmt)

        temp_dds = texconv.convert_to_dds(temp, dds_fmt, out=temp_dir,
                                          invert_normals=invert_normals, no_mip=no_mip,
                                          export_as_cubemap=export_as_cubemap,
                                          cubemap_layout=cubemap_layout,
                                          allow_slow_codec=allow_slow_codec, verbose=verbose)
        if temp_dds is None:
            raise RuntimeError('Failed to convert texture.')
        return temp_dds

    try:
        temp_tex = None
        texconv = Texconv()

        with tempfile.TemporaryDirectory() as temp_dir:
            if export_as_cubemap and ('fnz' in cubemap_layout):
                temp_tex = get_z_flipped(tex)
                temp_dds = save_temp_dds(temp_tex, temp_dir, ext, fmt, texconv)
                bpy.data.images.remove(temp_tex)
            else:
                temp_dds = save_temp_dds(tex, temp_dir, ext, fmt, texconv)

            shutil.copyfile(temp_dds, file)

    except Exception as e:
        if temp_tex is not None:
            bpy.data.images.remove(temp_tex)
        raise e

    return tex


def export_as_dds(context, tex, file):
    dds_options = context.scene.dds_options

    if dds_properties_exist():
        props = tex.dds_props
        dxgi = props.dxgi_format
        is_cube = props.is_cube
        cubemap_layout = props.cubemap_layout
        no_mip = props.no_mip
    else:
        dxgi = dds_options.dxgi_format
        is_cube = dds_options.export_as_cubemap
        cubemap_layout = dds_options.cubemap_layout
        no_mip = dds_options.no_mip

    if dxgi == "NONE":
        raise RuntimeError("Select DXGI format.")

    save_dds(tex, file, dxgi,
             invert_normals=dds_options.invert_normals, no_mip=no_mip,
             allow_slow_codec=dds_options.allow_slow_codec,
             export_as_cubemap=is_cube,
             cubemap_layout=cubemap_layout)


def put_export_options(context, layout):
    dds_options = context.scene.dds_options
    if not dds_properties_exist():
        layout.prop(dds_options, 'dxgi_format')
    layout.prop(dds_options, 'invert_normals')
    if not dds_properties_exist():
        layout.prop(dds_options, 'no_mip')
        layout.prop(dds_options, 'export_as_cubemap')
        if dds_options.export_as_cubemap:
            layout.prop(dds_options, 'cubemap_layout')
    layout.prop(dds_options, 'allow_slow_codec')


class DDS_OT_export_base(Operator):
    def draw(self, context):
        """Draw options for file picker."""
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.
        put_export_options(context, layout)

    def execute_base(self, context, file=None, directory=None, is_dir=False):
        try:
            start_time = time.time()

            if is_dir:
                count = 0
                for tex in bpy.data.images:
                    if dds_properties_exist() and tex.dds_props.dxgi_format == "NONE":
                        continue
                    name = tex.name
                    if name[-4:] != ".dds":
                        name += ".dds"
                    file = os.path.join(directory, name)
                    export_as_dds(context, tex, file)
                    count += 1
            else:
                tex = get_selected_tex(context)
                export_as_dds(context, tex, file)
                count = 1

            elapsed_s = f'{(time.time() - start_time):.2f}s'
            if count == 0:
                raise RuntimeError("There is no images that have DXGI format.")
            elif count == 1:
                m = f'Success! Exported {file} in {elapsed_s}'
            else:
                m = f'Success! Exported {count} images in {elapsed_s}'
            print(m)
            self.report({'INFO'}, m)
            ret = {'FINISHED'}

        except Exception as e:
            print(traceback.format_exc())
            self.report({'ERROR'}, e.args[0])
            ret = {'CANCELLED'}
        return ret


class DDS_OT_export_dds(DDS_OT_export_base, ExportHelper):
    """Operator to export selected image as a .dds file."""
    bl_idname = 'dds.export_dds'
    bl_label = 'Export Selected Image'
    bl_description = 'Export selected image as a .dds file'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default='*.dds; *.DDS', options={'HIDDEN'})

    filename_ext = '.dds'

    filepath: StringProperty(
        name='File Path'
    )

    def invoke(self, context, event):
        tex = get_selected_tex(context)
        if dds_properties_exist() and tex.dds_props.dxgi_format == "NONE":
            self.report({'ERROR'}, "Select a DXGI format for the image.")
            return {'CANCELLED'}
        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        return self.execute_base(context, file=self.filepath, is_dir=False)


class DDS_OT_export_all(DDS_OT_export_base):
    """Operator to export all images as .dds files."""
    bl_idname = 'dds.export_all'
    bl_label = 'Export All Images'
    bl_description = 'Export all images that have DXGI format'
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(
        name="target_dir",
        default=''
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return self.execute_base(context, directory=self.directory, is_dir=True)


class DDS_PT_export_panel(bpy.types.Panel):
    """UI panel for improt function."""
    bl_label = "Export as DDS"
    bl_idname = 'DDS_PT_export_panel'
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "DDS"

    def draw(self, context):
        """Draw UI panel."""
        layout = self.layout
        layout.operator(DDS_OT_export_dds.bl_idname, icon='TEXTURE_DATA')
        layout.operator(DDS_OT_export_all.bl_idname, icon='TEXTURE_DATA')
        put_export_options(context, layout)


classes = (
    DDS_OT_export_dds,
    DDS_OT_export_all,
    DDS_PT_export_panel,
)


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
