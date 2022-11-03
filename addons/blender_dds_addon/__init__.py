"""Blender addon to import .dds files."""

bl_info = {
    'name': 'DDS textures',
    'author': 'Matyalatte',
    'version': (0, 1, 1),
    'blender': (2, 83, 20),
    'location': 'Image Editor > Sidebar > DDS Tab',
    'description': 'Import and export .dds files',
    "wiki_url": "https://github.com/matyalatte/Blender-DDS-Addon",
    'support': 'COMMUNITY',
    'category': 'Import-Export',
}

try:
    def reload_package(module_dict_main):
        """Reload Scripts."""
        import importlib
        from pathlib import Path

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

    from . import import_dds, export_dds

    def register():
        """Add addon."""
        import_dds.register()
        export_dds.register()

    def unregister():
        """Remove addon."""
        import_dds.unregister()
        export_dds.unregister()

except ModuleNotFoundError as exc:
    print(exc)
    print('bpy not found.')
