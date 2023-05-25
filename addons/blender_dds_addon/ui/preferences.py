"""UI panel for addon preferences.

Notes:
    Edit > Preferences > Add-ons > Imoprt-Export: DDS textures
"""

import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

from .bpy_util import get_addon_preferences
from .custom_properties import add_custom_props_for_dds, remove_custom_props_for_dds


def update_custom_props(self, context):
    prefs = get_addon_preferences(context, "blender_dds_addon")
    if prefs.use_custom_prop:
        add_custom_props_for_dds()
    else:
        remove_custom_props_for_dds()


class DDSAddonPreferences(AddonPreferences):
    bl_idname = "blender_dds_addon"

    use_custom_prop: BoolProperty(
        update=update_custom_props,
        name="Use Custom Properties",
        description="When on, you can store export options for each image.",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_custom_prop")


def register():
    bpy.utils.register_class(DDSAddonPreferences)


def unregister():
    bpy.utils.unregister_class(DDSAddonPreferences)
