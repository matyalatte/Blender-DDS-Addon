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

from .dds import DXGI_FORMAT, is_hdr, assemble_cubemap
from .texconv import Texconv


def save_tga(tex, file, fmt):
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
             cubemap_suffix=None,
             texconv=None):
    """Export a texture as DDS.

    Args:
        file (string): file path to .dds file
        dds_fmt (string): DXGI format (e.g. BC1_UNORM)
        invert_normals (bool): Flip y axis for BC5 textures.
        no_mip (bool): Disable mipmap generation.
        allow_slow_codec: Allow CPU codec for BC6 and BC7.
        texconv (Texconv): Texture converter for dds.

    Returns:
        tex (bpy.types.Image): loaded texture
    """

    if cubemap_suffix is None:
        cubemap_suffix = ["x_pos", "x_neg", "y_pos", "y_neg", "z_pos", "z_neg"]

    if export_as_cubemap:
        def get_base(name, suffix_list):
            for suf in suffix_list:
                if name.endswith("_" + suf):
                    return name[:-(len(suf) + 1)]
            return None

        base = get_base(tex.name, cubemap_suffix)
        if base is None:
            msg = (f'Failed to make a cubemap. ({tex.name}'
                   'should have suffix defined with "Suffix Set for Cubemap" option)')
            raise RuntimeError(msg)

        def get_tex_by_name(base, suf, textures):
            tex_name = base + "_" + suf
            for t in textures:
                if t.name == tex_name:
                    return t
            raise RuntimeError(f'Failed to make a cubemap. ({name} not found)')

        textures_ = [img for img in bpy.data.images if base in img.name]
        textures = [get_tex_by_name(base, suf, textures_) for suf in cubemap_suffix]
    else:
        textures = [tex]

    if is_hdr(dds_fmt):
        ext = '.hdr'
        fmt = 'HDR'
    else:
        ext = '.tga'
        fmt = 'TARGA_RAW'

    with tempfile.TemporaryDirectory() as temp_dir:
        dds_list = []
        for tex in textures:
            temp = os.path.join(temp_dir, tex.name + ext)

            save_tga(tex, temp, fmt)

            if texconv is None:
                texconv = Texconv()

            temp_dds = texconv.convert_to_dds(temp, dds_fmt, out=temp_dir,
                                              invert_normals=invert_normals, no_mip=no_mip,
                                              allow_slow_codec=allow_slow_codec)
            if temp_dds is None:
                raise RuntimeError('Failed to convert texture.')
            dds_list.append(temp_dds)
        if len(dds_list) > 1:
            temp_dds = assemble_cubemap(dds_list, os.path.join(temp_dir, "temp.dds"))
        shutil.copyfile(temp_dds, file)

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
    else:
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
        description=("Export 6 textures as a cubemap.\n"
                     'Each texture should have a proper suffix defined with the "Suffix Set for Cubemap" option'),
        default=False,
    )

    cubemap_suffix: EnumProperty(
        name='Suffix Set for Cubemap',
        items=[
            ('AXIS', 'Axis', 'Use "_x_pos", "_x_neg", "_y_pos", "_y_neg", "_z_pos" and "_z_neg"'),
            ('NUMBER', 'Number', 'Use "_0", "_1", "_2", "_3", "_4" and "_5"'),
            ('BLENDER', 'Blender',
             'Use "_left", "_right", "_front", "_back", "_top" and "_bottom" (Right-handed, Z-up)'),
            ('3DSMAX', '3ds Max',
             'Use "_right", "_left", "_back", "_front", "_top" and "_bottom" (Right-handed, Z-up)'),
            ('MAYA', 'Maya', 'Use "_right", "_left", "_top", "_bottom", "_front" and "_back" (Right-handed, Y-up)'),
            ('UNITY', 'Unity', 'Use "_left", "_right", "_top", "_bottom", "_front" and "_back" (Left-handed, Y-up)'),
            ('UNREAL', 'Unreal Engine',
             'Use "_front", "_back", "_left", "_right", "_top" and "_bottom" (Left-handed, Z-up)')
        ],
        description=(
            'Cubemaps will be loaded as 6 textures.\n'
            'For import operations, the addon will append the suffixes to the texture names.\n'
            'For export operations, the addon will use the suffixes to choose textures'
        ),
        default='AXIS'
    )


suffix_set_list = {
    "AXIS": ["x_pos", "x_neg", "y_pos", "y_neg", "z_pos", "z_neg"],
    "NUMBER": ["0", "1", "2", "3", "4", "5"],
    "BLENDER": ["left", "right", "front", "back", "top", "bottom"],
    "3DSMAX": ["right", "left", "back", "front", "top", "bottom"],
    "MAYA": ["right", "left", "top", "bottom", "front", "back"],
    "UNITY": ["left", "right", "top", "bottom", "front", "back"],
    "UNREAL": ["front", "back", "left", "right", "top", "bottom"]
}


def get_cubemap_suffix(suffix_set):
    return suffix_set_list[suffix_set]


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
        layout.prop(dds_options, 'cubemap_suffix')

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
            area = context.area
            if area.type == 'IMAGE_EDITOR':
                space = area.spaces.active
            else:
                raise RuntimeError('Failed to get Image Editor. This is unexpected.')

            tex = space.image
            if tex is None:
                raise RuntimeError('Select an image on Image Editor.')
            dds_options = context.scene.dds_options
            cubemap_suffix = get_cubemap_suffix(dds_options.cubemap_suffix)
            save_dds(tex, file, dds_options.dds_format,
                     invert_normals=dds_options.invert_normals, no_mip=dds_options.no_mip,
                     allow_slow_codec=dds_options.allow_slow_codec,
                     export_as_cubemap=dds_options.export_as_cubemap,
                     cubemap_suffix=cubemap_suffix)

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
        layout.prop(dds_options, 'cubemap_suffix')


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
