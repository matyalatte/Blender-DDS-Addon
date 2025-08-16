"""Blender addon to import .dds files."""
import importlib
from pathlib import Path

from .ui import (import_dds, export_dds, custom_properties,
                 preferences, texture_list, drag_drop)
from .directx.texconv import unload_texconv
from .astcenc.astcenc import unload_astcenc

bl_info = {
    'name': 'DDS textures',
    'author': 'Matyalatte',
    'version': (0, 5, 0),
    'blender': (2, 83, 20),
    'location': 'Image Editor > Sidebar > DDS Tab',
    'description': 'Import and export .dds files',
    "wiki_url": "https://github.com/matyalatte/Blender-DDS-Addon",
    'support': 'COMMUNITY',
    'category': 'Import-Export',
}


def reload_package(module_dict_main):
    def reload_package_recursive(current_dir, module_dict):
        for path in current_dir.iterdir():
            if "__init__" in str(path) or path.stem not in module_dict:
                continue
            if path.is_file() and path.suffix == ".py":
                importlib.reload(module_dict[path.stem])
            elif path.is_dir():
                reload_package_recursive(path, module_dict[path.stem].__dict__)

    reload_package_recursive(Path(__file__).parent, module_dict_main)


if ".import_dds" in locals():
    reload_package(locals())


modules = [
    preferences,
    import_dds,
    export_dds,
    texture_list,
    custom_properties,
    drag_drop,
]


def register():
    """Add addon."""
    for module in modules:
        module.register()


def unregister():
    """Remove addon."""
    for module in modules:
        module.unregister()
    unload_texconv()
    unload_astcenc()
