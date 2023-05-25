import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup
from .bpy_util import get_selected_tex, dds_properties_exist
from ..directx.dxgi_format import DXGI_FORMAT
from .texture_list import DDSTextureListItem, draw_texture_list

fmt_list = [fmt.name for fmt in DXGI_FORMAT]
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
    return ('TYPELESS' not in fmt) and ('ASTC' not in fmt) and\
           (len(fmt) > 4) and (fmt not in ["UNKNOWN", "OPAQUE_420"])


DDS_FMT_ITEMS = [(fmt, get_alt_fmt(fmt), '') for fmt in fmt_list if is_supported(fmt)]
DDS_FMT_NAMES = [fmt for fmt in fmt_list if is_supported(fmt)]


class DDSPropBase:
    no_mip: BoolProperty(
        name='No Mipmaps',
        description="Disable mipmap generation",
        default=False,
    )

    texture_type: EnumProperty(
        name='Type',
        items=[
            ('2d', '2D', '2D texture'),
            ('cube', 'Cube', 'Cube map'),
            ('2d_array', '2D Array', 'Array of 2D textures'),
            ('cube_array', 'Cube Array', 'Array of cube maps'),
            ('volume', 'Volume', '3D texture'),
        ],
        description=(
            'Texture type'
        ),
        default='2d'
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

    texture_list: CollectionProperty(type=DDSTextureListItem)

    list_index: IntProperty(name="An extra texture for texture arrays or volume textures", default=0)


class DDSOptions(DDSPropBase, PropertyGroup):
    """Properties for operations."""
    dxgi_format: EnumProperty(
        name='DXGI format',
        items=DDS_FMT_ITEMS,
        description="DXGI format for DDS",
        default='BC1_UNORM'
    )

    invert_normals: BoolProperty(
        name='Invert Normals',
        description="Invert G channel for BC5 textures",
        default=False,
    )

    image_filter: EnumProperty(
        name='Image Filter',
        description="Image filter for mipmap generation",
        items=[
            ('POINT', 'Point', 'Nearest neighbor'),
            ('LINEAR', 'Linear', 'Bilinear interpolation (or box filter)'),
            ('CUBIC', 'Cubic', 'Bicubic interpolation'),
        ],
        default='LINEAR',
    )

    allow_slow_codec: BoolProperty(
        name='Allow Slow Codec',
        description=("Allow to use CPU codec for BC6 and BC7.\n"
                     "But it'll take a long time for conversion"),
        default=False,
    )


class DDSCustomProperties(DDSPropBase, PropertyGroup):
    """Properties for dds info."""
    dxgi_format: EnumProperty(
        name='DXGI format',
        items=[('NONE', 'None', 'Skip this image when excuting the export opration.')] + DDS_FMT_ITEMS,
        description="DXGI format for DDS",
        default='NONE'
    )


def add_custom_props_for_dds():
    if dds_properties_exist():
        return
    bpy.types.Image.dds_props = PointerProperty(type=DDSCustomProperties)


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
        if not dds_properties_exist():
            return
        layout = self.layout
        tex = get_selected_tex(context)
        if tex is None:
            return
        dds_props = tex.dds_props
        layout.prop(dds_props, "dxgi_format")
        if tex.dds_props.dxgi_format != "NONE":
            layout.prop(dds_props, "no_mip")
            layout.prop(dds_props, 'texture_type')
            if dds_props.texture_type in ["cube", "cube_array"]:
                layout.prop(dds_props, "cubemap_layout")
            if dds_props.texture_type in ["2d_array", "cube_array", "volume"]:
                draw_texture_list(layout, context, dds_props)


classes = (
    DDSOptions,
    DDSCustomProperties,
    DDS_PT_property_panel,
)


def register():
    """Add UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.dds_options = PointerProperty(type=DDSOptions)
    add_custom_props_for_dds()


def unregister():
    """Remove UI panel, operator, and properties."""
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.dds_options
    remove_custom_props_for_dds()
