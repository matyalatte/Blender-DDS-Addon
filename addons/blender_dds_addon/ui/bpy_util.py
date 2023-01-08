import os
import bpy


def dds_properties_exist():
    return hasattr(bpy.types.Image, "dds_props")


def get_addon_preferences(context, addon_name):
    preferences = context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return addon_prefs


def get_image_editor_space(context):
    area = context.area
    if area.type == 'IMAGE_EDITOR':
        space = area.spaces.active
    else:
        raise RuntimeError('Failed to get Image Editor. This is unexpected.')
    return space


def get_selected_tex(context):
    space = get_image_editor_space(context)
    tex = space.image
    if tex is None:
        raise RuntimeError('Select an image on Image Editor.')
    return tex


def load_texture(file, name, color_space='Non-Color'):
    """Load a texture file.

    Args:
        file (string): file path for dds
        name (string): object name for the texture
        color_space (string): color space

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    tex = bpy.data.images.load(file)
    tex.colorspace_settings.name = color_space
    tex.name = name
    tex.pack()
    tex.filepath = os.path.join('//textures', tex.name + '.' + file.split('.')[-1])
    tex.filepath_raw = tex.filepath
    return tex


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
