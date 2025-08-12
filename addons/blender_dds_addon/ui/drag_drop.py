import os
import time
import traceback

import bpy
from .import_dds import import_dds
from ..directx.texconv import Texconv
from ..astcenc.astcenc import Astcenc
from .bpy_util import flush_stdout


def is_dds_panel(context):
    return (context.area and context.area.type == 'IMAGE_EDITOR'
            and context.region and context.region.type == 'UI'
            and context.region.active_panel_category == 'DDS')


class DDS_OT_drag_drop_import(bpy.types.Operator):
    """Operator to import dropped .dds files."""
    bl_idname = "dds.drag_drop_import"
    bl_label = "Import a dropped dds file"
    directory: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return is_dds_panel(context)

    def execute(self, context):
        if not self.directory or not self.files:
            return {'CANCELLED'}

        texconv = Texconv()
        astcenc = Astcenc()

        try:
            start_time = time.time()
            count = 0

            for file in self.files:
                filepath = os.path.join(self.directory, file.name)
                import_dds(context, filepath,
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

        return ret

    def invoke(self, context, event):
        if self.directory and self.files:
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


if (4, 1, 0) > bpy.app.version:
    # blender 4.0 or older don't support drag-drop
    class Dummy:
        pass
    handler_cls = Dummy
else:
    handler_cls = bpy.types.FileHandler


class DDS_FH_import(handler_cls):
    bl_idname = "DDS_FH_import"
    bl_label = "File handler for dds import"
    bl_import_operator = "dds.drag_drop_import"
    bl_file_extensions = ".dds"

    @classmethod
    def poll_drop(cls, context):
        return is_dds_panel(context)


classes = (
    DDS_OT_drag_drop_import,
    DDS_FH_import,
)

if (4, 1, 0) > bpy.app.version:
    # blender 4.0 or older don't support drag-drop
    classes = ()


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
