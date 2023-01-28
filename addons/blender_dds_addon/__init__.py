"""Blender addon to import .dds files."""
import importlib
from pathlib import Path

from .ui import import_dds, export_dds, custom_properties, preferences
from .directx.texconv import unload_texconv

bl_info = {
    'name': 'DDS textures',
    'author': 'Matyalatte',
    'version': (0, 2, 1),
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


def register():
    """Add addon."""
    preferences.register()
    import_dds.register()
    export_dds.register()
    custom_properties.register()


def unregister():
    """Remove addon."""
    preferences.unregister()
    import_dds.unregister()
    export_dds.unregister()
    custom_properties.unregister()
    unload_texconv()
