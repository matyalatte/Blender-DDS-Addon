"""UI panel and operator to export DDS files."""

import os
import time
import shutil
import tempfile
import traceback

import bpy
from bpy.props import (StringProperty,
                       EnumProperty,
                       BoolProperty,
                       PointerProperty,
                       CollectionProperty)
from bpy.types import Operator, PropertyGroup
from bpy_extras.io_utils import ExportHelper
import numpy as np

from .dds import is_hdr
from .dxgi_format import DXGI_FORMAT
from .texconv import Texconv


def save_texture(tex, file, fmt):
    """Save a texture.

    Args:
        tex (bpy.types.Image): an image object
        file (string): file path
        fmt (string): file format
    """
    file_format = tex.file_format
    filepath_raw = tex.filepath_raw

    try:
        tex.file_format = fmt
        tex.filepath_raw = file
        tex.save()

        tex.file_format = file_format
        tex.filepath_raw = filepath_raw

    except Exception as e:
        tex.file_format = file_format
        tex.filepath_raw = filepath_raw
        raise e


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


fmt_list = [fmt.name[12:] for fmt in DXGI_FORMAT]
fmt_list = [fmt for fmt in fmt_list if "BC" in fmt] + [fmt for fmt in fmt_list if "BC" not in fmt]

dic = {
    "BC1_UNORM": " (DXT1)",
    "BC3_UNORM": " (DXT5)",
    "BC4_UNORM": " (ATI1)",
    "BC5_UNORM": " (ATI2)",
}


def get_alt_fmt(fmt):
    """Add alt name for the format."""
    if fmt in dic:
        return fmt + dic[fmt]
    return fmt


def is_supported(fmt):
    return ('TYPELESS' not in fmt) and ('INT' not in fmt) and \
           (len(fmt) > 4) and (fmt not in ["UNKNOWN", "420_OPAQUE"])


class DDSOptions(PropertyGroup):
    """Properties for general options."""

    dds_format: EnumProperty(
        name='DDS format',
        items=[(fmt, get_alt_fmt(fmt), '') for fmt in fmt_list if is_supported(fmt)],
        description='DXGI format for DDS',
        default='BC1_UNORM'
    )

    invert_normals: BoolProperty(
        name='Invert Normals',
        description="Invert G channel for BC5 textures",
        default=False,
    )

    no_mip: BoolProperty(
        name='No Mipmaps',
        description="Disable mipmap generation",
        default=False,
    )

    allow_slow_codec: BoolProperty(
        name='Allow Slow Codec',
        description=("Allow to use CPU codec for BC6 and BC7.\n"
                     "But it'll take a long time for conversion"),
        default=False,
    )

    export_as_cubemap: BoolProperty(
        name='Export as Cubemap',
        description=("Export a texture as a cubemap.\n"
                     'Faces should be aligned in a layout defined in "Layout for Cubemap Faces" option'),
        default=False,
    )

    cubemap_layout: EnumProperty(
        name='Layout for Cubemap Faces',
        items=[
            ('h-cross', 'Horizontal Cross', 'Align faces in a horizontal cross layout'),
            ('v-cross', 'Vertical Cross', 'Align faces in a vertical cross layout'),
            ('h-cross-fnz', 'Horizontal Cross (Flip -Z)',
             'Align faces in a vertical cross layout. And Rotate -Z face by 180 degrees'),
            ('v-cross-fnz', 'Vertical Cross (Flip -Z)',
             'Align faces in a vertical cross layout. And Rotate -Z face by 180 degrees'),
            ('h-strip', 'Horizontal Strip', 'Align faces horizontaly'),
            ('v-strip', 'Vertical Strip', 'Align faces verticaly'),
        ],
        description=(
            'How to align faces of a cubemap.\n'
        ),
        default='h-cross'
    )


def get_image_editor_space(context):
    area = context.area
    if area.type == 'IMAGE_EDITOR':
        space = area.spaces.active
    else:
        raise RuntimeError('Failed to get Image Editor. This is unexpected.')
    return space


class DDS_OT_export_dds(Operator, ExportHelper):
    """Operator to export .dds files."""
    bl_idname = 'dds.export_dds'
    bl_label = 'Export as DDS'
    bl_description = 'Export .dds files'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default='*.dds; *.DDS', options={'HIDDEN'})

    files: CollectionProperty(
        name='File Path',
        type=bpy.types.OperatorFileListElement,
    )

    filename_ext = '.dds'

    filepath: StringProperty(
        name='File Path'
    )

    def draw(self, context):
        """Draw options for file picker."""
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.
        dds_options = context.scene.dds_options
        layout.prop(dds_options, 'dds_format')
        layout.prop(dds_options, 'invert_normals')
        layout.prop(dds_options, 'no_mip')
        layout.prop(dds_options, 'allow_slow_codec')
        layout.prop(dds_options, 'export_as_cubemap')
        layout.prop(dds_options, 'cubemap_layout')

    def invoke(self, context, event):
        """Invoke."""
        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        """Run the operator."""
        return self.export_dds(context)

    def export_dds(self, context):
        """Export a file."""
        file = self.filepath
        try:
            start_time = time.time()

            space = get_image_editor_space(context)
            tex = space.image
            if tex is None:
                raise RuntimeError('Select an image on Image Editor.')
            dds_options = context.scene.dds_options
            save_dds(tex, file, dds_options.dds_format,
                     invert_normals=dds_options.invert_normals, no_mip=dds_options.no_mip,
                     allow_slow_codec=dds_options.allow_slow_codec,
                     export_as_cubemap=dds_options.export_as_cubemap,
                     cubemap_layout=dds_options.cubemap_layout)

            elapsed_s = f'{(time.time() - start_time):.2f}s'
            m = f'Success! Exported DDS in {elapsed_s}'
            print(m)
            self.report({'INFO'}, m)
            ret = {'FINISHED'}

        except Exception as e:
            print(traceback.format_exc())
            self.report({'ERROR'}, e.args[0])
            ret = {'CANCELLED'}
        return ret


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
        dds_options = context.scene.dds_options
        layout.prop(dds_options, 'dds_format')
        layout.prop(dds_options, 'invert_normals')
        layout.prop(dds_options, 'no_mip')
        layout.prop(dds_options, 'allow_slow_codec')
        layout.prop(dds_options, 'export_as_cubemap')
        layout.prop(dds_options, 'cubemap_layout')


classes = (
    DDSOptions,
    DDS_OT_export_dds,
    DDS_PT_export_panel,
)


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.dds_options = PointerProperty(type=DDSOptions)


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.dds_options
