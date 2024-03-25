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

from ..directx.dds import DDSHeader, DDS
from ..directx.texconv import Texconv, unload_texconv
from ..astcenc.astcenc import Astcenc, unload_astcenc
from .bpy_util import get_image_editor_space, load_texture, dds_properties_exist, flush_stdout
from .custom_properties import DDS_FMT_NAMES


def load_dds(file, invert_normals=False, cubemap_layout='h-cross',
             texconv=None, astcenc=None):
    """Import a texture form .dds file.

    Args:
        file (string): file path to .dds file
        invert_normals (bool): Flip y axis if the texture is normal map.
        cubemap_layout (string): Layout for cubemap faces.
        texconv (Texconv): Texture converter for dds.
        astcenc (Astcenc): Astc converter.

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    tex_list = []
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = os.path.join(temp_dir, os.path.basename(file))
            shutil.copyfile(file, temp)

            if texconv is None:
                texconv = Texconv()
            if astcenc is None:
                astcenc = Astcenc()

            dds_header = DDSHeader.read_from_file(temp)

            if dds_header.is_astc():
                dds = DDS.load(temp)
                dds.remove_mips()
                dds.decompress_astc(astcenc)
                dds.save(temp)

            # Check dxgi_format
            if dds_header.is_srgb():
                color_space = 'sRGB'
            else:
                color_space = 'Non-Color'

            tga_list = []

            # Disassemble if it's a non-2D texture
            if dds_header.is_3d() or dds_header.is_array():
                dds = DDS.load(temp)
                dds_list = dds.get_disassembled_dds_list()
                base_name = os.path.basename(temp)
                for new_dds, i in zip(dds_list, range(len(dds_list))):
                    new_name = ".".join(base_name.split(".")[:-1])
                    if i >= 1:
                        new_name += f"-{i}"
                    new_name += ".dds"
                    new_path = os.path.join(temp_dir, new_name)
                    new_dds.save(new_path)
                    tga = texconv.convert_to_tga(new_path, out=temp_dir, cubemap_layout=cubemap_layout,
                                                 invert_normals=invert_normals)
                    tga_list.append(tga)
            else:
                tga = texconv.convert_to_tga(temp, out=temp_dir, cubemap_layout=cubemap_layout,
                                             invert_normals=invert_normals)
                tga_list = [tga]

            for tga in tga_list:
                if tga is None:
                    raise RuntimeError('Failed to convert texture.')

                # Load tga file
                tex = load_texture(tga, name=os.path.basename(tga)[:-4], color_space=color_space)
                tex_list.append(tex)

        tex = tex_list[0]
        if dds_properties_exist():
            # Update custom properties
            props = tex.dds_props
            dxgi = dds_header.get_format_as_str()
            if dxgi in DDS_FMT_NAMES:
                props.dxgi_format = dxgi
            props.no_mip = dds_header.mipmap_num <= 1
            props.texture_type = dds_header.get_texture_type()
            if dds_header.is_cube():
                props.cubemap_layout = cubemap_layout
            if dds_header.is_3d() or dds_header.is_array():
                for tex in tex_list[1:]:
                    new_item = props.texture_list.add()
                    new_item.texture = tex

        for tex in tex_list:
            if cubemap_layout.endswith("-fnz"):
                # Flip -z face for cubemaps
                w, h = tex.size
                pix = np.array(tex.pixels).reshape((h, w, -1))
                if cubemap_layout[0] == "v":
                    pix[h//4 * 0: h//4 * 1, w//3 * 1: w//3 * 2] = \
                        (pix[h//4 * 0: h//4 * 1, w//3 * 1: w//3 * 2])[::-1, ::-1]
                else:
                    pix[h//3 * 1: h//3 * 2, w//4 * 3: w//4 * 4] = \
                        (pix[h//3 * 1: h//3 * 2, w//4 * 3: w//4 * 4])[::-1, ::-1]
                pix = pix.flatten()
                tex.pixels = list(pix)

            tex.update()

    except Exception as e:
        for tex in tex_list:
            if tex is not None:
                bpy.data.images.remove(tex)
        raise e

    return tex_list[0]


def import_dds(context, file, texconv=None, astcenc=None):
    """Import a file."""
    space = get_image_editor_space(context)
    dds_options = context.scene.dds_options
    tex = load_dds(file, invert_normals=dds_options.invert_normals,
                   cubemap_layout=dds_options.cubemap_layout,
                   texconv=texconv, astcenc=astcenc)
    if space:
        space.image = tex


def import_dds_rec(context, folder, texconv=None, astcenc=None):
    """Search a folder recursively, and import found dds files."""
    count = 0
    for file in sorted(os.listdir(folder)):
        path = os.path.join(folder, file)
        if os.path.isdir(path):
            count += import_dds_rec(context, path)
        elif file.split('.')[-1].lower() == "dds":
            import_dds(context, path, texconv=texconv, astcenc=astcenc)
            count += 1
    return count


class DDS_OT_import_base(Operator):
    """Base class for imoprt operators."""

    def draw(self, context):
        """Draw options for file picker."""
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        dds_options = context.scene.dds_options
        layout.prop(dds_options, 'invert_normals')
        layout.prop(dds_options, 'cubemap_layout')

    def execute_base(self, context, files=None, directory=None, is_dir=False):
        if directory is None:
            raise RuntimeError('"self.directory" is not specified. This is unexpected.')

        texconv = Texconv()
        astcenc = Astcenc()

        try:
            start_time = time.time()
            if is_dir:
                # For DDS_OT_import_dir
                count = import_dds_rec(context, directory,
                                       texconv=texconv, astcenc=astcenc)
            else:
                # For DDS_OT_import_dds
                count = 0
                for _, file in enumerate(files):
                    import_dds(context, os.path.join(directory, file.name),
                               texconv=texconv, astcenc=astcenc)
                    flush_stdout()
                    count += 1
            elapsed_s = f'{(time.time() - start_time):.2f}s'
            if count == 0:
                raise RuntimeError("Imported no DDS files.")
            elif count == 1:
                m = f'Success! Imported a DDS file in {elapsed_s}'
            else:
                m = f'Success! Imported {count} DDS files in {elapsed_s}'
            print(m)
            self.report({'INFO'}, m)
            ret = {'FINISHED'}

        except Exception as e:
            print(traceback.format_exc())
            self.report({'ERROR'}, e.args[0])
            ret = {'CANCELLED'}

        # release DLL resources
        unload_texconv()
        unload_astcenc()

        return ret


class DDS_OT_import_dds(DDS_OT_import_base, ImportHelper):
    """Operator to import .dds files."""
    bl_idname = 'dds.import_dds'
    bl_label = 'Import Files'
    bl_description = 'Import selected .dds files'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default='*.dds; *.DDS', options={'HIDDEN'})

    filepath: StringProperty(subtype='FILE_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        """Invoke."""
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        return self.execute_base(context, files=self.files, directory=self.directory)


class DDS_OT_import_dir(DDS_OT_import_base):
    """Operator to import DDS files from a directory."""
    bl_idname = 'dds.import_dir'
    bl_label = 'Import from a Directory'
    bl_description = 'Search a directory recursively and import found DDS files'
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


class DDS_PT_import_panel(bpy.types.Panel):
    """UI panel for import function."""
    bl_label = "Import DDS"
    bl_idname = 'DDS_PT_import_panel'
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "DDS"

    def draw(self, context):
        """Draw UI panel."""
        layout = self.layout
        layout.operator(DDS_OT_import_dds.bl_idname, icon='TEXTURE_DATA')
        layout.operator(DDS_OT_import_dir.bl_idname, icon='TEXTURE_DATA')
        dds_options = context.scene.dds_options
        layout.prop(dds_options, 'invert_normals')
        layout.prop(dds_options, 'cubemap_layout')


classes = (
    DDS_OT_import_dds,
    DDS_OT_import_dir,
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
