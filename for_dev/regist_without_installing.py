"""Script to use the addon without installing it in Blender.

Notes:
    Registration
    1. Make a new folder and rename it to 'addons'
    2. Unzip blender_dds_addon*.zip
    3. Put blender_dds_addon (not a zip!) in the addons folder
    4. Launch Blender
    5. Uninstall the addon if you installed
    6. Go to Edit->Preferences->File Paths->Data->Scripts
       (or Edit->Preferences->File Paths->Script Directories)
    7. Type the directory has the addons folder
       (or remove the folder from Script Directories)
    8. Close the preferences window
    9. Go to Scripting Tab
    10. Open this python script from Text->Open
    11. Check Text->Register
    12. Save the scene as .blend
    13. Done! Only the .blend file will load the addon.

    Unregstration
    1. Launch Blender
    2. Go to Edit->Preferences->File Paths->Data->Scripts
       (or Edit->Preferences->File Paths->Script Directories)
    3. Type '//' as the script folder
       (or remove the folder from Script Directories)
    4. Close the preferences window
    5. Go to Scripting Tab
    6. Uncheck Text->Register
    7. Remove 'addons' folder if you want to
    8. Done! You can install the addon again
"""

import blender_dds_addon

if "bpy" in locals():
    import importlib
    if "blender_dds_addon" in locals():
        importlib.reload(blender_dds_addon)


def register():
    """Enable addon."""
    blender_dds_addon.register()


def unregister():
    """Disable addon."""
    blender_dds_addon.unregister()


status = 'register'
if status == 'register':
    register()
else:
    unregister()
