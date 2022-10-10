"""UI panel and operator to import .uasset files."""

import os
import time
import shutil
import tempfile

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from .texconv import Texconv


def load_tga(file, name, color_space='Non-Color'):
    """Load tga file.

    Args:
        file (string): file path for dds
        name (string): object name for the texture
        color_space (string): color space

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    tex = bpy.data.images.load(file)
    tex.pack()
    tex.colorspace_settings.name = color_space
    tex.filepath = ''
    tex.filepath_raw = ''
    tex.name = name
    return tex


def load_dds(file, invert_normals=False, no_err=False, texconv=None):
    """Import a texture form .uasset file.

    Args:
        file (string): file path to .uasset file
        invert_normals (bool): Flip y axis if the texture is normal map.
        texconv (Texconv): Texture converter for dds.

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    texture_name = os.path.basename(file)[:-4]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = os.path.join(temp_dir, "temp.dds")
        shutil.copyfile(file, temp)
        if texconv is None:
            texconv = Texconv()
        try:
            temp_tga = texconv.convert_to_tga(temp, out=temp_dir, invert_normals=invert_normals)
            if temp_tga is None:  # if texconv doesn't exist
                raise RuntimeError('Failed to convert texture.')
            tex = load_tga(temp_tga, name=texture_name)
        except Exception as e:
            if not no_err:
                raise e
            print(f'Failed to load {file}')
            tex = None

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

    def invoke(self, context, event):
        """Invoke."""
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        """Run the operator."""
        if not self.directory:
            raise RuntimeError('"self.directory" is not specified. This is unexpected.')
        for _, file in enumerate(self.files):
            ret = self.import_uasset(context, os.path.join(self.directory, file.name))
            if ret != {'FINISHED'}:
                return ret
        return ret

    def import_uasset(self, context, file):
        """Import a file."""
        try:
            start_time = time.time()
            area = context.area
            if area.type == 'IMAGE_EDITOR':
                space = area.spaces.active
            else:
                raise RuntimeError('Failed to get Image Editor. This is unexpected.')
            dds_options = context.scene.dds_options
            tex = load_dds(file, invert_normals=dds_options.invert_normals)
            space.image = tex
            elapsed_s = f'{(time.time() - start_time):.2f}s'
            m = f'Success! Imported DDS in {elapsed_s}'
            print(m)
            self.report({'INFO'}, m)
            ret = {'FINISHED'}

        except Exception as e:
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
