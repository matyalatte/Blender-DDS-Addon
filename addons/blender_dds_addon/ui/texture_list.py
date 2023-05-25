import bpy
from bpy.props import PointerProperty, EnumProperty
from bpy.types import PropertyGroup, Image, UIList, Operator
from .bpy_util import get_selected_tex, dds_properties_exist


class DDSTextureListItem(PropertyGroup):
    texture: PointerProperty(
        name="item",
        type=Image,
        description="An extra texture for texture arrays or volume textures"
    )


class DDS_UL_texture_list(UIList):
    """UI to edit texture array."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        custom_icon = 'TEXTURE'
        check_tex_status(context, item.texture, layout, show_msg=False)

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.texture:
                layout.prop(item.texture, "name", text="", emboss=False, icon=custom_icon)
            else:
                layout.label(text="", icon=custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)

    def draw_filter(self, context, layout):
        pass


def get_tex(context):
    if not dds_properties_exist():
        return None
    return get_selected_tex(context)


class DDS_OT_list_new_item(Operator):
    """Add a new item to the list"""

    bl_idname = "dds.list_new_item"
    bl_label = "Add a new item"

    def execute(self, context):
        tex = get_tex(context)
        if tex is None:
            return {'CANCELLED'}
        tex.dds_props.texture_list.add()
        return {'FINISHED'}


class DDS_OT_list_delete_item(Operator):
    """Delete the selected item from the list"""

    bl_idname = "dds.list_delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        tex = get_tex(context)
        if tex is None:
            return None
        return tex.dds_props.texture_list

    def execute(self, context):
        tex = get_tex(context)
        if tex is None:
            return {'CANCELLED'}
        texture_list = tex.dds_props.texture_list
        index = tex.dds_props.list_index

        texture_list.remove(index)
        tex.dds_props.list_index = min(max(0, index - 1), len(texture_list) - 1)

        return {'FINISHED'}


class DDS_OT_list_move_item(Operator):
    """Move an item in the list"""

    bl_idname = "dds.list_move_item"
    bl_label = "Move an item in the list"

    direction: EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        tex = get_tex(context)
        if tex is None:
            return None
        return tex.dds_props.texture_list

    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """
        tex = get_tex(context)
        if tex is None:
            return {'CANCELLED'}
        texture_list = tex.dds_props.texture_list
        index = tex.dds_props.list_index

        list_length = len(texture_list) - 1
        new_index = index + (-1 if self.direction == 'UP' else 1)

        tex.dds_props.list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        tex = get_tex(context)
        if tex is None:
            return {'CANCELLED'}
        texture_list = tex.dds_props.texture_list
        index = tex.dds_props.list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        texture_list.move(neighbor, index)
        self.move_index(context)

        return {'FINISHED'}


def check_tex_status(context, extra_tex, layout, show_msg=False):
    if extra_tex is None:
        layout.alert = True
        if show_msg:
            layout.label(text="Specify a texture or remove this item.")
        return
    tex = get_selected_tex(context)
    w, h = tex.size
    extra_w, extra_h = extra_tex.size
    if w != extra_w or h != extra_h:
        layout.alert = True
        if show_msg:
            layout.label(text=f"The size should be ({w}, {h}).")


def draw_texture_list(layout, context, dds_props):
    # draw list
    layout.separator(factor=0.5)
    texture_type = dds_props.texture_type.replace("_", " ")
    layout.label(text=f"Extra textures for {texture_type}")
    row = layout.row(align=True).split(factor=0.85, align=True)
    row.template_list("DDS_UL_texture_list", "texture_list",
                      dds_props, "texture_list",
                      dds_props, "list_index")

    # draw operators
    col = row.split(align=True).column()
    row = col.column(align=True)
    row.operator("dds.list_new_item", text="", icon="ADD")
    row.operator("dds.list_delete_item", text="", icon="REMOVE")

    row = col.column(align=True)
    row.operator("dds.list_move_item", text="", icon="TRIA_UP").direction = "UP"
    row.operator("dds.list_move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

    index = dds_props.list_index
    if dds_props.texture_list is None or len(dds_props.texture_list) == 0:
        return

    # image selector for an element
    item = dds_props.texture_list[index]
    col = layout.column(align=True)
    col.prop(item, "texture", text="")
    extra_tex = item.texture
    check_tex_status(context, extra_tex, col, show_msg=True)


classes = (
    DDSTextureListItem,
    DDS_UL_texture_list,
    DDS_OT_list_new_item,
    DDS_OT_list_delete_item,
    DDS_OT_list_move_item,
)


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
