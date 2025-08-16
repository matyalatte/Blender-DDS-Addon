import os
import bpy
import numpy as np


def flush_stdout():
    print("", end="", flush=True)


def dds_properties_exist():
    return hasattr(bpy.types.Image, "dds_props")


def get_addon_preferences(context, addon_name):
    preferences = context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return addon_prefs


def get_image_editor_space(context):
    area = context.area
    if area and area.type == 'IMAGE_EDITOR':
        return area.spaces.active
    return None


def get_selected_tex(context):
    space = get_image_editor_space(context)
    if space:
        return space.image
    return None


def load_texture(file, name, color_space='Non-Color'):
    """Load a texture file.

    Args:
        file (string): file path for tga
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


# height, width, x+pos, x-pos, y+pos, y-pos, z+pos, z-pos
cube_layouts = {
    "h-cross": (3, 4, (1, 2), (1, 0), (2, 1), (0, 1), (1, 1), (1, 3)),
    "v-cross": (4, 3, (2, 2), (2, 0), (3, 1), (1, 1), (2, 1), (0, 1)),
    "h-cross-fnz": (3, 4, (1, 2), (1, 0), (2, 1), (0, 1), (1, 1), (1, 3)),
    "v-cross-fnz": (4, 3, (2, 2), (2, 0), (3, 1), (1, 1), (2, 1), (0, 1)),
    "h-strip": (1, 6, (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)),
    "v-strip": (6, 1, (5, 0), (4, 0), (3, 0), (2, 0), (1, 0), (0, 0)),
}


def load_texture_from_buffer(name, width, height, buffers, dtype,
                             premultiplied_alpha=False,
                             cubemap_layout='h-cross', color_space='Non-Color'):
    """Load a texture file from buffers.

    Args:
        name (string): object name for the texture
        width (int): image width
        height (int): image height
        buffers (list[byte]): binary data for pixels.
                              A buffer for a 2d image, Six buffers for a cubemap.
        dtype : a data type object for numpy
        premultiplied_alpha (bool): Convert premultiplied alpha to straight alpha.
        cubemap_layout (string): layout for cubemaps
        color_space (string): color space

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    float_buffer = np.issubdtype(dtype, np.floating)
    if len(buffers) == 1:
        tex = bpy.data.images.new(name, width, height, float_buffer=float_buffer)
        tex.colorspace_settings.name = color_space
        pixels = np.frombuffer(buffers[0], dtype=dtype).reshape((height, width, -1))
        pixels = pixels[::-1]
    else:
        layout = cube_layouts[cubemap_layout]
        tex = bpy.data.images.new(name, width * layout[1], height * layout[0], float_buffer=float_buffer)
        tex.colorspace_settings.name = color_space
        pixels = np.zeros((height * layout[0], width * layout[1], 4), dtype=dtype)
        for buf, pos in zip(buffers, layout[2:]):
            face = np.frombuffer(buf, dtype=dtype).reshape((height, width, -1))
            face = face[::-1]
            pixels[height * pos[0]: height * (pos[0] + 1), width * pos[1]: width * (pos[1] + 1), ::] = face

    if premultiplied_alpha:
        alpha = pixels[..., 3:4]
        out = pixels.copy()
        out[..., :3] = np.where(alpha > 0, pixels[..., :3] / alpha, pixels[..., :3])
        tex.pixels = list(out.flatten())
    else:
        tex.pixels = list(pixels.flatten())
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


def texture_to_buffer(tex, dtype):
    """Get pixels as bytes.

    Args:
        tex (bpy.types.Image): an image object
        dtype : a data type object for numpy
    """
    w, h = tex.size
    pixels = np.array(tex.pixels, dtype=dtype).reshape(h, w, -1)
    pixels = pixels[::-1].flatten()
    return pixels.tobytes()


def dxgi_to_dtype(fmt):
    if fmt == "R32G32B32A32_FLOAT":
        return np.float32
    if fmt == "R16G16B16A16_FLOAT":
        return np.float16
    raise RuntimeError(f"dxgi_to_dtype() does not support {fmt}.")
