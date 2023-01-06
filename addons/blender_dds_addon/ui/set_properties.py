import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty
from bpy.types import PropertyGroup
from .bpy_util import get_image_editor_space, dds_properties_exist
from .export_dds import DDS_FMT_ITEMS


class DDSProperties(PropertyGroup):
    """Properties for export options."""

    dxgi_format: EnumProperty(
        name='DDS format',
        items=[('NONE', 'None', 'Skip this image when excuting the export opration.')] + DDS_FMT_ITEMS,
        description="DXGI format for DDS",
        default='NONE'
    )

    no_mip: BoolProperty(
        name='No Mipmaps',
        description="Disable mipmap generation",
        default=False,
    )

    is_cube: BoolProperty(
        name='Is Cubemap',
        description=("Export this texture as a cubemap.\n"
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


def add_custom_props_for_dds():
    if dds_properties_exist():
        return
    bpy.types.Image.dds_props = PointerProperty(type=DDSProperties)


def remove_custom_props_for_dds():
    if dds_properties_exist():
        del bpy.types.Image.dds_props


class DDS_PT_property_panel(bpy.types.Panel):
    """UI panel for custom properties."""
    bl_label = "Custom Properties"
    bl_idname = 'DDS_PT_property_panel'
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "DDS"

    def draw(self, context):
        """Draw UI panel."""
        layout = self.layout
        tex = get_image_editor_space(context).image
        if tex is None:
            return
        layout.prop(tex.dds_props, "dxgi_format")
        if tex.dds_props.dxgi_format != "NONE":
            layout.prop(tex.dds_props, "no_mip")
            layout.prop(tex.dds_props, "is_cube")
            if tex.dds_props.is_cube:
                layout.prop(tex.dds_props, "cubemap_layout")


classes = (
    DDSProperties,
    DDS_PT_property_panel,
)


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)
    add_custom_props_for_dds()


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
    remove_custom_props_for_dds()
