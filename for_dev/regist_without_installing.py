"""Script to use the addon without installing it in Blender.

Notes:
    Registration
    1. Make a new folder and rename it to 'modules'
    2. Unzip blender_dds_addon*.zip
    3. Put blender_dds_addon (not a zip!) in the modules folder
    4. Launch Blender
    5. Uninstall blender dds addon if you installed
    6. Go to Edit->Preferences->File Paths->Data->Scripts
    7. Type the directory has the modules folder
    8. Close the preferences window
    9. Go to Scripting Tab
    10. Open this python script from Text->Open
    11. Check Text->Register
    12. Save the scene as .blend
    13. Done! Only the .blend file will load the addon when you open it.

    Unregstration
    1. Launch Blender
    2. Go to Edit->Preferences->File Paths->Data->Scripts
    3. Type '//' as the script folder
    4. Close the preferences window
    5. Go to Scripting Tab
    6. Uncheck Text->Register
    7. Remove 'modules' folder if you want to
    8. Done! You can install the addon again
"""

import blender_dds_addon

if "bpy" in locals():
    import importlib
    if "blender_dds_addon" in locals():
        importlib.reload(blender_dds_addon)


def register():
    """Regist addon."""
    blender_dds_addon.register()


def unregister():
    """Unregist addon."""
    blender_dds_addon.unregister()


status = 'register'
if status == 'register':
    register()
else:
    unregister()
